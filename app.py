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

# 2. Styling (Suiwer Maroen - Geen Teal nie)
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stApp{background:#008080}.block-container{padding:1rem;max-width:500px}
.card{background:white!important;padding:18px;border-radius:15px;border-left:12px solid #800000;margin-bottom:15px;box-shadow:0 4px 10px rgba(0,0,0,0.2)}
.t{color:#800000!important;font-weight:bold;font-size:1.15rem;margin:5px 0}
.box{background:#f8f9fa;padding:12px;border-radius:8px;margin:10px 0;border-left:5px solid #800000;color:#333;font-size:0.85rem;}
.btn-row {display:flex!important; gap:4px!important; justify-content:space-between!important; margin-top:10px!important; width:100%!important; flex-wrap: wrap;}
.btn { flex:1 1 auto!important; background:#800000!important; color:white!important; text-align:center!important; text-decoration:none!important; font-weight:bold!important; font-size:0.65rem!important; padding:10px 5px!important; border-radius:6px!important; display:block!important; border:none!important; margin-bottom:4px;}
label { color:white !important; font-weight:bold; }
h2 { color: white !important; text-align: center; text-transform: uppercase;}
.stButton>button { width:100%; background-color:#800000; color:white; border:none; border-radius:10px; font-weight:bold;}
</style>
""", unsafe_allow_html=True)

URL_DATA = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?gid=0&single=true&output=csv"

def load_live_data():
    try:
        SA_TIME = pytz.timezone('Africa/Johannesburg')
        now = datetime.now(SA_TIME).date()
        # Dwing vars data met 'n tydstempel
        response = requests.get(f"{URL_DATA}&nocache={time.time()}", timeout=10)
        df = pd.read_csv(io.StringIO(response.text))
        
        # Maak seker kolomme is skoon
        df.columns = [c.strip() for c in df.columns]
        
        def parse_dt(x):
            s = str(x).strip()
            if not s or s.lower() == 'nan': return pd.NaT
            if '202' not in s: s = f"{s} 2026"
            return pd.to_datetime(s, dayfirst=True, errors='coerce')
        
        # Soek die datum kolom (gewoonlik die 4de een)
        df['dt_fixed'] = df.iloc[:, 3].apply(parse_dt)
        return df[df['dt_fixed'].dt.date >= now].sort_values(by='dt_fixed'), now, datetime.now(SA_TIME)
    except:
        return pd.DataFrame(), datetime.now().date(), datetime.now()

st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", use_container_width=True)
df_live, today_date, update_time = load_live_data()

if st.button(f"🔄 FORCE REFRESH ({update_time.strftime('%H:%M')})"):
    st.cache_data.clear()
    st.rerun()

if not df_live.empty:
    url_acts = st.query_params.get_all("act")
    all_acts = sorted([str(a) for a in df_live.iloc[:, 1].dropna().unique() if str(a).lower() != 'nan'])
    sel_acts = st.multiselect("Activity:", all_acts, default=url_acts if (url_acts and all(a in all_acts for a in url_acts)) else None)
    st.query_params["act"] = sel_acts

    f_df = df_live
    if sel_acts:
        f_df = f_df[f_df.iloc[:, 1].astype(str).isin(sel_acts)]

    for i, r in f_df.iterrows():
        # --- AGE GROUP & SPORT (FORCE) ---
        sport = str(r.iloc[1])
        # Ons kombineer Sport en Age Group (Kolom 2) in een lyn
        age = str(r.iloc[2]) if str(r.iloc[2]).lower() != 'nan' else ""
        venue = str(r.iloc[4])
        date_str = r['dt_fixed'].strftime('%d %B %Y')
        
        # Knoppies
        btns = []
        has_info_link = False
        labels = ["PROGRAMME", "TEAM", "CONFIRM", "INFORMATION"]
        for idx, label in enumerate(labels):
            val = str(r.iloc[5+idx]).strip()
            match = re.search(r'(https?://[^\s<>"]+)', val)
            if match:
                btns.append(f'<a href="{match.group(0)}" target="_blank" class="btn">{label}</a>')
                if label == "INFORMATION": has_info_link = True

        # Swem Gala / Information to follow Logika
        info_val = str(r.iloc[8]).strip()
        info_box = ""
        if info_val.lower() != 'nan' and info_val != "" and not has_info_link:
            info_box = f'<div class="box"><b>Note:</b><br>{info_val}</div>'

        st.markdown(f"""
        <div class="card">
            <div style="color:#333; font-size:0.85rem;">🗓️ {date_str}</div>
            <div class="t">{sport} {age}</div>
            <div style="color:#333; font-size:0.85rem;">📍 {venue}</div>
            <div class="btn-row">{" ".join(btns)}</div>
            {info_box}
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("No fixtures found.")
