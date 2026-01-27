import streamlit as st
import pandas as pd
import re
from datetime import datetime
import pytz
import requests
import io
import urllib.parse
import streamlit.components.v1.html as html_component
from streamlit_autorefresh import st_autorefresh

# 1. Page Configuration
st.set_page_config(page_title="LMCP Event Hub", layout="centered")
st_autorefresh(interval=120000, key="datarefresh")

# 2. Styling (CSS)
STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700&display=swap');
body { background:#008080; font-family:'Source Sans 3', sans-serif; margin:0; padding:0; }
.navbar { background:white; border-bottom:5px solid #800000; text-align:center; padding:10px 0; }
.navbar img { max-width:100%; max-height:120px; object-fit:contain; }
.header-title { background:#008080; color:white; text-align:center; padding:15px; font-size:1.4rem; font-weight:700; }
.card { background:white; padding:25px; border-radius:22px; border-left:12px solid #800000; margin-bottom:25px; box-shadow:0 6px 18px rgba(0,0,0,0.18); font-family:'Source Sans 3', sans-serif; }
.card-date { color:#666; font-size:0.9rem; margin-bottom: 5px; }
.card-title { color:#800000; font-size:1.5rem; font-weight:700; margin: 5px 0; }
.venue-link { color:#008080; font-weight:600; text-decoration:none; font-size: 0.95rem; }
.team-box { background:#fff3f3; padding:15px; border-radius:12px; margin:15px 0; border:1px dashed #800000; color:#800000; font-size:0.9rem; white-space: pre-wrap; }
.note-box { background:#f8f9fa; padding:15px; border-radius:12px; margin:15px 0; border-left:5px solid #008080; color:#333; font-size:0.9rem; white-space: pre-wrap; }
.btn-row { display:flex; flex-wrap:wrap; gap:10px; margin-top:15px; }
.btn { background:#800000; color:white !important; padding:10px 20px; border-radius:12px; font-weight:600; text-decoration:none; font-size:0.8rem; display:inline-block; }
.prog-container { margin-top:15px; border-top: 1px solid #eee; padding-top:10px; }
.footer { background:#800000; color:white; text-align:center; padding:18px; font-size:0.85rem; margin-top:30px; }
</style>
"""

# 3. Data Logic
URL_DATA = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data():
    try:
        r = requests.get(f"{URL_DATA}&cb={datetime.now().timestamp()}", timeout=10)
        df = pd.read_csv(io.StringIO(r.content.decode('utf-8')))
        def parse_dt(x):
            s = str(x).strip()
            if not s or s.lower() == 'nan': return pd.NaT
            if '202' not in s: s = f"{s} {datetime.now().year}"
            return pd.to_datetime(s, dayfirst=True, errors='coerce')
        df['dt_fixed'] = df.iloc[:, 3].apply(parse_dt)
        return df
    except:
        return pd.DataFrame()

# 4. App UI
st.markdown("<style>[data-testid='stHeader'] {display: none;} .block-container {padding:0 !important;}</style>", unsafe_allow_html=True)
st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", use_container_width=True)

df_raw = load_data()
SA_TIME = pytz.timezone('Africa/Johannesburg')
today = datetime.now(SA_TIME).date()

with
