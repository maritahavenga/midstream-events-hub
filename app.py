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

# 2. Styling (Maroon & Teal)
st.markdown("""
<style>
#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
.stApp{background:#008080}.block-container{padding:1rem;max-width:500px}
.card{background:white!important;padding:18px;border-radius:15px;border-left:12px solid #800000;margin-bottom:15px;box-shadow:0 4px 10px rgba(0,0,0,0.2)}
.t{color:#800000!important;font-weight:bold;font-size:1.2rem;margin:5px 0}
.box{background:#f8f9fa;padding:12px;border-radius:10px;margin:10px 0;border-left:5px solid #008080;color:#333;font-size:0.9rem;line-height:1.4;white-space: pre-wrap;}
.team-box{background:#fff3f3;padding:10px;border-radius:8px;margin:5px 0;border:1px dashed #800000;color:#800000;font-size:0.85rem;white-space: pre-wrap;}
.btn-row {display: flex; gap: 6px; justify-content: flex-start; margin-top: 10px; flex-wrap: wrap;}
.btn {background: #800000; color: white !important; text-align: center; text-decoration: none; font-weight: bold; font-size: 0.7rem; padding: 10px 14px; border-radius: 6px; display: inline-block; border: none; margin-bottom: 5px;}
.prog-btn-container {margin-top: 15px; border-top: 1px solid #eee; padding-top: 10px;}
label { color:white !important; font-weight:bold; }
.stButton>button { width:100%; background-color:#800000; color:white; border:2px solid #00cccc; border-radius:10px; font-weight:bold; height: 45px;}
</style>
""", unsafe_allow_html=True)

URL_DATA = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?gid=0&single=true&output=csv"

def load_data():
    try:
        SA_TIME = pytz.timezone('Africa/Johannesburg')
        now = datetime.now(SA_TIME).date()
        response = requests.get(f"{URL_DATA}&cb={int(time.time())}", timeout=10)
        df = pd.read_csv(io.StringIO(response.content.decode('utf-8')))
        def parse_dt(x):
            s = str(x).strip()
            if not s or s.lower() == 'nan': return pd.NaT
            if '202' not in s: s = f"{s} 2026"
            return pd.to_datetime(s, dayfirst=True, errors='coerce')
        df['dt_fixed'] = df.iloc[:, 3].apply(parse_dt)
        return df, now, datetime.now(SA_TIME)
    except:
        return pd.DataFrame(), datetime.now().date(), datetime.now()

st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", use_container_width=True)
df, today, up_time = load_data()

# 3. REFRESH & FILTERS
if st.button(f"🔄 REFRESH DATA (Updated: {up_time.strftime('%H:%M')})"):
    st.cache_data.clear()
    st.rerun()

if not df.empty:
    c1, c2 = st.columns(2)
    with c1:
        view_range = st.radio("Show:", ["Upcoming", "Results"], horizontal=True)
    with c2:
        cat_filter = st.selectbox("Category:", ["All", "Sport", "Culture", "Academics"])

    if view_range == "Upcoming":
        f_df = df[df['dt_fixed'].dt.date >= today].sort_values(by='dt_fixed')
    else:
        f_df = df[df['dt_fixed'].dt.date < today].sort_values(by='dt_fixed', ascending=False)

    if cat_filter != "All":
        f_df = f_df[f_df.iloc[:, 0].str.contains(cat_filter, case=False, na=False)]

    search_q = st.text_input("🔍 Search Activity or Age (e.g. u13 hockey):").lower()
    if search_q:
        f_df = f_df[f_df.apply(lambda r: search_q in str(r.values).lower(), axis=1)]

    # 4. Wys die Kaarte
    for _, r in f_df.iterrows():
        sport = str(r.iloc[1])
        # Age Group Brute Force
        age_raw = str(r.iloc[2]).strip()
        age = age_raw if (age_raw.lower() != 'nan' and age_raw != "") else ""
        
        date_str = r['dt_fixed'].strftime('%d %B %Y') if pd.notnull(r['dt_fixed']) else "TBA"
        venue = str(r.iloc[4])
        
        other_btns = ""
        prog_btn = ""
        team_html = ""
        info_html = ""
        
        # Kolomme: 5=Prog, 6=Team, 7=Conf, 8=Info
        for idx, lbl in [(5, "PROGRAMME"), (6, "TEAM"), (7, "CONFIRM"), (8, "INFORMATION")]:
            val = str(r.iloc[idx]).strip()
            if val.lower() == 'nan' or not val: continue
            
            link = re.search(r'(https?://[^\s<>"]+)', val)
            if link:
                btn_tag = f'<a href="{link.group(0)}" target="_blank" class="btn">{lbl}</a>'
                if lbl == "PROGRAMME":
                    prog_btn = btn_tag
                else:
                    other_btns += btn_tag
            else:
                if lbl == "TEAM":
                    team_html = f'<div class="team-box"><b>TEAMS:</b><br>{val}</div>'
                elif lbl == "INFORMATION":
                    info_html = f'<div class="box"><b>Note:</b><br>{val}</div>'

        st.markdown(f"""
        <div class="card">
            <div style="font-size:0.85rem;color:#333">🗓️ {date_str}</div>
            <div class="t">{sport} {age}</div>
            <div style="font-size:0.85rem;color:#333">📍 {venue}</div>
            {team_html}
            <div class="btn-row">{other_btns}</div>
            {info_html}
            {f'<div class="prog-btn-container"><div class="btn-row">{prog_btn}</div></div>' if prog_btn else ""}
        </div>
        """, unsafe_allow_html=True)
else:
    st.error("No connection to data.")
