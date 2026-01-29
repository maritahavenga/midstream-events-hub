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
        df.columns = [c.strip() for c in df.columns]
        return df.fillna("")
    except: return pd.DataFrame()

st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", use_container_width=True)
df_raw = load_data(EVENTS_URL)

# --- SLIM KOLOM-SOEKER (Hanteer KeyError) ---
def find_col(possible_names, default_index):
    for name in possible_names:
        for actual_col in df_raw.columns:
            if name.lower() in actual_col.lower():
                return actual_col
    if df_raw.shape[1] > default_index:
        return df_raw.columns[default_index]
    return df_raw.columns[0]

if not df_raw.empty:
    # Ken kolomme toe gebaseer op teks-soektog in die opskrifte
    CAT_COL = find_col(["category"], 2)
    ACT_COL = find_col(["activity", "subject"], 3)
    DATE_COL = find_col(["date"], 5)
    AGE_COL = find_col(["age", "grade"], 11)
    DUR_COL = find_col(["duration"], 12)
    TEAM_COL = find_col(["team", "assessment"], 4)
    VENUE_COL = find_col(["venue"], 6)
    PROG_COL = find_col(["programme", "document"], 7)
    INFO_COL = find_col(["list", "information"], 8)
    NOTE_COL = find_col(["note"], 10)

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

    SA_TIME = pytz.timezone('Africa/Johannesburg')
    today = datetime.now(SA_TIME).date()
    df = df_raw.copy()
    df['dt_fixed'] = pd.to_datetime(df[DATE_COL], dayfirst=True, errors='coerce')
    
    def filter_logic(row):
        show_by_date = pd.isnull(row['dt_fixed']) or row['dt_fixed'].date() >= today
        show_by_dur = "full term" in str(row[DUR_COL]).lower() if DUR_COL in row else False
        if not (show_by_date or show_by_dur): return False
        
        if "All" not in st.session_state.f_cat:
            if not any(str(c).lower() in
