import streamlit as st
import pandas as pd
import urllib.parse as up
import re
from datetime import datetime, timedelta
import pytz
import requests
import io
import time
from streamlit_autorefresh import st_autorefresh

# 1. Page Configuration
st.set_page_config(page_title="LMCP Live Fixtures", layout="centered")
st_autorefresh(interval=120000, key="datarefresh")

# 2. Styling
st.markdown("""<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stTabs {display: none !important;}
.stApp{background:#008080}.block-container{padding:1rem;max-width:500px}
.card{background:white!important;padding:18px;border-radius:15px;border-left:12px solid #800000;margin-bottom:15px;box-shadow:0 4px 10px rgba(0,0,0,0.2)}
.t{color:#800000!important;font-weight:bold;font-size:1.15rem;margin:5px 0}.v{color:#800000!important;font-weight:bold;text-decoration:underline}
.box{background:#f8f9fa;padding:12px;border-radius:10px;margin:10px 0;border-left:5px solid #008080;color:#333;font-size:0.9rem;line-height:1.4;white-space: pre-wrap;}
.btn-row {display:flex!important; gap:4px!important; justify-content:space-between!important; margin-top:15px!important; width:100%!important;}
.btn { flex:1!important; background:#800000!important; color:white!important; text-align:center!important; text-decoration:none!important; font-weight:bold!important; font-size:0.65rem!important; padding:12px 2px!important; border-radius:6px!important; display:block!important; white-space:nowrap!important;}
h2 { color: white !important; text-align: center; margin-top: 10px; text-transform: uppercase; letter-spacing: 1px;}
div[data-baseweb="select"] > div { background-color:#800000 !important; border:none !important; }
div[data-baseweb="select"] * { color:white !important; }
label { color:white !important; font-weight:bold; }
.stButton>button { width:100%; background-color:#800000; color:white; border:2px solid #00cccc; font-size:0.9rem; border-radius:10px; height:45px; font-weight:bold; margin-bottom:10px;}
</style>
""", unsafe_allow_html=True)

URL_DATA = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=60)
def load_live_data():
    try:
        SA_TIME = pytz.timezone('Africa/Johannesburg')
        now = datetime.now(SA_TIME).date()
        response = requests.get(f"{URL_DATA}&refresh={int(time.time())}", timeout=10)
        df = pd.read_csv(io.StringIO(response.text))
        def parse_dt(x):
            s = str(x).strip()
            if not s or s.lower() == 'nan': return pd.NaT
            if '202' not in s: s = f"{s} 2026"
            return pd.to_datetime(s, dayfirst=True, errors='coerce')
        df['dt_fixed'] = df.iloc[:, 3].apply(parse_dt)
        df = df[df['dt_fixed'].dt.date >= now].sort_values(by='dt_fixed')
        return df, now, datetime.now(SA_TIME)
    except:
        return pd.DataFrame(), datetime.now().date(), datetime.now()

st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", use_container_width=True)
df_live, today_date, update_time = load_live_data()

st.markdown("<h2>Upcoming Fixtures</h2>", unsafe_allow_html=True)

if not df_live.empty:
    # 1. Radio Button (7 dae vs Alles)
    view_opt = st.radio("View Range:", ["All Upcoming", "Next 7 Days"], horizontal=True, key="range_v")
    
    if st.button(f"🔄 REFRESH (Update: {update_time.strftime('%H:%M')})", key="ref_v"):
        st.cache_data.clear()
        st.rerun()

    # 2. Search Bar
    raw_s = st.text_input("🔍 Search:", key="search_v")
    
    c = st.columns([1, 1, 1])
    with c[0]: 
        cat = st.selectbox("Type:", ["All", "Sport", "Culture", "Academics"], key="cat_v")
    
    f_df = df_live if cat == "All" else df_live[df_live.iloc[:, 0].str.contains(cat, case=False, na=False)]
    if view_opt == "Next 7 Days":
        f_df = f_df[f_df['dt_fixed'].dt.date <= (today_date + timedelta(days=7))]

    # 3. Multiselects met unieke keys vir geheue
    with c[1]: 
        sel_acts = st.multiselect("Activity:", sorted(f_df.iloc[:, 1].dropna().unique()), key="act_v")
    with c[2]: 
        sel_ages = st.multiselect("Age Group:", sorted(f_df.iloc[:, 2].dropna().unique()), key="age_v")

    # Filter logika
    final_df = f_df
    if raw_s:
        final_df = final_df[final_df.apply(lambda r: raw_s.lower() in str(r).lower(), axis=1)]
    if sel_acts:
        final_df = final_df[final_df.iloc[:, 1].isin(sel_acts)]
    if sel_ages:
        final_df = final_df[final_df.iloc[:, 2].isin(sel_ages)]

    if not final_df.empty:
        for i, r in final_df.iterrows():
            age_val = str(r.iloc[2]).strip()
            title = f"{r.iloc[1]} {age_val}"
            dat = r['dt_fixed'].strftime('%d %B %Y')
            st.markdown(f'<div class="card"><div style="font-size:0.85rem;color:#333">🗓️ {dat}</div><div class="t">{title}</div><div style="font-size:0.85rem;color:#333">📍 {r.iloc[4]}</div></div>', unsafe_allow_html=True)
    else:
        st.info("No events found.")
