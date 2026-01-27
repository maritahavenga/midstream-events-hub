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

@st.cache_data(ttl=60)
def load_data():
    try:
        r = requests.get(f"{URL}&cb={datetime.now().timestamp()}", timeout=10)
        df = pd.read_csv(io.StringIO(r.content.decode('utf-8')))
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

# 2. UI Header
st.markdown("<style>[data-testid='stHeader'] {display: none;} .block-container {padding:0 !important;}</style>", unsafe_allow_html=True)
st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", use_container_width=True)
st.markdown("<div style='background:#008080; color:white; text-align:center; padding:15px; font-size:1.4rem; font-weight:700; border-bottom: 5px solid #800000;'>Laerskool Midstream College Primary Event Hub</div>", unsafe_allow_html=True)

with st.container():
    st.markdown("<div style='background:white; padding:20px; border-radius:0 0 20px 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);'>", unsafe_allow_html=True)
    search_q = st.text_input("🔍 Search (e.g. u7 or Athletics):", placeholder="Type here...").lower().strip()
    c1, c2 = st.columns(2)
    with c1: view = st.radio("Date Range:", ["Upcoming", "Next 7 Days"], horizontal=True)
    with c2: 
        cats = ["All", "Sport", "Culture", "Academics"]
        cat_f = st.selectbox("Category:", cats)
    
    acts = sorted(df_raw.iloc[:, 1].dropna().unique().tolist()) if not df_raw.empty else []
    act_f = st.multiselect("Select Activities:", acts)
    
    if st.button("🔄 REFRESH"):
        st.cache_data.clear()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# 3. Logic & Rendering
if not df_raw.empty:
    df = df_raw[df_raw['dt_fixed'].dt.date >= today]
    if view == "Next 7 Days":
        df = df[df['dt_fixed'].dt.date <= today + timedelta(days=7)]
    
    if cat_f != "All": df = df[df.iloc[:, 0].str.contains(cat_f, case=False, na=False)]
    if act_f: df = df[df.iloc[:, 1].isin(act_f)]
    if search_q:
        def match(r):
            pool = str(r.values).lower()
            is_age = re.search(r'u\s?\d+', search_q)
            is_mass = any(x in str(r.iloc[1]).lower() for x in ['athletics', 'swimming', 'atletiek', 'swem', 'gala'])
            return (search_q in pool) or (is_age and is_mass)
        df = df[df.apply(match, axis=1)]

    h = """<style>
    @import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700&display=swap');
    body { background:#008080; font-family:'Source Sans 3', sans-serif; margin:0; padding:15px; }
    .card { background:white; padding:25px; border-radius:22px; border-left:12px solid #800000; margin-bottom:20px; box-shadow:0 6px 15px rgba(0,0,0,0.15); position: relative; }
    .new-badge { position: absolute; top: 15px; right: 15px; background: #ffcc00; color: #800000; padding: 4px 10px; border-radius: 8px; font-weight: bold; font-size: 0.7rem; text-transform: uppercase; animation: flash 1.5s infinite; border: 1px solid #800000; }
    @keyframes flash { 0% { opacity: 1; } 50% { opacity: 0.4; } 100% { opacity: 1; } }
    .card-title { color:#800000; font-size:1.4rem; font-weight:700; margin: 5px 0; }
    .venue { color:#008080; font-weight:600; text-decoration:none; font-size: 0.9rem; }
    .team-box { background:#fff3f3; padding:12px; border-radius:10px; margin:10px 0; border:1px dashed #800000; color:#800000; font-size:0.85rem; }
    .note-box { background:#f8f9fa; padding:12px; border-radius:10px; margin:10px 0; border-left:5px solid #008080; color:#333; font-size:0.85rem; }
    .btn-row { display:flex; flex-wrap:wrap; gap:8px; margin-top:12px; }
    .btn { background:#800000; color:white !important; padding:8px 16px; border-radius:10px; font-weight:600; text-decoration:none; font-size:0.75rem; display:inline-block; }
    </style>"""

    for _, r in df.sort_values('dt_fixed').iterrows():
        sport, age = str(r.iloc[1]), (str(r.iloc[2]) if str(r.iloc[2]).lower() != 'nan' else "")
        dt_s = r['dt_fixed'].strftime('%d %B %Y') if pd.notnull(r['dt_fixed']) else "TBA"
        ven = str(r.iloc[4])
        t_b, b_r, n_b, badge = "", "", "", ""
        
        # --- SMART BADGE LOGIC ---
        info_text = str(r.iloc[8]).lower()
        team_text = str(r.iloc[6]).lower()
        # Wys badge as die datum vandag/môre is OF as jy "NEW", "NUUT" of "!" in die teks tik
        if (pd.notnull(r['dt_fixed']) and r['dt_fixed'].date() <= today + timedelta(days=1)) or \
           any(word in info_text or word in team_text for word in ["new", "nuut", "!"]):
