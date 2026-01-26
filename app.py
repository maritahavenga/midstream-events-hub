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

# 2. Styling (Die stabiele Midstream-look)
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stApp{background:#008080}.block-container{padding:1rem;max-width:500px}
.card{background:white!important;padding:18px;border-radius:15px;border-left:12px solid #800000;margin-bottom:15px;box-shadow:0 4px 10px rgba(0,0,0,0.2)}
.t{color:#800000!important;font-weight:bold;font-size:1.15rem;margin:5px 0}
.box{background:#f8f9fa;padding:12px;border-radius:10px;margin:10px 0;border-left:5px solid #008080;color:#333;font-size:0.85rem;}
.btn-row {display:flex!important; gap:4px!important; justify-content:space-between!important; margin-top:10px!important; width:100%!important; flex-wrap: wrap;}
.btn { flex:1 1 auto!important; background:#800000!important; color:white!important; text-align:center!important; text-decoration:none!important; font-weight:bold!important; font-size:0.65rem!important; padding:10px 5px!important; border-radius:6px!important; display:block!important; border:1px solid #00cccc!important; margin-bottom:4px;}
label { color:white !important; font-weight:bold; }
h2 { color: white !important; text-align: center; text-transform: uppercase;}
.stButton>button { width:100%; background-color:#800000; color:white; border:2px solid #00cccc; border-radius:10px; font-weight:bold;}
</style>
""", unsafe_allow_html=True)

URL_DATA = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?gid=0&single=true&output=csv"

def load_live_data():
    try:
        SA_TIME = pytz.timezone('Africa/Johannesburg')
        now = datetime.now(SA_TIME).date()
        past_limit = now - timedelta(days=10) # Laat Results toe
        
        response = requests.get(f"{URL_DATA}&refresh={time.time()}", timeout=10)
        df = pd.read_csv(io.StringIO(response.text))
        
        def parse_dt(x):
            s = str(x).strip()
            if not s or s.lower() == 'nan': return pd.NaT
            if '202' not in s: s = f"{s} 2026"
            return pd.to_datetime(s, dayfirst=True, errors='coerce')
        
        df['dt_fixed'] = df.iloc[:, 3].apply(parse_dt)
        return df[df['dt_fixed'].dt.date >= past_limit].sort_values(by='dt_fixed'), now, datetime.now(SA_TIME)
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
    # --- ALLE FILTERS IS TERUG ---
    url_acts = st.query_params.get_all("act")
    
    view_range = st.radio("View Range:", ["All Upcoming", "Next 7 Days"], horizontal=True)
    category = st.selectbox("Category:", ["All", "Sport", "Culture", "Academics"])

    all_acts = sorted([str(a) for a in df_live.iloc[:, 1].dropna().unique() if str(a).lower() != 'nan'])
    sel_acts = st.multiselect("Activity:", all_acts, default=url_acts if (url_acts and all(a in all_acts for a in url_acts)) else None)
    
    # Update URL vir Sticky Filters
    st.query_params["act"] = sel_acts

    # Filter Logika
    f_df = df_live
    if view_range == "Next 7 Days":
        f_df = f_df[f_df['dt_fixed'].dt.date <= (today_date + timedelta(days=7))]
    if category != "All":
        f_df = f_df[f_df.iloc[:, 0].str.contains(category, case=False, na=False)]
    if sel_acts:
        f_df = f_df[f_df.iloc[:, 1].astype(str).isin(sel_acts)]

    for i, r in f_df.iterrows():
        act, age = str(r.iloc[1]), (str(r.iloc[2]) if str(r.iloc[2]).lower() != 'nan' else "")
        ven = str(r.iloc[4])
        dat = r['dt_fixed'].strftime('%d %B %Y') if pd.notnull(r['dt_fixed']) else "TBA"
        
        # Detective Logika vir links in kolomme 5, 6, 7 en 8
        found_btns = []
        for idx, label in [(5, "PROGRAMME"), (6, "TEAM"), (7, "CONFIRM"), (8, "INFORMATION")]:
            val = str(r.iloc[idx]).strip()
            match = re.search(r'(https?://[^\s<>"]+)', val)
            if match:
                found_btns.append(f'<a href="{match.group(0)}" target="_blank" class="btn">{label}</a>')

        st.markdown(f"""
        <div class="card">
            <div style="color:#333; font-size:0.85rem;">🗓️ {dat}</div>
            <div class="t">{act} {age}</div>
            <div style="color:#333; font-size:0.85rem;">📍 {ven}</div>
            <div class="btn-row">
                {"".join(found_btns)}
            </div>
            {f'<div class="box"><b>Note:</b><br>{r.iloc[8]}</div>' if (str(r.iloc[8]).lower()!='nan' and "http" not in str(r.iloc[8])) else ""}
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("No fixtures found.")
