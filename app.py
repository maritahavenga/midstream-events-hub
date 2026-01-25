import streamlit as st
import pandas as pd
import urllib.parse as up
import re
from datetime import datetime
import pytz
import requests
import io

st.set_page_config(page_title="Events Hub", layout="centered")

st.markdown("""<style>
.stApp{background:#008080}.block-container{padding:1rem;max-width:500px}
.card{background:white!important;padding:18px;border-radius:15px;border-left:12px solid #800000;margin-bottom:15px;box-shadow:0 4px 10px rgba(0,0,0,0.2)}
.t{color:#800000!important;font-weight:bold;font-size:1.15rem;margin:5px 0}.v{color:#800000!important;font-weight:bold;text-decoration:underline}
.box{background:#f8f9fa;padding:12px;border-radius:10px;margin:10px 0;border-left:5px solid #008080;color:#333;font-size:0.9rem;line-height:1.4}
.team-box{background:#fff3f3;padding:10px;border-radius:8px;margin:5px 0;border:1px dashed #800000;color:#800000;font-size:0.85rem}
.btn-row {display: flex!important; gap: 4px!important; justify-content: space-between!important; margin-top: 15px!important; width: 100%!important;}
.btn {
    flex: 1!important; background: #800000!important; color: white!important; 
    text-align: center!important; text-decoration: none!important;
    font-weight: bold!important; font-size: 0.65rem!important; padding: 12px 2px!important;
    border-radius: 6px!important; display: block!important; white-space: nowrap!important;
}
div[data-baseweb="select"] > div { background-color: #800000 !important; border: none !important; }
div[data-baseweb="select"] * { color: white !important; }
label { color: white !important; font-weight: bold; }
.update-ts { text-align: center; color: white; font-size: 0.7rem; margin-top: 20px; opacity: 0.8; }
.cal-svg { width: 16px; height: 16px; vertical-align: middle; margin-right: 6px; fill: #555; }
</style>""", unsafe_allow_html=True)

CAL_SVG = '<svg class="cal-svg" viewBox="0 0 24 24"><path d="M19,4H18V2H16V4H8V2H6V4H5C3.89,4 3,4.9 3,6V20C3,21.1 3.89,22 5,22H19C20.1,22 21,21.1 21,20V6C21,4.9 20.1,4 19,4M19,20H5V9H19V20M5,7V6H19V7H5Z"/></svg>'

U = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=10) 
def load():
    response = requests.get(U)
    response.encoding = 'utf-8' 
    df = pd.read_csv(io.StringIO(response.text))
    def parse_dt(x):
        s = str(x).strip()
        if not s or s.lower() == 'nan': return pd.NaT
        if '2026' not in s: s = f"{s} 2026"
        return pd.to_datetime(s, dayfirst=True, errors='coerce')
    # Column D is the Date
    df['dt_fixed'] = df.iloc[:, 3].apply(parse_dt)
    return df.sort_values(by='dt_fixed', ascending=True), datetime.now(pytz.timezone('Africa/Johannesburg'))

def get_l(val):
    t = str(val).strip()
    m = re.search(r'https?://[^\s<>"]+', t)
    return m.group(0) if m else None

# State management for persistence
if 'cat_sel' not in st.session_state: st.session_state.cat_sel = "All
