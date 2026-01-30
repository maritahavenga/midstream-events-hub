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
    afrikaans_variants = ["afrikaans", "eat", "eerste addisionele taal"]
    if any(variant in str(activity_name).lower() for variant in afrikaans_variants):
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
            sel_cat = st.multiselect("Category", ["Sport", "Culture", "Academics"], default=[], key="f_cat")
        with c2:
            act_list = sorted(list(set([str(a).strip() for a in df_raw.iloc[:, 3] if a])))
            sel_act = st.multiselect("Activity / Subject", act_list, default=[], key="f_act")
        with c3:
            age_list = sorted(list(set([clean_val(a) for a in df_raw.iloc[:, 11] if a]))) if df_raw.shape[1] > 11 else []
            sel_age = st.multiselect("Gr / Age", age_list, default=[], key="f_age")
        
        search_q = st.text_input("Search", placeholder="Search Subject, Grade or Detail...")
        
        if st.button("REFRESH HUB", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    SA_TIME = pytz.timezone('Africa/Johannesburg')
    today = datetime.now(SA_TIME).date()
    df_filtered = []

    for _, r in df_raw.iterrows():
        dt_val = pd.to_datetime(r.iloc[5], dayfirst=True, errors='coerce')
        is_ft = len(r) > 12 and "full term" in str(r.iloc[12]).lower()
        if not (is_ft or pd.isnull(dt_val) or dt_val.date() >= today): continue
        
        if sel_cat:
            match_found = False
            row_cat = str(r.iloc[2]).lower().strip()
            for s in sel_cat:
                if s.lower() in row_cat or (s == "Academics" and "academic" in row_cat): match_found = True
            if not match_found: continue
        
        if sel_act and str(r.iloc[3]).strip() not in sel_act: continue
        if sel_age and df_raw.shape[1] > 11 and clean_val(r.iloc[11]) not in sel_age: continue
        
        df_filtered.append((r, dt_val))

    h = """<style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
        body { font-family: 'Inter', sans-serif; background: transparent; }
        .card { background:white; padding:20px; border-radius:15px; border-left:10px solid #800000; margin-bottom:18px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
        .card-title { color:#800000; font-size:1.15rem; font-weight:800; margin-bottom:5px; line-height:1.2; }
        .info-row { font-size:0.9rem; color:#444; margin: 5px 0; font-weight: 500; }
        .venue-bold { color:#008080; font-weight:800; text-transform: uppercase; }
        .note-box { background:#e7f3f3; border-radius:8px; padding:12px; margin-top:10px; border-left:4px solid #008080; font-size:0.85rem; color:#004d4d; font-weight:600; }
        .team-frame { border: 2px dotted #800000; border-radius: 8px; padding: 6px 10px; margin-top: 8px; display: inline-block; font-size: 0.85rem; color: #800000; font-weight: 700; background: #fff9f9; }
        .btn-box { display:flex; flex-wrap:wrap; gap:8px; margin-top:15px; }
        .btn { background:#800000; color:white !important; padding:8px 14px; border-radius:8px; text-decoration:none; font-size:0.75rem; font-weight:700; text-transform:uppercase; display:inline-block; }
    </style>"""

    for r, dt in df_filtered:
        cat = str(r.iloc[2]).lower()
        act_raw = str(r.iloc[3])
        is_acad = "academic" in cat
        prefix = "Gr " if is_acad else "U"
        age = clean_val(r.iloc[11]) if len(r)>11 else ""
        age_str = f"{prefix}{age}" if age else ""
        team_detail = clean_val(r.iloc[4])
        
        full_title = f"{translate_term(act_raw, act_raw)} {age_str} {translate_term(team_detail, act_raw)}".strip()
        if search_q and search_q.lower() not in full_title.lower(): continue

        d_str = "FULL TERM" if (len(r) > 12 and "full term" in str(r.iloc[12]).lower()) else (dt.strftime('%d %B %Y') if pd.notnull(dt) else str(r.iloc[5]))
        
        btns = ""
        if "http" in str(r.iloc[7]).lower(): btns += f"<a href='{r.iloc[7]}' target='_blank' class='btn'>{'Document' if is_acad else 'Programme'}</a>"
        if "http" in str(r.iloc[8]).lower(): btns += f"<a href='{r.iloc[8]}' target='_blank' class='btn'>Assessment Details</a>"
        elif clean_val(r.iloc[8]): btns += f"<div class='team-frame'>INFO: {r.iloc[8]}</div>"
        
        note_raw = clean_val(r.iloc[10]).replace("$", "")
        if "http" in note_raw.lower():
            btns += f"<a href='{note_raw}' target='_blank' class='btn'>Info</a>"
            note_html = ""
        else:
            note_html = f"<div class='note-box'>NOTE: {note_raw}</div>" if note_raw else ""
        
        h += f"""<div class='card'>
            <div class='card-title'>{full_title}</div>
            <div class='info-row'>📅 {d_str}</div>
            <div class='info-row'>📍 <span class='venue-bold'>{translate_term(str(r.iloc[6]), act_raw).upper()}</span></div>
            {note_html}
            <div class='btn-box'>{btns}</div>
        </div>"""

    components.html(h, height=2500, scrolling=True)

st.markdown("<center style='color:#999;font-size:0.7rem;'>LMCP Digital Hub 2026</center>", unsafe_allow_html=True)
