import streamlit as st
import pandas as pd
import re
from datetime import datetime
import pytz
import requests
import io
import urllib.parse
from streamlit_autorefresh import st_autorefresh

# 1. Page Configuration
st.set_page_config(page_title="LMCP Event Hub", layout="centered")
st_autorefresh(interval=120000, key="datarefresh")

# 2. Styling (The Look You Love)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700&display=swap');
html, body, .stApp { background:#008080; font-family:'Source Sans 3', sans-serif; }
#MainMenu, footer, header {visibility:hidden;}

/* Fix the Top Banner/Logo Spacing */
.block-container { max-width:820px; padding: 0 !important; margin: 0 auto; }
[data-testid="stHeader"] {display: none;}

.navbar { background:white; border-bottom:5px solid #800000; text-align:center; line-height: 0; }
.navbar img { width:100%; max-height:140px; object-fit:contain; }
.header-title { background:#008080; color:white; text-align:center; padding:15px; font-size:1.4rem; font-weight:700; margin-top:-2px; }

/* Filter Box */
.filter-box { background:white; padding:20px; border-radius:0 0 20px 20px; margin-bottom:20px; box-shadow:0 6px 18px rgba(0,0,0,0.18); }

/* Card Styling */
.card { background:white; padding:25px; border-radius:22px; border-left:12px solid #800000; margin-bottom:25px; box-shadow:0 6px 18px rgba(0,0,0,0.18); text-align: left; }
.card-date { color:#666; font-size:0.9rem; margin-bottom: 5px; }
.card-title { color:#800000; font-size:1.5rem; font-weight:700; margin: 5px 0; line-height: 1.2; }
.venue-link { color:#008080; font-weight:600; text-decoration:none; font-size: 0.95rem; }

/* Team & Note Boxes */
.team-box { background:#fff3f3; padding:15px; border-radius:12px; margin:15px 0; border:1px dashed #800000; color:#800000; font-size:0.9rem; white-space: pre-wrap; }
.note-box { background:#f8f9fa; padding:15px; border-radius:12px; margin:15px 0; border-left:5px solid #008080; color:#333; font-size:0.9rem; white-space: pre-wrap; }

/* Buttons */
.btn-row { display:flex; flex-wrap:wrap; gap:10px; margin-top:15px; }
.btn { background:#800000; color:white !important; padding:10px 20px; border-radius:12px; font-weight:600; text-decoration:none; font-size:0.8rem; display:inline-block; border: none; }
.prog-container { margin-top:15px; border-top: 1px solid #eee; padding-top:10px; }

label { color: #333 !important; font-weight: bold; }
</style>
<div class="navbar"><img src="https://midstream-primary.co.za/wp-content/uploads/2021/09/MCP-1.png"></div>
<div class="header-title">Laerskool Midstream College Primary Event Hub</div>
""", unsafe_allow_html=True)

# 3. Data Loading
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?gid=0&single=true&output=csv"

def load_data():
    try:
        r = requests.get(f"{DATA_URL}&cb={datetime.now().timestamp()}", timeout=10)
        df = pd.read_csv(io.StringIO(r.content.decode('utf-8')))
        def parse_dt(x):
            s = str(x).strip()
            if not s or s.lower() == 'nan': return pd.NaT
            if '202' not in
