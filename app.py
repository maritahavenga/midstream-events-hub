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

# 2. Styling (Skoon en stabiel)
st.markdown("""<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stApp{background:#008080}.block-container{padding:1rem;max-width:500px}
.card{background:white!important;padding:18px;border-radius:15px;border-left:12px solid #800000;margin-bottom:15px;box-shadow:0 4px 10px rgba(0,0,0,0.2)}
.t{color:#800000!important;font-weight:bold;font-size:1.15rem;margin:5px 0}
.box{background:#f8f9fa;padding:12px;border-radius:10px;margin:10px 0;border-left:5px solid #008080;color:#333;font-size:0.85rem;}
label { color:white !important; font-weight:bold; }
h2 { color: white !important; text-align: center; text-transform: uppercase; margin-top:0;}
.stButton>button { width:100%; background-color:#800000; color:white; border:2px solid #00cccc; border-radius:10px; font-weight:bold; margin-bottom:10px;}
</style>
""", unsafe_allow_html=True)

URL_DATA = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?gid=0&single=true&output=csv"

def get_link(val):
    s = str(val).strip()
    if s.lower() == 'nan' or not s: return None
    m = re.search(r'(https?://[^\s<>"]+)', s)
    return m.group(0) if m else None

def load_live_data():
    try:
        SA_TIME = pytz.timezone('Africa/Johannesburg')
        now = datetime.now(SA_TIME).date()
        response = requests.get(f"{URL_DATA}&refresh={int(time.time())}", timeout=10)
        df = pd.read_csv(io.StringIO(response.text))
        df = df.dropna(subset=[df.columns[1]]) # Verwyder leë rye
        
        def parse_dt(x):
            s = str(x).strip()
            if not s or s.lower() == 'nan': return pd.NaT
            if '202' not in s: s = f"{s} 2026"
            return pd.to_datetime(s, dayfirst=True, errors='coerce')
        
        df['dt_fixed'] = df.iloc[:, 3].apply(parse_dt)
        return df[df['dt_fixed'].dt.date >= now].sort_values(by='dt_fixed'), now, datetime.now(SA_TIME)
    except:
        return pd.DataFrame(), datetime.now().date(), datetime.now()

st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", use_container_width=True)
df_live, today_date, update_time = load_live_data()

# Refresh Button
if st.button(f"🔄 REFRESH DATA ({update_time.strftime('%H:%M')})"):
    st.cache_data.clear()
    st.rerun()

st.markdown("<h2>Upcoming Fixtures</h2>", unsafe_allow_html=True)

if not df_live.empty:
    # FILTERS
    c = st.columns(2)
    all_acts = sorted([str(a) for a in df_live.iloc[:, 1].dropna().unique() if str(a).lower() != 'nan'])
    
    # HARD-CODE: Hierdie is altyd gekies as die app oopmaak
    defaults = [a for a in ["Athletics", "Swimming", "Atletiek", "Swem"] if a in all_acts]
    
    with c[0]:
        sel_acts = st.multiselect("Activity:", all_acts, default=defaults, key="act_v")
    with c[1]:
        all_ages = sorted([str(a) for a in df_live.iloc[:, 2].dropna().unique() if str(a).lower() != 'nan'])
        sel_ages = st.multiselect("Age Group:", all_ages, key="age_v")

    # Filter Logika
    f_df = df_live
    if sel_acts: f_df = f_df[f_df.iloc[:, 1].astype(str).isin(sel_acts)]
    if sel_ages: f_df = f_df[f_df.iloc[:, 2].astype(str).isin(sel_ages)]

    # VERTOON DATA
    for i, r in f_df.iterrows():
        st.markdown(f"""
        <div class="card">
            <div style="color:#333; font-size:0.85rem;">🗓️ {r['dt_fixed'].strftime('%d %B %Y')}</div>
            <div class="t">{r.iloc[1]} {str(r.iloc[2]) if str(r.iloc[2]).lower() != 'nan' else ''}</div>
            <div style="color:#333; font-size:0.85rem;">📍 {r.iloc[4]}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Knoppies (Standaard Streamlit Buttons - Hulle verdwyn nooit nie!)
        btn_cols = st.columns(4)
        labels = ["PROGRAMME", "TEAM", "CONFIRM", "INFO"]
        for idx, label in enumerate(labels):
            link = get_link(r.iloc[5+idx])
            if link:
                with btn_cols[idx]:
                    st.link_button(label, link, use_container_width=True)
        
        note = str(r.iloc[8]).strip()
        if note.lower() != 'nan' and not get_link(note):
            st.markdown(f'<div class="box"><b>Note:</b><br>{note}</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
else:
    st.info("Geen fixtures gevind nie.")
