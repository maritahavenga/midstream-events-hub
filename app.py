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
    if "klaskamer" in text.lower() or "klas" in text.lower():
        text = re.sub(r'(?i)\bklaskamer\b|\bklas\b', "'s Classroom", text)
    for afrikaans, english in translations.items():
        text = re.sub(rf'\b{afrikaans}\b', english, text, flags=re.IGNORECASE)
    return text

def format_dle_spec(d_val, l_val, e_val, category=""):
    raw_act = clean_val(d_val)
    act = translate_term(raw_act, raw_act)
    age_raw = clean_val(l_val)
    team_raw = translate_term(clean_val(e_val), raw_act)
    
    cat_clean = str(category).strip().lower()
    if age_raw:
        if "academic" in cat_clean:
            prefix = "Gr " if not any(x in age_raw.upper() for x in ["GRADE", "GR"]) else ""
            age_part = f"{prefix}{age_raw}"
        else:
            prefix = "U" if not any(x in age_raw.upper() for x in ["GRADE", "GR", "U"]) else ""
            age_part = f"{prefix}{age_raw}"
    else:
        age_part = ""
        
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

df_raw = load_data(EVENTS_URL)

with st.container():
    st.markdown("<div style='background:white; padding:20px; border-radius:12px; border:1px solid #eee; box-shadow:0 4px 12px rgba(0,0,0,0.05); margin-bottom:20px;'>", unsafe_allow_html=True)
    if not df_raw.empty:
        c1, c2, c3 = st.columns(3)
        with c1:
            sel_cat = st.multiselect("Category", ["All", "Sport", "Culture", "Academics"], default="All", key="f_cat")
        
        is_only_acad = "Academics" in sel_cat and len(sel_cat) == 1
        act_label = "Subjects" if is_only_acad else "Activities"
        age_label = "Grade" if is_only_acad else "Age / Grade"

        with c2:
            raw_acts = df_raw.iloc[:, 3].unique().tolist()
            clean_acts = sorted(list(set([translate_term(str(a).split()[0], str(a)) for a in raw_acts if a])))
            st.multiselect(act_label, ["All"] + clean_acts, default="All", key="f_act")
        
        with c3:
            raw_ages = sorted(list(set([clean_val(a) for a in df_raw.iloc[:, 11] if a])))
            st.multiselect(age_label, ["All"] + raw_ages, default="All", key="f_age")

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
    
    def should_show(row):
        if len(row) > 12 and "full term" in str(row.iloc[12]).lower(): return True
        if pd.isnull(row['dt_fixed']): return True
        return row['dt_fixed'].date() >= today

    df = df[df.apply(should_show, axis=1)]

    # --- VERBETERDE FILTER LOGIKA ---
    if "All" not in st.session_state.f_cat:
        # Hierdie kyk nou of die woord 'Academic' ENIGSINS in die kolom voorkom
        df = df[df.iloc[:, 2].apply(lambda x: any(c.lower() in str(x).lower() for c in st.session_state.f_cat))]
    
    if "All" not in st.session_state.f_act:
        df = df[df.iloc[:, 3].apply(lambda x: any(sel.lower() in translate_term(str(x), str(x)).lower() for sel in st.session_state.f_act))]
    
    if "All" not in st.session_state.f_age:
        df = df[df.iloc[:, 11].astype(str).apply(lambda x: any(a in clean_val(x) for a in st.session_state.f_age))]
        
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
    </style>"""

    for _, r in df.iterrows():
        this_cat = str(r.iloc[2]).strip()
        raw_act_name = str(r.iloc[3])
        title_str = format_dle_spec(r.iloc[3], r.iloc[11], r.iloc[4], this_cat)
        
        if search_terms and not any(term in title_str.lower() for term in search_terms): continue
        
        is_ft = len(r) > 12 and "full term" in str(r.iloc[12]).lower()
        d_str = "FULL TERM" if is_ft else (r['dt_fixed'].strftime('%d %B %Y') if pd.notnull(r['dt_fixed']) else str(r.iloc[5]))
        
        ven_raw = translate_term(clean_val(r.iloc[6]), raw_act_name)
        prog_link = clean_val(r.iloc[7])
        
        is_acad = "academic" in this_cat.lower()
        prog_btn_text = "Document" if is_acad else "Programme"
        team_btn_text = "Assessment Details" if is_acad else "Team List"
        info_label = "INFO" if is_acad else "TEAM"
        
        btns, extra_content = "", ""
        if "http" in prog_link.lower(): btns += f"<a href='{prog_link}' target='_blank' class='btn'>{prog_btn_text}</a>"
        team_info = translate_term(clean_val(r.iloc[8]), raw_act_name)
        if "http" in team_info.lower(): btns += f"<a href='{team_info}' target='_blank' class='btn'>{team_btn_text}</a>"
        elif team_info: extra_content += f"<div class='team-frame'>{info_label}: {team
