import streamlit as st
import pandas as pd
import requests
import io
import re
from datetime import datetime
import pytz
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

# 1. Konfigurasie
st.set_page_config(page_title="LMCP Digital Hub", layout="centered")
st_autorefresh(interval=120000, key="datarefresh")

EVENTS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

def clean_val(val):
    v = str(val).replace(".0", "").replace("nan", "").replace("NAN", "").strip()
    return "" if v.lower() in ["n/a", "none", ""] else v

def translate_term(text, activity_name=""):
    act_str = str(activity_name).strip()
    # Forceer formele Afrikaanse name vir Akademis
    if re.search(r'(?i)\bEAT\b', act_str):
        text = text.replace(activity_name, "Afrikaans Eerste Addisionele Taal")
    elif re.search(r'(?i)\bHT\b', act_str):
        text = text.replace(activity_name, "Afrikaans Hooftaal")
        
    if any(k in act_str.lower() for k in ["afrikaans", "eat", "eerste addisionele taal", "hooftaal", "ht"]):
        return text

    translations = {
        "Saal": "Hall", "Ouditorium": "Auditorium", "Musiekkamer": "Music Room",
        "Swembad": "Pool", "Tennisbane": "Tennis Courts", "Netbalbane": "Netball Courts",
        "Muurbalbane": "Squash Courts", "Veld": "Field", "Koor": "Choir", 
        "Astro": "Astro", "Atletiek": "Athletics", "Wiskunde": "Mathematics", 
        "Wetenskap": "Science", "Geskiedenis": "History", "Geografie": "Geography"
    }
    for afrikaans, english in translations.items():
        text = re.sub(rf'\b{afrikaans}\b', english, text, flags=re.IGNORECASE)
    return text

@st.cache_data(ttl=1)
def load_data(url):
    try:
        r = requests.get(f"{url}&cb={datetime.now().timestamp()}", timeout=10)
        df = pd.read_csv(io.StringIO(r.content.decode('utf-8')))
        return df.fillna("")
    except: return pd.DataFrame()

st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", use_container_width=True)
df_raw = load_data(EVENTS_URL)

if not df_raw.empty:
    with st.container():
        st.markdown("<div style='background:white; padding:20px; border-radius:12px; border:1px solid #eee; box-shadow:0 4px 12px rgba(0,0,0,0.05); margin-bottom:20px;'>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            sel_cat = st.multiselect("Category", ["Sport", "Culture", "Academics"], key="f_cat")
        with c2:
            act_list = sorted(list(set([str(a).strip() for a in df_raw.iloc[:, 3] if a])))
            sel_act = st.multiselect("Activity / Subject", act_list, key="f_act")
        with c3:
            age_options = ["Gr 1", "Gr 2", "Gr 3", "Gr 4", "Gr 5", "Gr 6", "Gr 7", "U7", "U8", "U9", "U10", "U11", "U12", "U13"]
            sel_age = st.multiselect("Gr / Age Group", age_options, key="f_age")
        
        search_q = st.text_input("Search", placeholder="Search Subject, Grade or Detail...")
        if st.button("REFRESH HUB", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    SA_TIME = pytz.timezone('Africa/Johannesburg')
    today = datetime.now(SA_TIME).date()
    
    target_numbers = set()
    for s in sel_age:
        nums = re.findall(r'\d+', s)
        if nums:
            n = int(nums[0])
            target_numbers.add(n)
            if n >= 7: target_numbers.add(n - 6)
            if n <= 7: target_numbers.add(n + 6)

    df_filtered = []
    for _, r in df_raw.iterrows():
        act_name = str(r.iloc[3])
        dt_val = pd.to_datetime(str(r.iloc[5]), errors='coerce')
        if pd.isnull(dt_val): dt_val = pd.to_datetime(str(r.iloc[5]), dayfirst=True, errors='coerce')
        if pd.notnull(dt_val) and dt_val.date() < today: continue
        if sel_cat and not any(s.lower() in str(r.iloc[2]).lower() or (s=="Academics" and "academic" in str(r.iloc[2]).lower()) for s in sel_cat): continue
        if sel_act and act_name.strip() not in sel_act: continue
        
        is_global_act = any(ws in act_name.lower() for ws in ["swimming", "athletics"])
        if target_numbers and not is_global_act:
            row_age_val = clean_val(r.iloc[11])
            row_nums = re.findall(r'\d+', row_age_val)
            if not row_nums or int(row_nums[0]) not in target_numbers: continue
        
        is_ft = len(r) > 12 and "full term" in str(r.iloc[12]).lower()
        g_raw = clean_val(r.iloc[11])
        match = re.search(r'\d+', g_raw)
        g_num = int(match.group()) if match else 99
        if "U" in g_raw.upper() and g_num >= 7: g_num = g_num - 6
        df_filtered.append({'data': r, 'date': dt_val if pd.notnull(dt_val) else datetime.max.replace(tzinfo=None), 'subject': act_name.lower(), 'grade_val': g_num, 'is_ft': is_ft})

    df_filtered.sort(key=lambda x: (not x['is_ft'], x['date'], x['subject'], x['grade_val']))

    h = """<style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
        body { font-family: 'Inter', sans-serif; background: transparent; }
        .card { background:white; padding:20px; border-radius:15px; border-left:10px solid #800000; margin-bottom:18px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
        .card-title { color:#800000; font-size:1.15rem; font-weight:800; margin-bottom:10px; line-height:1.2; }
        .info-row { font-size:0.9rem; color:#444; margin: 5px 0; font-weight: 500; }
        .venue-bold { color:#008080; font-weight:800; text-transform: uppercase; }
        .note-box { background:#e7f3f3; border-radius:8px; padding:12px; margin-top:10px; border-left:4px solid #008080; font-size:0.85rem; color:#004d4d; font-weight:600; }
        .btn-box { display:flex; flex-wrap:wrap; gap:8px; margin-top:15px; }
        .btn { background:#800000; color:white !important; padding:8px 14px; border-radius:8px; text-decoration:none; font-size:0.75rem; font-weight:700; text-transform:uppercase; display:inline-block; }
    </style>"""

    for item in df_filtered:
        r = item['data']
        act_display_name = str(r.iloc[3])
        row_cat = str(r.iloc[2]).lower()
        
        # --- STRENG AKADEMIESE LOGIKA ---
        is_academic = "academic" in row_cat or any(v in act_display_name.lower() for v in ["afrikaans", "eat", "ht", "math", "wiskunde", "science", "history"])
        
        row_age = clean_val(r.iloc[11])
        is_global = any(ws in act_display_name.lower() for ws in ["swimming", "athletics"])
        
        prefix = "Gr " if is_academic else "U"
        age_display = f"{prefix}{row_age} " if row_age and not (is_global and not row_age) else ""
            
        t_act = translate_term(act_display_name, act_display_name)
        t_detail = translate_term(clean_val(r.iloc[4]), act_display_name)
        full_title = f"{t_act} {age_display}{t_detail}".strip()
        
        if search_q and search_q.lower() not in full_title.lower(): continue
        d_str = "FULL TERM" if item['is_ft'] else (item['date'].strftime('%d %B %Y') if item['date'] != datetime.max.replace(tzinfo=None) else str(r.iloc[5]))
        
        # Knoppie name gebaseer op akademie-logika
        prog_btn = "Document" if is_academic else "Programme"
        team_btn = "Assessment Details" if is_academic else "Team List"
        
        btns = ""
        if "http" in str(r.iloc[7]).lower(): btns += f"<a href='{r.iloc[7]}' target='_blank' class='btn'>{prog_btn}</a>"
        if "http" in str(r.iloc[8]).lower(): btns += f"<a href='{r.iloc[8]}' target='_blank' class='btn'>{team_btn}</a>"
        
        note_raw = clean_val(r.iloc[10]).replace("$", "")
        if "http" in note_raw.lower(): btns += f"<a href='{note_raw}' target='_blank' class='btn'>Info</a>"
        else: note_html = f"<div class='note-box'>NOTE: {note_raw}</div>" if note_raw else ""
        
        h += f"""<div class='card'><div class='card-title'>{full_title}</div><div class='info-row'>📅 {d_str}</div><div class='info-row'>📍 <span class='venue-bold'>{translate_term(str(r.iloc[6]), act_display_name).upper()}</span></div>{note_html if 'note_html' in locals() else ''}<div class='btn-box'>{btns}</div></div>"""
        note_html = ""

    components.html(h, height=2500, scrolling=True)
st.markdown("<center style='color:#999;font-size:0.7rem;'>LMCP Digital Hub 2026</center>", unsafe_allow_html=True)
