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

# 1. Page Configuration
st.set_page_config(page_title="LMCP Event Hub", layout="centered")
st_autorefresh(interval=120000, key="datarefresh")

# 2. Data Loading
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data():
    try:
        r = requests.get(f"{DATA_URL}&cb={datetime.now().timestamp()}", timeout=10)
        df = pd.read_csv(io.StringIO(r.content.decode('utf-8')))
        def parse_dt(x):
            s = str(x).strip()
            if not s or s.lower() == 'nan': return pd.NaT
            if '202' not in s: s = f"{s} {datetime.now().year}"
            return pd.to_datetime(s, dayfirst=True, errors='coerce')
        df['dt_fixed'] = df.iloc[:, 3].apply(parse_dt)
        return df
    except:
        return pd.DataFrame()

df_raw = load_data()
SA_TIME = pytz.timezone('Africa/Johannesburg')
today = datetime.now(SA_TIME).date()

# 3. App UI & Sticky Filters
st.markdown("<style>[data-testid='stHeader'] {display: none;} .block-container {padding:0 !important;}</style>", unsafe_allow_html=True)

# LOGO & TITLE SECTION
st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", use_container_width=True)
st.markdown("<div style='background:#008080; color:white; text-align:center; padding:15px; font-size:1.4rem; font-weight:700; border-bottom: 5px solid #800000;'>Laerskool Midstream College Primary Event Hub</div>", unsafe_allow_html=True)

# FILTER BOX
with st.container():
    st.markdown("<div style='background:white; padding:20px; border-radius:0 0 20px 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);'>", unsafe_allow_html=True)
    
    search_q = st.text_input("🔍 Search (e.g. u7 or Athletics):", placeholder="Type here...").lower().strip()
    
    col1, col2 = st.columns(2)
    with col1:
        cat_options = ["All", "Sport", "Culture", "Academics"]
        cat_filter = st.selectbox("Select Category:", cat_options)
    with col2:
        all_activities = sorted(df_raw.iloc[:, 1].dropna().unique().tolist()) if not df_raw.empty else []
        act_filter = st.multiselect("Select Activities:", all_activities, placeholder="e.g. Swimming, Athletics")
    
    c3, c4 = st.columns([2, 1])
    with c3:
        view = st.radio("Date Range:", ["Upcoming", "Next 7 Days"], horizontal=True)
    with c4:
        if st.button("🔄 REFRESH"):
            st.cache_data.clear()
            st.rerun()
            
    st.markdown("</div>", unsafe_allow_html=True)

# 4. Filter & Build HTML
if not df_raw.empty:
    if view == "Upcoming":
        df = df_raw[df_raw['dt_fixed'].dt.date >= today].sort_values(by='dt_fixed')
    else:
        df = df_raw[(df_raw['dt_fixed'].dt.date >= today) & (df_raw['dt_fixed'].dt.date <= today + timedelta(days=7))].sort_values(by='dt_fixed')
    
    if cat_filter != "All":
        df = df[df.iloc[:, 0].str.contains(cat_filter, case=False, na=False)]
    if act_filter:
        df = df[df.iloc[:, 1].isin(act_filter)]
        
    # VERBETERDE SMART SEARCH
    if search_q:
        def smart_match(row):
            text_pool = str(row.values).lower()
            # As ouer "u7" (of u8 ens) tik, en die sport is Athletics of Swimming, wys dit altyd
            is_age_search = re.search(r'u\s?\d+', search_q)
            is_mass_sport = any(x in str(row.iloc[1]).lower() for x in ['athletics', 'swimming', 'atletiek', 'swem', 'gala'])
            
            if search_q in text_pool:
                return True
            if is_age_search and is_mass_sport:
                return True
            return False
            
        df = df[df.apply(smart_match, axis=1)]

    INTERNAL_STYLE = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700&display=swap');
    body { background:#008080; font-family:'Source Sans 3', sans-serif; margin:0; padding:15px; }
    .card { background:white; padding:25px; border-radius:22px; border-left:12px solid #800000; margin-bottom:20px; box-shadow:0 6px 15px rgba(0,0,0,0.15); }
    .card-date { color:#666; font-size:0.85rem; }
    .card-title { color:#800000; font-size:1.4rem; font-weight:700; margin: 5px 0; }
    .venue { color:#008080; font-weight:600; text-decoration:none; font-size: 0.9rem; }
    .team-box { background:#fff3f3; padding:12px; border-radius:10px; margin:10px 0; border:1px dashed #800000; color:#800000; font-size:0.85rem; }
    .note-box { background:#f8f9fa; padding:12px; border-radius:10px; margin:10px 0; border-left:5px solid #008080; color:#333; font-size:0.85rem; }
    .btn-row { display:flex; flex-wrap:wrap; gap:8px; margin-top:12px; }
    .btn { background:#800000; color:white !important; padding:8px 16px; border-radius:10px; font-weight:600; text-decoration:none; font-size:0.75rem; display:inline-block; }
    </style>
    """

    cards_
