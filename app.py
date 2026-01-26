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
.t{color:#800000!important;font-weight:bold;font-size:1.15rem;margin:5px 0}
.box{background:#f8f9fa;padding:12px;border-radius:10px;margin:10px 0;border-left:5px solid #008080;color:#333;font-size:0.9rem;white-space: pre-wrap;}
.btn-row {display: flex !important; flex-wrap: wrap !important; gap: 6px !important; margin-top: 10px !important; width: 100% !important;}
.btn {flex: 1 1 auto !important; background: #800000 !important; color: white !important; text-align: center !important; text-decoration: none !important; font-weight: bold !important; font-size: 0.7rem !important; padding: 10px 5px !important; border-radius: 6px !important; min-width: 80px !important; display: inline-block !important; border: 1px solid #00cccc !important;}
h2 { color: white !important; text-align: center; margin-top: 10px; text-transform: uppercase; letter-spacing: 1px;}
div[data-baseweb="select"] > div { background-color:#800000 !important; border:none !important; }
div[data-baseweb="select"] * { color:white !important; }
label { color:white !important; font-weight:bold; }
.stButton>button { width:100%; background-color:#800000; color:white; border:2px solid #00cccc; font-size:0.9rem; border-radius:10px; font-weight:bold;}
</style>
""", unsafe_allow_html=True)

URL_DATA = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?gid=0&single=true&output=csv"

def get_l(val):
    t = str(val).strip()
    m = re.search(r'https?://[^\s<>"]+', t)
    return m.group(0) if m else None

def load_live_data():
    try:
        SA_TIME = pytz.timezone('Africa/Johannesburg')
        now = datetime.now(SA_TIME).date()
        response = requests.get(f"{URL_DATA}&refresh={int(time.time())}", timeout=10)
        df = pd.read_csv(io.StringIO(response.text))
        df = df.dropna(subset=[df.columns[1], df.columns[3]]) 
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

if not df_live.empty:
    # 1. 7-Day Toggle
    view_opt = st.radio("View Range:", ["All Upcoming", "Next 7 Days"], horizontal=True, key="range_sel")
    
    # 2. Category Select
    cat = st.selectbox("Category (Type):", ["All", "Sport", "Culture", "Academics"], key="type_sel")

    # 3. Multiselects met "Hard-coded" Defaults
    c = st.columns([1, 1])
    all_acts = sorted([str(a) for a in df_live.iloc[:, 1].dropna().unique() if str(a).lower() != 'nan'])
    perma_filters = ["Swimming", "Athletics", "Swem", "Atletiek"]
    default_selection = [a for a in perma_filters if a in all_acts]
    
    with c[0]:
        sel_acts = st.multiselect("Activity:", all_acts, default=default_selection, key="act_sel")
    with c[1]:
        all_ages = sorted([str(a) for a in df_live.iloc[:, 2].dropna().unique() if str(a).lower() != 'nan'])
        sel_ages = st.multiselect("Age Group:", all_ages, key="age_sel")

    # Filter Logika
    f_df = df_live
    if view_opt == "Next 7 Days":
        f_df = f_df[f_df['dt_fixed'].dt.date <= (today_date + timedelta(days=7))]
    if cat != "All":
        f_df = f_df[f_df.iloc[:, 0].str.contains(cat, case=False, na=False)]
    if sel_acts:
        f_df = f_df[f_df.iloc[:, 1].astype(str).isin(sel_acts)]
    if sel_ages:
        f_df = f_df[f_df.iloc[:, 2].astype(str).isin(sel_ages)]

    # Vertoon Kaartjies
    for i, r in f_df.iterrows():
        act_name = str(r.iloc[1])
        age_name = str(r.iloc[2]) if str(r.iloc[2]).lower() != 'nan' else ""
        dat = r['dt_fixed'].strftime('%d %B %Y')
        ven = str(r.iloc[4])
        
        # Knoppies
        prog_l = get_l(r.iloc[5])
        team_l = get_l(r.iloc[6])
        conf_l = get_l(r.iloc[7])
        info_l = get_l(r.iloc[8])
        info_text = str(r.iloc[8]).strip()
        
        mu = f"https://www.google.com/maps/search/?api=1&query={up.quote(ven + ' Midstream')}"
        
        # HTML bou vir knoppies
        btns_html = ""
        if any([prog_l, team_l, conf_l, info_l]):
            btns_html = '<div class="btn-row">'
            if prog_l: btns_html += f'<a href="{prog_l}" target="_blank" class="btn">PROGRAMME</a>'
            if team_l: btns_html += f'<a href="{team_l}" target="_blank" class="btn">TEAM</a>'
            if conf_l: btns_html += f'<a href="{conf_l}" target="_blank" class="btn">CONFIRM</a>'
            if info_l: btns_html += f'<a href="{info_l}" target="_blank" class="btn">INFO</a>'
            btns_html += '</div>'

        st.markdown(f"""
        <div class="card">
            <div style="font-size:0.85rem;color:#333">🗓️ {dat}</div>
            <div class="t">{act_name} {age_name}</div>
            <div style="font-size:0.85rem;color:#333">📍 <a href="{mu}" target="_blank" class="v">{ven}</a></div>
            {f'<div class="box"><b>Note:</b><br>{info_text}</div>' if (info_text.lower()!='nan' and not info_l) else ""}
            {btns_html}
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("Geen fixtures gevind nie.")
