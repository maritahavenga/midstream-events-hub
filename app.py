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

# 2. Styling (Skoon Midstream Look)
st.markdown("""
<style>
#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
.stApp{background:#008080}.block-container{padding:1rem;max-width:500px}
.stTabs [data-baseweb="tab-list"] {gap: 8px; background-color: #008080; justify-content: center;}
.stTabs [data-baseweb="tab"] { height: 45px; background-color: #800000; color: white; border-radius: 10px 10px 0px 0px; font-weight: bold; border: 1px solid #00cccc;}
.stTabs [aria-selected="true"] { background-color: #00cccc !important; }
.card{background:white!important;padding:18px;border-radius:15px;border-left:12px solid #800000;margin-bottom:15px;box-shadow:0 4px 10px rgba(0,0,0,0.2)}
.t{color:#800000!important;font-weight:bold;font-size:1.15rem;margin:5px 0}
.box{background:#f8f9fa;padding:12px;border-radius:10px;margin:10px 0;border-left:5px solid #008080;color:#333;font-size:0.9rem;white-space: pre-wrap;}
.team-box{background:#fff3f3;padding:10px;border-radius:8px;margin:5px 0;border:1px dashed #800000;color:#800000;font-size:0.85rem;white-space: pre-wrap;}
.btn-row {display:flex !important; gap:4px !important; justify-content:space-between !important; margin-top:10px !important; width:100% !important; flex-wrap: wrap !important;}
.btn { flex:1 1 auto !important; background:#800000 !important; color:white !important; text-align:center !important; text-decoration:none !important; font-weight:bold !important; font-size:0.65rem !important; padding:10px 5px !important; border-radius:6px !important; display:block !important; border:none !important; margin-bottom:5px !important;}
label { color:white !important; font-weight:bold; }
h2 { color: white !important; text-align: center; text-transform: uppercase; }
.stButton>button { width:100%; background-color:#800000; color:white; border:2px solid #00cccc; border-radius:10px; font-weight:bold;}
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

tab_up, tab_res = st.tabs(["🗓️ UPCOMING", "🏆 RESULTS"])

with tab_up:
    st.markdown("<h2>Upcoming Fixtures</h2>", unsafe_allow_html=True)
    if not df.empty:
        f_df = df[df['dt_fixed'].dt.date >= today].sort_values(by='dt_fixed')
        
        search_q = st.text_input("🔍 Search (e.g. u13 hockey):", key="q_up").lower()
        if search_q:
            f_df = f_df[f_df.apply(lambda r: search_q in str(r.values).lower(), axis=1)]

        for _, r in f_df.iterrows():
            # Kolomme: 1=Act, 2=Age, 4=Venue
            sport = str(r.iloc[1])
            age = str(r.iloc[2]) if str(r.iloc[2]).lower() != 'nan' else ""
            date_str = r['dt_fixed'].strftime('%d %B %Y') if pd.notnull(r['dt_fixed']) else "TBA"
            venue = str(r.iloc[4])
            
            btns = []
            team_t = ""
            note_t = ""
            # Kolomme: 5=Prog, 6=Team, 7=Conf, 8=Info
            for idx, lbl in [(5, "PROGRAMME"), (6, "TEAM"), (7, "CONFIRM"), (8, "INFORMATION")]:
                val = str(r.iloc[idx]).strip()
                if val.lower() == 'nan' or not val: continue
                link = re.search(r'(https?://[^\s<>"]+)', val)
                if link:
                    btns.append(f'<a href="{link.group(0)}" target="_blank" class="btn">{lbl}</a>')
                else:
                    if lbl == "TEAM": team_t = val
                    elif lbl == "INFORMATION": note_t = val

            btn_html = f'<div class="btn-row">{"".join(btns)}</div>' if btns else ""
            tm_html = f'<div class="team-box"><b>TEAMS:</b><br>{team_t}</div>' if team_t else ""
            nt_html = f'<div class="box"><b>Note:</b><br>{note_t}</div>' if note_t else ""

            st.markdown(f"""
            <div class="card">
                <div style="font-size:0.85rem;color:#333">🗓️ {date_str}</div>
                <div class="t">{sport} {age}</div>
                <div style="font-size:0.85rem;color:#333">📍 {venue}</div>
                {tm_html}
                {btn_html}
                {nt_html}
            </div>
            """, unsafe_allow_html=True)

with tab_res:
    st.markdown("<h2>Match Results</h2>", unsafe_allow_html=True)
    if not df.empty:
        r_df = df[df['dt_fixed'].dt.date < today].sort_values(by='dt_fixed', ascending=False)
        for _, r in r_df.iterrows():
            res_val = str(r.iloc[9]).strip() if len(r) > 9 else ""
            res_link = re.search(r'(https?://[^\s<>"]+)', res_val)
            date_res = r['dt_fixed'].strftime('%d %b %Y')
            title_res = f"{r.iloc[1]} {str(r.iloc[2]) if str(r.iloc[2]).lower() != 'nan' else ''}"
            
            if res_link:
                res_disp = f'<div class="btn-row"><a href="{res_link.group(0)}" target="_blank" class="btn" style="background:#1e7e34!important;">🏆 VIEW RESULTS</a></div>'
            else:
                res_disp = f'<div class="res-box" style="background:#e6f4ea; padding:10px; border-radius:8px; border:1px solid #1e7e34; color:#1e7e34; font-weight:bold; text-align:center; margin-top:10px;">🏆 RESULT: {res_val if res_val.lower() != "nan" else "Pending"}</div>'
            
            st.markdown(f"""
            <div class="card">
                <div style="font-size:0.85rem; color:#666;">🗓️ {date_res} | 📍 {r.iloc[4]}</div>
                <div class="t">{title_res}</div>
                {res_disp}
            </div>
            """, unsafe_allow_html=True)
