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

# 1. Page Config
st.set_page_config(page_title="Events & Results Hub", layout="centered")
st_autorefresh(interval=120000, key="datarefresh")

# 2. CSS Styling
st.markdown("""<style>
.stApp{background:#008080}.block-container{padding:1rem;max-width:500px}
.stTabs [data-baseweb="tab-list"] {gap: 8px; background-color: #008080;}
.stTabs [data-baseweb="tab"] {
    height: 45px; background-color: #800000; color: white; 
    border-radius: 10px 10px 0px 0px; font-weight: bold; border: 1px solid #00cccc;
}
.stTabs [aria-selected="true"] { background-color: #00cccc !important; color: white !important; }
.card{background:white!important;padding:18px;border-radius:15px;border-left:12px solid #800000;margin-bottom:15px;box-shadow:0 4px 10px rgba(0,0,0,0.2)}
.t{color:#800000!important;font-weight:bold;font-size:1.15rem;margin:5px 0}
.res-box{background:#e6f4ea; padding:10px; border-radius:8px; margin:5px 0; border:1px solid #1e7e34; color: #1e7e34; font-weight:bold; text-align:center;}
.btn-row {display:flex!important; gap:4px!important; justify-content:space-between!important; margin-top:15px!important;}
.btn {
    flex:1!important; background:#800000!important; color:white!important; 
    text-align:center!important; text-decoration:none!important;
    font-weight:bold!important; font-size:0.65rem!important; padding:12px 2px!important;
    border-radius:6px!important; display:block!important;
}
#back-to-top {
    position: fixed; bottom: 90px; right: 20px; background-color: #800000; 
    color: white !important; width: 45px; height: 45px; line-height: 45px; 
    text-align: center; border-radius: 50%; z-index: 99999; border: 2px solid white;
}
</style>
<div id="top"></div>
<a href="#top" id="back-to-top">↑</a>
""", unsafe_allow_html=True)

# --- DATA URLS ---
# Replace the gid=0 for URL_RESULTS with the GID of your new "Results" tab
URL_UPCOMING = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?gid=0&single=true&output=csv"
URL_RESULTS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?gid=REPLACE_WITH_YOUR_RESULTS_GID&single=true&output=csv"

def get_data(url, is_upcoming=True):
    try:
        SA_TIME = pytz.timezone('Africa/Johannesburg')
        now = datetime.now(SA_TIME).date()
        response = requests.get(f"{url}&refresh={int(time.time())}")
        df = pd.read_csv(io.StringIO(response.text))
        def parse_dt(x):
            s = str(x).strip()
            if not s or s.lower() == 'nan': return pd.NaT
            if '202' not in s: s = f"{s} 2026"
            return pd.to_datetime(s, dayfirst=True, errors='coerce')
        df['dt_fixed'] = df.iloc[:, 3].apply(parse_dt)
        
        if is_upcoming:
            # Only show events from today onwards
            df = df[df['dt_fixed'].dt.date >= now].sort_values(by='dt_fixed')
        else:
            # Show events that have already happened
            df = df[df['dt_fixed'].dt.date < now].sort_values(by='dt_fixed', ascending=False)
        return df
    except:
        return pd.DataFrame()

def get_l(val):
    t = str(val).strip()
    m = re.search(r'https?://[^\s<>"]+', t)
    return m.group(0) if m else None

# --- UI LOGIC ---
st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", use_container_width=True)

tab_up, tab_res = st.tabs(["🗓️ UPCOMING", "🏆 PAST RESULTS"])

with tab_up:
    df_up = get_data(URL_UPCOMING, is_upcoming=True)
    search_up = st.text_input("🔍 Search Upcoming:", placeholder="e.g. U13B...")
    # ... logic to display df_up ...

with tab_res:
    df_res = get_data(URL_RESULTS, is_upcoming=False)
    search_res = st.text_input("🔍 Search Results:", placeholder="e.g. Rugby...")
    
    if not df_res.empty:
        if search_res:
            df_res = df_res[df_res.apply(lambda r: search_res.lower() in str(r).lower(), axis=1)]
        
        for _, r in df_res.iterrows():
            res_val = str(r.iloc[8]).strip() if len(r) > 8 else "Result Pending"
            st.markdown(f'''<div class="card">
                <div style="font-size:0.85rem;">🗓️ {r['dt_fixed'].strftime('%d %b %Y')}</div>
                <div class="t">{r.iloc[1]} {r.iloc[2]}</div>
                <div class="res-box">🏆 RESULT: {res_val}</div>
            </div>''', unsafe_allow_html=True)
