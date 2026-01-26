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
.stApp{background:#008080}.block-container{padding:1rem;max-width:500px}
.card{background:white!important;padding:18px;border-radius:15px;border-left:12px solid #800000;margin-bottom:15px;box-shadow:0 4px 10px rgba(0,0,0,0.2)}
.t{color:#800000!important;font-weight:bold;font-size:1.15rem;margin:5px 0}
.box{background:#f8f9fa;padding:12px;border-radius:10px;margin:10px 0;border-left:5px solid #008080;color:#333;font-size:0.85rem;}
label { color:white !important; font-weight:bold; }
h2 { color: white !important; text-align: center; text-transform: uppercase;}
.stButton>button { width:100%; background-color:#800000; color:white; border:2px solid #00cccc; border-radius:10px; font-weight:bold;}
</style>
""", unsafe_allow_html=True)

URL_DATA = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?gid=0&single=true&output=csv"

def get_link(val):
    s = str(val).strip()
    if not s or s.lower() == 'nan': return None
    m = re.search(r'(https?://[^\s<>"]+)', s)
    return m.group(0) if m else None

def load_live_data():
    try:
        SA_TIME = pytz.timezone('Africa/Johannesburg')
        now = datetime.now(SA_TIME).date()
        response = requests.get(f"{URL_DATA}&refresh={time.time()}", timeout=10)
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

# Refresh knoppie
if st.button(f"🔄 REFRESH (Update: {update_time.strftime('%H:%M')})"):
    st.cache_data.clear()
    st.rerun()

st.markdown("<h2>Upcoming Fixtures</h2>", unsafe_allow_html=True)

if not df_live.empty:
    # --- STICKY URL LOGIKA ---
    saved_acts = st.query_params.get_all("act")
    
    range_opt = st.radio("View Range:", ["All Upcoming", "Next 7 Days"], horizontal=True)
    cat_opt = st.selectbox("Category:", ["All", "Sport", "Culture", "Academics"])

    all_acts = sorted([str(a) for a in df_live.iloc[:, 1].dropna().unique() if str(a).lower() != 'nan'])
    
    # Gebruik URL as default (Sticky)
    sel_acts = st.multiselect("Activity:", all_acts, default=saved_acts if (saved_acts and all(a in all_acts for a in saved_acts)) else None)
    
    # Update URL onmiddellik
    st.query_params["act"] = sel_acts

    # Filter Logika
    f_df = df_live
    if range_opt == "Next 7 Days":
        f_df = f_df[f_df['dt_fixed'].dt.date <= (today_date + timedelta(days=7))]
    if cat_opt != "All":
        f_df = f_df[f_df.iloc[:, 0].str.contains(cat_opt, case=False, na=False)]
    if sel_acts:
        f_df = f_df[f_df.iloc[:, 1].astype(str).isin(sel_acts)]

    # DISPLAY
    for i, r in f_df.iterrows():
        st.markdown(f"""
        <div class="card">
            <div style="color:#333; font-size:0.85rem;">🗓️ {r['dt_fixed'].strftime('%d %B %Y')}</div>
            <div class="t">{r.iloc[1]} {str(r.iloc[2]) if str(r.iloc[2]).lower() != 'nan' else ''}</div>
            <div style="color:#333; font-size:0.85rem;">📍 {r.iloc[4]}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # BUTTONS (F, G, H, I)
        btn_cols = st.columns(4)
        button_names = ["PROGRAMME", "TEAM", "CONFIRM", "INFORMATION"]
        
        for idx, label in enumerate(button_names):
            link = get_link(r.iloc[5+idx])
            if link:
                with btn_cols[idx]:
                    st.link_button(label, link, use_container_width=True)
        
        # Note (As dit nie 'n link is nie)
        note = str(r.iloc[8]).strip()
        if note.lower() != 'nan' and not get_link(note):
            st.markdown(f'<div class="box"><b>Note:</b><br>{note}</div>', unsafe_allow_html=True)
else:
    st.info("No fixtures found.")
