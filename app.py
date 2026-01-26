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
h2 { color: white !important; text-align: center; margin-top: 5px; text-transform: uppercase; letter-spacing: 1px;}
div[data-baseweb="select"] > div { background-color:#800000 !important; border:none !important; }
div[data-baseweb="select"] * { color:white !important; }
label { color:white !important; font-weight:bold; }
.stButton>button { width:100%; background-color:#800000; color:white; border:2px solid #00cccc; font-size:0.9rem; border-radius:10px; font-weight:bold; margin-bottom:10px;}
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

# --- REFRESH KNOPPIE HEEL BO ---
if st.button(f"🔄 REFRESH DATA (Last Update: {update_time.strftime('%H:%M')})"):
    st.cache_data.clear()
    st.rerun()

st.markdown("<h2>Upcoming Fixtures</h2>", unsafe_allow_html=True)

if not df_live.empty:
    # 1. RANGE FILTER
    view_opt = st.radio("View Range:", ["All Upcoming", "Next 7 Days"], horizontal=True, key="range_v")
    
    # 2. CATEGORY SELECT
    cat = st.selectbox("Category (Type):", ["All", "Sport", "Culture", "Academics"], key="cat_v")

    # 3. ACTIVITY & AGE MET HARD-CODED DEFAULTS
    c = st.columns([1, 1])
    all_acts = sorted([str(a) for a in df_live.iloc[:, 1].dropna().unique() if str(a).lower() != 'nan'])
    defaults = [a for a in ["Athletics", "Swimming", "Atletiek", "Swem"] if a in all_acts]
    
    with c[0]:
        sel_acts = st.multiselect("Activity:", all_acts, default=defaults, key="act_v")
    with c[1]:
        all_ages = sorted([str(a) for a in df_live.iloc[:, 2].dropna().unique() if str(a).lower() != 'nan'])
        sel_ages = st.multiselect("Age Group:", all_ages, key="age_v")

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

    # 4. Vertoon Kaartjies
    for i, r in f_df.iterrows():
        act = str(r.iloc[1])
        age = str(r.iloc[2]) if str(r.iloc[2]).lower() != 'nan' else ""
        dat = r['dt_fixed'].strftime('%d %B %Y')
        ven = str(r.iloc[4])
        
        # Knoppies Skakels
        p_l, t_l, c_l, i_l = get_link(r.iloc[5]), get_link(r.iloc[6]), get_link(r.iloc[7]), get_link(r.iloc[8])
        note = str(r.iloc[8]).strip()
        
        mu = f"https://www.google.com/maps/search/?api=1&query={up.quote(ven + ' Midstream')}"
        
        btns = ""
        if any([p_l, t_l, c_l, i_l]):
            btns = '<div class="btn-row">'
            if p_l: btns += f'<a href="{p_l}" target="_blank" class="btn">PROGRAMME</a>'
            if t_l: btns += f'<a href="{t_l}" target="_blank" class="btn">TEAM</a>'
            if c_l: btns += f'<a href="{c_l}" target="_blank" class="btn">CONFIRM</a>'
            if i_l: btns += f'<a href="{i_l}" target="_blank" class="btn">INFO</a>'
            btns += '</div>'

        st.markdown(f"""
        <div class="card">
            <div style="font-size:0.85rem;color:#333">🗓️ {dat}</div>
            <div class="t">{act} {age}</div>
            <div style="font-size:0.85rem;color:#333">📍 <a href="{mu}" target="_blank" class="v">{ven}</a></div>
            {f'<div class="box"><b>Note:</b><br>{note}</div>' if (note.lower()!='nan' and not i_l) else ""}
            {btns}
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("No fixtures found.")
