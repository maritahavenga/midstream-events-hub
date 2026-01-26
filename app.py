import streamlit as st
import pandas as pd
import re
from datetime import datetime
import pytz
import requests
import io
import time
import html
from streamlit_autorefresh import st_autorefresh

# --------------------------------------------------
# Page Config
# --------------------------------------------------
st.set_page_config(page_title="LMCP Live Fixtures", layout="centered")
st_autorefresh(interval=120000, key="datarefresh")

# --------------------------------------------------
# Styling
# --------------------------------------------------
st.markdown("""
<style>
#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
.stApp{background:#008080}.block-container{padding:1rem;max-width:500px}
.card{background:white!important;padding:18px;border-radius:15px;border-left:12px solid #800000;margin-bottom:15px;box-shadow:0 4px 10px rgba(0,0,0,0.2)}
.t{color:#800000!important;font-weight:bold;font-size:1.2rem;margin:5px 0}
.box{background:#f8f9fa;padding:12px;border-radius:10px;margin:10px 0;border-left:5px solid #008080;color:#333;font-size:0.9rem;white-space: pre-wrap;}
.team-box{background:#fff3f3;padding:10px;border-radius:8px;margin:5px 0;border:1px dashed #800000;color:#800000;font-size:0.85rem;white-space: pre-wrap;}
.btn-row {display:flex;gap:6px;flex-wrap:wrap;margin-top:10px}
.btn {background:#800000;color:white!important;font-weight:bold;font-size:0.7rem;padding:10px 14px;border-radius:6px;text-decoration:none}
label { color:white !important; font-weight:bold; }
.stTextInput, .stSelectbox { width: 50% !important; }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# Data Source
# --------------------------------------------------
URL_DATA = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-"
    "YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub"
    "?gid=0&single=true&output=csv"
)

# --------------------------------------------------
# Helpers
# --------------------------------------------------
URL_REGEX = re._
