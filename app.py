import streamlit as st
import pandas as pd
import requests
import io
import re
from datetime import datetime
import pytz
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

# 1. Configuration
st.set_page_config(page_title="LMCP Digital Hub", layout="centered")
st_autorefresh(interval=120000, key="datarefresh")

EVENTS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

def clean_val(val):
    v = str(val).replace(".0", "").replace("nan", "").replace("NAN", "").strip()
    return "" if v.lower() in ["n/a", "none", ""] else v

def translate_term(text, activity_name=""):
    if "afrikaans" in str(activity_name).lower(): return text
    translations = {
        "Saal": "Hall", "Ouditorium": "Auditorium", "Musiekkamer": "Music Room",
        "Swembad": "Pool", "Tennisbane": "Tennis Courts", "Netbalbane": "Netball Courts",
        "Muurbalbane": "Squash Courts", "Muurbal": "Squash", "Veld": "Field",
        "Koor": "Choir", "Astro": "Astro", "Atletiek": "Athletics", "Vierkant": "Quad",
        "Assessering": "Assessment", "Kwartaal": "Term", "Toets": "Test",
        "Mondeling": "Oral", "Toespraak": "Speech", "Hoofrekene": "Mental Maths",
        "Tegnologie": "Technology", "Wetenskap": "Science", "Wiskunde": "Mathematics",
        "Geskiedenis": "History", "Geografie": "Geography", "Sosiale Wetenskappe": "Social Sciences"
    }
    if "klaskamer" in text.lower() or "klas" in text.lower():
        text = re.sub(r'(?i)\bklaskamer\b|\bklas\b', "'s Classroom", text)
    for afrikaans, english in translations.items():
        text = re.sub(rf'\b{afrikaans}\b', english, text, flags=re.IGNORECASE)
    return text

def format_dle_spec(d_val, l_val, e_val):
    raw_act = clean_val(d_val)
    act = translate_term(raw_act, raw_act)
    age_raw = clean_val(l_val)
    team_raw = translate_term(clean_val(e_val), raw_act)
    if age_raw:
        age_part = age_raw if any(x in age_raw.upper() for x in ["GRADE", "GR", "U"]) else f"U{age_raw}"
    else: age_part = ""
    return f"{act} {age_part} {team_raw}".replace("  ", " ").strip()

@st.cache_data(ttl=1)
def load_data(url):
    try:
        r = requests.get(f"{url}&cb={datetime.now().timestamp()}", timeout=10)
        df = pd.read_csv(io.StringIO(r.content.decode('utf-8')))
        return df.fillna("")
    except: return pd.DataFrame()

# Header
st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", use_container_width=True)
st.markdown("<div style='background: linear-gradient(90deg, #008080, #006666); color:white; text-align:center; padding:15px; font-size:1.3rem; font-weight:800; border-radius:12px 12px 0 0;'>Laerskool Midstream College Primary Digital Hub</div>", unsafe_allow_html=True)

df_raw = load_data(EVENTS_URL)

with st.container():
    st.markdown("<div style='background:white; padding:20px; border-radius:0 0 12px 12px; border:1px solid #eee; box-shadow:0 4px 12px rgba(0,0,0,0.05); margin-bottom:20px;'>", unsafe_allow_html=True)
    if not df_raw.empty:
        c1, c2 = st.columns(2)
        with c1:
            sel_cat = st.multiselect("Category", ["All", "Sport", "Culture", "Academics"], default="All", key="f_cat")
        with c2:
            act_label = "Subjects" if "Academics" in sel_cat and len(sel_cat)==1 else "Activities"
            raw_acts = df_raw.iloc[:, 3].unique().tolist()
            clean_acts = sorted(list(set([translate_term(str(a).split()[0], str(a)) for a in raw_acts])))
            st.multiselect(act_label, ["All"] + clean_acts, default="All", key="f_act")
    st.markdown("---")
    search_q = st.text_input("Search", key="f_search", placeholder="Search Grade, Subject, Sport...")
    if st.button("REFRESH HUB", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

SA_TIME = pytz.timezone('Africa/Johannesburg')
today = datetime.now(SA_TIME).date()

if not df_raw.empty:
    df = df_raw.copy()
    df['dt_fixed'] = pd.to_datetime(df.iloc[:, 5], dayfirst=True, errors='coerce')
    
    # --- NUWE SLIM LOGIKA ---
    # Ons kyk of daar 'n 'Full Term' seleksie in Kolom M (index 12) is
    def should_show(row):
        is_full_term = False
        if len(row) > 12: # Kyk of Kolom M bestaan
            is_full_term = "full term" in str(row.iloc[12]).lower()
        
        if is_full_term: return True
        if pd.isnull(row['dt_fixed']): return True
        return row['dt_fixed'].date() >= today

    df = df[df.apply(should_show, axis=1)]
    # ------------------------

    if "All" not in st.session_state.f_act:
        df = df[df.iloc[:, 3].apply(lambda x: any(sel in translate_term(str(x), str(x)) for sel in st.session_state.f_act))]
    if "All" not in st.session_state.f_cat:
        df = df[df.iloc[:, 2].isin(st.session_state.f_cat)]
    search_terms = search_q.lower().split()

    h = """<style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
        body, div, p, a { font-family: 'Inter', sans-serif !important; }
        .card { background:white; padding:20px; border-radius:15px; border-left:10px solid #800000; margin-bottom:18px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); position: relative; }
        .card-title { color:#800000; font-size:1.2rem; font-weight:800; margin-bottom:10px; }
        .info-row { font-size:0.95rem; color:#444; margin: 8px 0; }
        .venue-bold { color:#008080 !important; font-weight:800; text-decoration:none; text-transform: uppercase; }
        .note-box { background:#e7f3f3; border-radius:8px; padding:12px; margin-top:12px; border-left:5px solid #008080; font-size:0.9rem; color:#004d4d; font-weight: 600; }
        .team-frame { border: 2px dotted #800000; border-radius: 8px; padding: 6px 10px; margin-top: 8px; display: inline-block; font-size: 0.85rem; color: #800000; font-weight: 700; background: #fff9f9; }
        .btn-box { display:flex; flex-wrap:wrap; gap:8px; margin-top:15px; }
        .btn { background:#800000 !important; color:white !important; padding:8px 12px; border-radius:8px; text-decoration:none; font-size:0.75rem; font-weight:700; text-transform:uppercase; display:inline-block; }
        @keyframes blink { 50% { opacity: 0; } }
    </style>"""

    for _, r in df.iterrows():
        raw_act_name = str(r.iloc[3])
        title_str = format_dle_spec(r.iloc[3], r.iloc[11], r.iloc[4])
        if search_terms and not any(term in title_str.lower() for term in search_terms): continue
        
        # As dit 'Full Term' is, wys ons nie 'n spesifieke datum nie, maar 'Full Term'
        is_ft = False
        if len(r) > 12: is_ft = "full term" in str(r.iloc[12]).lower()
        d_str = "FULL TERM" if is_ft else (r['dt_fixed'].strftime('%d %B %Y') if pd.notnull(r['dt_fixed']) else str(r.iloc[5]))
        
        ven_raw = translate_term(clean_val(r.iloc[6]), raw_act_name)
        prog_link = clean_val(r.iloc[7])
        on_site = ["hall", "auditorium", "pool", "tennis courts", "netball courts", "squash courts", "astro", "music room", "classroom", "quad"]
        ven_link = "http://googleusercontent.com/maps.google.com/maps?q=Midstream+College+Primary" if any(p in ven_raw.lower() for p in on_site) else f"http://googleusercontent.com/maps.google.com/maps?q={ven_raw.replace(' ', '+')}+South+Africa"
        is_acad = (str(r.iloc[2]).strip() == "Academics")
        prog_btn_text = "View Document" if is_acad else "Programme"
        team_btn_text = "Assessment Details" if is_acad else "Team List"
        info_label = "INFO" if is_acad else "TEAM"
        btns, extra_content = "", ""
        if "http" in prog_link.lower(): btns += f"<a href='{prog_link}' target='_blank' class='btn'>{prog_btn_text}</a>"
        team_info = translate_term(clean_val(r.iloc[8]), raw_act_name)
        if "http" in team_info.lower(): btns += f"<a href='{team_info}' target='_blank' class='btn'>{team_btn_text}</a>"
        elif team_info: extra_content += f"<div class='team-frame'>{info_label}: {team_info}</div>"
        note_raw = clean_val(r.iloc[10])
        note_display = translate_term(note_raw.replace("$", "").strip(), raw_act_name)
        if "http" in note_display.lower(): btns += f"<a href='{note_display}' target='_blank' class='btn'>Information</a>"
        elif note_display: extra_content += f"<div class='note-box'>NOTE: {note_display}</div>"
        badge = "<div style='position:absolute;top:15px;right:15px;background:red;color:white;padding:5px;border-radius:5px;font-size:0.7rem;animation:blink 1s infinite;'>NEW UPDATE</div>" if "$" in note_raw else ""
        h += f"""<div class='card'>{badge}<div class='card-title'>{title_str}</div>
                <div class='info-row'>📅&nbsp;&nbsp;{d_str}</div>
                <div class='info-row'>📍&nbsp;&nbsp;<a class='venue-bold' href='{ven_link}' target='_blank'>{ven_raw.upper()}</a></div>
                {extra_content}<div class='btn-box'>{btns}</div></div>"""
    components.html(h, height=2500, scrolling=True)
st.markdown("<div style='text-align:center;color:#999;font-size:0.8rem;'>Laerskool Midstream College Primary Digital Hub 2026</div>", unsafe_allow_html=True)
