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
from streamlit_javascript import st_javascript

# 1. Page Configuration
st.set_page_config(page_title="LMCP Live Fixtures", layout="centered")
st_autorefresh(interval=120000, key="datarefresh")

# 2. Styling
st.markdown("""<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stApp{background:#008080}.block-container{padding:1rem;max-width:500px}
.card{background:white;padding:18px;border-radius:15px;border-left:12px solid #800000;margin-bottom:15px;box-shadow:0 4px 10px rgba(0,0,0,0.2)}
.t{color:#800000;font-weight:bold;font-size:1.15rem;margin:5px 0}
.box{background:#f8f9fa;padding:12px;border-radius:10px;margin:10px 0;border-left:5px solid #008080;color:#333;font-size:0.85rem;}
div[data-baseweb="select"] > div { background-color:#800000 !important; }
div[data-baseweb="select"] * { color:white !important; }
label { color:white !important; font-weight:bold; }
.stButton>button { width:100%; background-color:#800000; color:white; border-radius:10px; font-weight:bold;}
</style>
""", unsafe_allow_html=True)

URL_DATA = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?gid=0&single=true&output=csv"

# --- PERSISTENCE ENGINE (LOCAL STORAGE) ---
# This reads the "Post-it note" from the phone
saved_act = st_javascript("localStorage.getItem('saved_act');")
saved_age = st_javascript("localStorage.getItem('saved_age');")

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
        return df[df['dt_fixed'].dt.date >= now].sort_values(by='dt_fixed'), now, datetime.now(SA_TIME)
    except:
        return pd.DataFrame(), datetime.now().date(), datetime.now()

st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", use_container_width=True)
df_live, today_date, update_time = load_live_data()

if st.button(f"🔄 REFRESH DATA ({update_time.strftime('%H:%M')})"):
    st.cache_data.clear()
    st.rerun()

if not df_live.empty:
    c = st.columns(2)
    
    # Activity Filter
    all_acts = sorted([str(a) for a in df_live.iloc[:, 1].dropna().unique() if str(a).lower() != 'nan'])
    
    # Process saved memory
    default_act = []
    if saved_act and saved_act != "null":
        default_act = [a for a in saved_act.split(',') if a in all_acts]
    if not default_act: # Fallback for your specific crisis
        default_act = [a for a in ["Swimming", "Athletics", "Swem", "Atletiek"] if a in all_acts]

    with c[0]:
        sel_acts = st.multiselect("Activity:", all_acts, default=default_act, key="act_v")
    
    # Save choice to phone immediately
    if sel_acts:
        st_javascript(f"localStorage.setItem('saved_act', '{','.join(sel_acts)}');")

    # Age Group Filter
    all_ages = sorted([str(a) for a in df_live.iloc[:, 2].dropna().unique() if str(a).lower() != 'nan'])
    default_age = []
    if saved_age and saved_age != "null":
        default_age = [a for a in saved_age.split(',') if a in all_ages]

    with c[1]:
        sel_ages = st.multiselect("Age Group:", all_ages, default=default_age, key="age_v")
    
    if sel_ages:
        st_javascript(f"localStorage.setItem('saved_age', '{','.join(sel_ages)}');")

    # Filter Logic
    f_df = df_live
    if sel_acts: f_df = f_df[f_df.iloc[:, 1].astype(str).isin(sel_acts)]
    if sel_ages: f_df = f_df[f_df.iloc[:, 2].astype(str).isin(sel_ages)]

    # 3. Display
    for i, r in f_df.iterrows():
        st.markdown(f"""
        <div class="card">
            <div style="color:#333; font-size:0.85rem;">🗓️ {r['dt_fixed'].strftime('%d %B %Y')}</div>
            <div class="t">{r.iloc[1]} {str(r.iloc[2]) if str(r.iloc[2]).lower() != 'nan' else ''}</div>
            <div style="color:#333; font-size:0.85rem;">📍 {r.iloc[4]}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Native Buttons for Athletics & Swimming
        btn_cols = st.columns(4)
        labels = ["PROGRAMME", "TEAM", "CONFIRM", "INFO"]
        for idx, label in enumerate(labels):
            link_raw = str(r.iloc[5+idx])
            link = re.search(r'(https?://[^\s<>"]+)', link_raw)
            if link:
                with btn_cols[idx]:
                    st.link_button(label, link.group(0), use_container_width=True)
        
        note = str(r.iloc[8]).strip()
        if note.lower() != 'nan' and 'http' not in note.lower():
            st.markdown(f'<div class="box"><b>Note:</b><br>{note}</div>', unsafe_allow_html=True)
        st.markdown("---")
else:
    st.info("No fixtures found.")
