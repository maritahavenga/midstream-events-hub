import streamlit as st
import pandas as pd
import re
from datetime import datetime, timedelta
import pytz
import requests
import io
import urllib.parse
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

# 1. Config & Data
st.set_page_config(page_title="LMCP Event Hub", layout="centered")
st_autorefresh(interval=120000, key="datarefresh")

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?gid=0&single=true&output=csv"

def clean_text(text, is_group=False, is_category=False):
    if not text or str(text).lower() == 'nan': return ""
    t = str(text).strip()
    
    # 1. STANDAARDISEER KATEGORIEË
    if is_category:
        low_c = t.lower()
        if "acad" in low_c: return "Academics"
        if "sport" in low_c: return "Sport"
        if "cult" in low_c or "kult" in low_c: return "Culture"
    
    # 2. OUDERDOMME
    if is_group:
        nums = re.findall(r'\d+', t)
        if nums:
            age_num = nums[0]
            suffix = ""
            if "girl" in t.lower(): suffix = " Girls"
            elif "boy" in t.lower(): suffix = " Boys"
            return f"U{age_num}{suffix}"
    
    # 3. SPELFOUTE & VERTALINGS
    t_lower = t.lower()
    if "reve" in t_lower and "revue" not in t_lower:
        t = "Revue"
    
    corrections = {
        "atletiek": "Athletics", "swem": "Swimming", "hokkie": "Hockey",
        "muurbal": "Squash", "bergfiets": "Mountain Bike", "skaak": "Chess", "koor": "Choir"
    }
    
    for bad, good in corrections.items():
        if bad in t.lower(): return good
            
    return t.capitalize() if t.isupper() else t

@st.cache_data(ttl=10)
def load_data():
    try:
        r = requests.get(f"{URL}&cb={datetime.now().timestamp()}", timeout=10)
        df = pd.read_csv(io.StringIO(r.content.decode('utf-8')))
        # Maak data skoon soos dit inkom
        df.iloc[:, 0] = df.iloc[:, 0].apply(lambda x: clean_text(x, is_category=True))
        df.iloc[:, 1] = df.iloc[:, 1].apply(lambda x: clean_text(x))
        df.iloc[:, 2] = df.iloc[:, 2].apply(lambda x: clean_text(x, is_group=True))
        
        def parse_dt(x):
            s = str(x).strip()
            if not s or s.lower() == 'nan': return pd.NaT
            if '202' not in s: s = f"{s} {datetime.now().year}"
            return pd.to_datetime(s, dayfirst=True, errors='coerce')
        df['dt_fixed'] = df.iloc[:, 3].apply(parse_dt)
        return df
    except: return pd.DataFrame()

df_raw = load_data()
SA_TIME = pytz.timezone('Africa/Johannesburg')
today = datetime.now(SA_TIME).date()

# 2. UI Style
st.markdown("""
<style>
    [data-testid='stHeader'] {display: none;} 
    .block-container {padding:0 !important;}
    div.stButton > button {
        background-color: #800000 !important;
        color: white !important;
        border-radius: 10px;
        border: none;
        width: 100%;
        font-weight: bold;
        height: 3em;
    }
</style>
""", unsafe_allow_html=True)

st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", use_container_width=True)
st.markdown("<div style='background:#008080; color:white; text-align:center; padding:15px; font-size:1.4rem; font-weight:700; border-bottom: 5px solid #800000;'>Laerskool Midstream College Primary Event Hub</div>", unsafe_allow_html=True)

with st.container():
    st.markdown("<div style='background:white; padding:20px; border-radius:0 0 20px 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);'>", unsafe_allow_html=True)
    search_q = st.text_input("🔍 Search (e.g. Hockey or Academics):", placeholder="Type here...").lower().strip()
    col1, col2 = st.columns(2)
    with col1:
        cat_f = st.selectbox("Select Category:", ["All", "Sport", "Culture", "Academics"])
    with col2:
        act_opts = sorted(df_raw.iloc[:, 1].dropna().unique().tolist()) if not df_raw.empty else []
        act_f = st.multiselect("Select Activities:", act_opts)
    
    c3, c4 = st.columns([2, 1])
    with c3:
        view = st.radio("Date Range:", ["Upcoming", "Next 7 Days"], horizontal=True)
    with c4:
        if st.button("🔄 REFRESH"):
            st.cache_data.clear()
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# 3. Display Logic
if not df_raw.empty:
    df = df_raw[df_raw['dt_fixed'].dt.date >= today]
    if view == "Next 7 Days":
        df = df[df['dt_fixed'].dt.date <= today + timedelta(days=7)]
    
    # Filter vir Kategorie
    if cat_f != "All":
        df = df[df.iloc[:, 0] == cat_f]
        
    if act_f: 
        df = df[df.iloc[:, 1].isin(act_f)]
        
    if search_q:
        def match(r):
            row_str = " ".join(str(v) for v in r.values).lower()
            return search_q in row_str
        df = df[df.apply(match, axis=1).fillna(False)]

    h = """<style>
    @import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700&display=swap');
    body { background:#008080; font-family:'Source Sans 3', sans-serif; margin:0; padding:1
