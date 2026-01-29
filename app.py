import streamlit as st
import pandas as pd
import requests
import io
import re
from datetime import datetime
import pytz
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

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
        "Muurbalbane": "Squash Courts", "Muurbal": "Squash", "Veld": "Field",
        "Koor": "Choir", "Astro": "Astro", "Atletiek": "Athletics", "Vierkant": "Quad",
        "Assessering": "Assessment", "Kwartaal": "Term", "Toets": "Test",
        "Mondeling": "Oral", "Toespraak": "Speech", "Hoofrekene": "Mental Maths",
        "Tegnologie": "Technology", "Wetenskap": "Science", "Wiskunde": "Mathematics",
        "Geskiedenis": "History", "Geografie": "Geography", "Sosiale Wetenskappe": "Social Sciences"
    }
    for afrikaans, english in translations.items():
        text = re.sub(rf'\b{afrikaans}\b', english, text, flags=re.IGNORECASE)
    return text

@st.cache_data(ttl=1)
def load_data(url):
    try:
        r = requests.get(f"{url}&cb={datetime.now().timestamp()}", timeout=10)
        df = pd.read_csv(io.StringIO(r.content.decode('utf-8')))
        # Strip spasies van kolomname af om foute te voorkom
        df.columns = [c.strip() for c in df.columns]
        return df.fillna("")
    except: return pd.DataFrame()

st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", use_container_width=True)
df_raw = load_data(EVENTS_URL)

# Kolom Name vir verwysing
CAT_COL = "Category"
ACT_COL = "Activity / Subject name"
DATE_COL = "Date / Due Date"
AGE_COL = "Age Group (9,10) / Grade (1,2,3)"
DUR_COL = "Display Duration"
TEAM_COL = "Team / Assessment"
VENUE_COL = "Venue"
PROG_COL = "Programme / Document Link"
INFO_COL = "Team List / Information"
NOTE_COL = "Note"

if not df_raw.empty:
    # 1. Filters Area
    with st.container():
        st.markdown("<div style='background:white; padding:20px; border-radius:12px; border:1px solid #eee; box-shadow:0 4px 12px rgba(0,0,0,0.05); margin-bottom:20px;'>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        
        with c1:
            cats = ["All"] + sorted([str(x) for x in df_raw[CAT_COL].unique() if x])
            sel_cat = st.multiselect("Category", cats, default="All", key="f_cat")
        
        is_only_acad = any("Academic" in str(c) for c in sel_cat)
        act_label = "Subjects" if is_only_acad else "Activities"
        age_label = "Grade" if is_only_acad else "Age / Grade"

        with c2:
            raw_acts = sorted([str(x) for x in df_raw[ACT_COL].unique() if x])
            st.multiselect(act_label, ["All"] + raw_acts, default="All", key="f_act")
        
        with c3:
            raw_ages = sorted([str(x) for x in df_raw[AGE_COL].unique() if x])
            st.multiselect(age_label, ["All"] + raw_ages, default="All", key="f_age")

        search_q = st.text_input("Search", key="f_search", placeholder="Search Grade, Subject, Sport...")
        if st.button("REFRESH HUB", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # 2. Data Processing
    SA_TIME = pytz.timezone('Africa/Johannesburg')
    today = datetime.now(SA_TIME).date()
    df = df_raw.copy()
    
    # Datum skoonmaak
    df['dt_fixed'] = pd.to_datetime(df[DATE_COL], dayfirst=True, errors='coerce')
    
    def filter_logic(row):
        # Wys as dit vandag/toekoms is OF as Duration 'Full Term' is
        show_by_date = pd.isnull(row['dt_fixed']) or row['dt_fixed'].date() >= today
        show_by_dur = False
        if DUR_COL in row:
            show_by_dur = "full term" in str(row[DUR_COL]).lower()
        
        if not (show_by_date or show_by_dur): return False
        
        # Kategorie Filter
        if "All" not in st.session_state.f_cat:
            if not any(str(c).lower() in str(row[CAT_COL]).lower() for c in st.session_state.f_cat): return False
            
        # Aktiwiteit Filter
        if "All" not in st.session_state.f_act:
            if not any(str(a).lower() in str(row[ACT_COL]).lower() for a in st.session_state.f_act): return False
            
        # Ouderdom Filter
        if "All" not in st.session_state.f_age:
            if str(row[AGE_COL]) not in st.session_state.f_age: return False
            
        return True

    df = df[df.apply(filter_logic, axis=1)]

    # 3. Display
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
    </style>"""

    for _, r in df.iterrows():
        # Bepaal Kategorie-tipe
        is_acad = "academic" in str(r[CAT_COL]).lower()
        
        # Formateer Titel
        act_name = translate_term(str(r[ACT_COL]), str(r[ACT_COL]))
        age_val = str(r[AGE_COL])
        prefix = "Gr " if is_acad else "U"
        age_str = f"{prefix}{age_val}" if age_val else ""
        team_str = translate_term(str(r[TEAM_COL]), str(r[ACT_COL]))
        title_str = f"{act_name} {age_str} {team_str}".strip()
        
        if st.session_state.f_search and st.session_state.f_search.lower() not in title_str.lower(): continue
        
        is_ft = DUR_COL in r and "full term" in str(r[DUR_COL]).lower()
        d_str = "FULL TERM" if is_ft else (r['dt_fixed'].strftime('%d %B %Y') if pd.notnull(r['dt_fixed']) else str(r[DATE_COL]))
        
        # Buttons & Content
        prog_btn = "Document" if is_acad else "Programme"
        info_lbl = "INFO" if is_acad else "TEAM"
        btns, extra = "", ""
        
        if "http" in str(r[PROG_COL]).lower(): btns += f"<a href='{r[PROG_COL]}' target='_blank' class='btn'>{prog_btn}</a>"
        if "http" in str(r[INFO_COL]).lower(): btns += f"<a href='{r[INFO_COL]}' target='_blank' class='btn'>Assessment Details</a>"
        elif clean_val(r[INFO_COL]): extra += f"<div class='team-frame'>{info_lbl}: {r[INFO_COL]}</div>"
        
        note_text = clean_val(r[NOTE_COL]).replace("$", "")
        if "http" in note_text.lower(): btns += f"<a href='{note_text}' target='_blank' class='btn'>Info</a>"
        elif note_text: extra += f"<div class='note-box'>NOTE: {note_text}</div>"
        
        badge = "<div style='position:absolute;top:15px;right:15px;background:red;color:white;padding:5px;border-radius:5px;font-size:0.7rem;animation:blink 1s infinite;'>NEW UPDATE</div>" if "$" in str(r[NOTE_COL]) else ""
        ven_raw = translate_term(str(r[VENUE_COL]), str(r[ACT_COL]))
        
        h += f"""<div class='card'>{badge}<div class='card-title'>{title_str}</div>
                <div class='info-row'>📅&nbsp;&nbsp;{d_str}</div>
                <div class='info-row'>📍&nbsp;&nbsp;<span class='venue-bold'>{ven_raw.upper()}</span></div>
                {extra}<div class='btn-box'>{btns}</div></div>"""
                
    components.html(h, height=2500, scrolling=True)

st.markdown("<div style='text-align:center;color:#999;font-size:0.8rem;'>Laerskool Midstream College Primary Digital Hub 202
