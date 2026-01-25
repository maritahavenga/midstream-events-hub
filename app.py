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
st.set_page_config(page_title="LMCP Events & Results", layout="centered")
st_autorefresh(interval=120000, key="datarefresh")

# 2. Styling
st.markdown("""<style>
.stApp{background:#008080}.block-container{padding:1rem;max-width:500px}
.stTabs [data-baseweb="tab-list"] {gap: 8px; background-color: #008080; justify-content: center;}
.stTabs [data-baseweb="tab"] { height: 45px; background-color: #800000; color: white; border-radius: 10px 10px 0px 0px; font-weight: bold; border: 1px solid #00cccc;}
.stTabs [aria-selected="true"] { background-color: #00cccc !important; }
.card{background:white!important;padding:18px;border-radius:15px;border-left:12px solid #800000;margin-bottom:15px;box-shadow:0 4px 10px rgba(0,0,0,0.2)}
.t{color:#800000!important;font-weight:bold;font-size:1.15rem;margin:5px 0}.v{color:#800000!important;font-weight:bold;text-decoration:underline}
.box{background:#f8f9fa;padding:12px;border-radius:10px;margin:10px 0;border-left:5px solid #008080;color:#333;font-size:0.9rem;line-height:1.4}
.team-box{background:#fff3f3;padding:10px;border-radius:8px;margin:5px 0;border:1px dashed #800000;color:#800000;font-size:0.85rem}
.res-box{background:#e6f4ea; padding:10px; border-radius:8px; margin:5px 0; border:1px solid #1e7e34; color: #1e7e34; font-weight:bold; text-align:center;}
.btn-row {display:flex!important; gap:4px!important; justify-content:space-between!important; margin-top:15px!important; width:100%!important;}
.btn { flex:1!important; background:#800000!important; color:white!important; text-align:center!important; text-decoration:none!important; font-weight:bold!important; font-size:0.65rem!important; padding:12px 2px!important; border-radius:6px!important; display:block!important; white-space:nowrap!important;}
#back-to-top { position: fixed; bottom: 90px; right: 20px; background-color: #800000; color: white !important; width: 45px; height: 45px; line-height: 45px; text-align: center; border-radius: 50%; z-index: 99999; border: 2px solid white; }
div[data-baseweb="select"] > div { background-color:#800000 !important; border:none !important; }
div[data-baseweb="select"] * { color:white !important; }
label { color:white !important; font-weight:bold; }
.stButton>button { width:100%; background-color:#800000; color:white; border:2px solid #00cccc; font-size:0.9rem; border-radius:10px; height:45px; font-weight:bold; margin-bottom:10px;}
</style>
<div id="top"></div>
<a href="#top" id="back-to-top">↑</a>
""", unsafe_allow_html=True)

URL_DATA = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?gid=0&single=true&output=csv"

def load_all_data():
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
        return df, now, datetime.now(SA_TIME)
    except:
        return pd.DataFrame(), datetime.now().date(), datetime.now()

def get_l(val):
    t = str(val).strip()
    m = re.search(r'https?://[^\s<>"]+', t)
    return m.group(0) if m else None

st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", use_container_width=True)
df_all, today_date, update_time = load_all_data()

tab_up, tab_res = st.tabs(["🗓️ UPCOMING", "🏆 RESULTS"])

with tab_up:
    if not df_all.empty:
        df_up = df_all[df_all['dt_fixed'].dt.date >= today_date].sort_values(by='dt_fixed')
        if st.button(f"🔄 REFRESH (Update: {update_time.strftime('%H:%M')})", key="ref_up"):
            st.cache_data.clear()
            st.rerun()

        raw_search = st.text_input("🔍 Search Upcoming:", placeholder="U13B, Hockey...", key="search_up")
        s = raw_search.lower().replace(" ","")
        
        if not df_up.empty:
            if s: df_up = df_up[df_up.apply(lambda r: s in str(r).lower().replace(" ",""), axis=1)]
            for _, r in df_up.iterrows():
                age_val = str(r.iloc[2]).strip()
                display_title = f"{r.iloc[1]} {age_val}" if age_val != 'nan' else str(r.iloc[1])
                ven = str(r.iloc[4])
                dat = r['dt_fixed'].strftime('%d %B %Y') if pd.notnull(r['dt_fixed']) else "TBA"
                
                prog_l, team_val = get_l(r.iloc[5]), str(r.iloc[6]).strip()
                team_l, conf_l = get_l(team_val), get_l(r.iloc[7])
                info_val, info_l = str(r.iloc[8]).strip(), get_l(str(r.iloc[8]))
                mu = f"https://www.google.com/maps/search/?api=1&query={up.quote(ven + ' Midstream')}"
                
                bx = f'<div class="box"><b>Note:</b> {info_val}</div>' if (info_val and info_val.lower()!='nan' and not info_l) else ""
                tm_bx = f'<div class="team-box"><b>Team Info:</b> {team_val}</div>' if (team_val and team_val.lower()!='nan' and not team_l) else ""

                btns = '<div class="btn-row">'
                if prog_l: btns += f'<a href="{prog_l}" target="_blank" class="btn">PROGRAMME</a>'
                if team_l: btns += f'<a href="{team_l}" target="_blank" class="btn
