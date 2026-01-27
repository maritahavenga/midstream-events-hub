import streamlit as st
st.set_page_config(page_title="LMCP Event Hub", layout="centered")

import pandas as pd
import re
from datetime import datetime, timedelta
import requests, io, urllib.parse

today = datetime.now().date()

# =========================
# STYLES
# =========================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700&display=swap');

html, body, .stApp {
    margin:0;
    padding:0;
    background:#008080;
    font-family:'Source Sans 3', sans-serif;
}

#MainMenu, footer, header {visibility:hidden;}
.block-container {
    max-width:760px;
    padding-top:0 !important;
}

.navbar {
    position:fixed;
    top:0; left:0; right:0;
    background:white;
    border-bottom:4px solid #800000;
    z-index:9999;
}
.navbar img {
    width:100%;
    max-height:130px;
    object-fit:contain;
}

.header-green {
    margin-top:130px;
    background:#008080;
    color:white;
    text-align:center;
    padding:18px;
    font-weight:700;
    font-size:1.35rem;
}

.filter-box {
    background:white;
    padding:22px;
    border-radius:18px;
    margin:28px 0;
    box-shadow:0 4px 14px rgba(0,0,0,0.18);
}

.card {
    background:white;
    padding:34px;
    border-radius:20px;
    border-left:10px solid #800000;
    margin-bottom:40px;
    box-shadow:0 6px 18px rgba(0,0,0,0.18);
}

.card-date {color:#666; font-size:0.9rem;}
.card-title {color:#800000; font-size:1.45rem; font-weight:700;}

.venue a {
    color:#333;
    text-decoration:none;
}
.venue a:hover {text-decoration:underline;}

.team {
    background:#fff3f3;
    padding:16px;
    border-radius:12px;
    margin-top:18px;
    font-size:0.95rem;
}

.btn-row {
    display:flex;
    flex-wrap:wrap;
    gap:14px;
    margin-top:22px;
}
.btn {
    background:#800000;
    color:white;
    padding:12px 26px;
    border-radius:14px;
    font-weight:600;
    text-decoration:none;
}
.btn:hover {opacity:0.9;}
</style>

<div class="navbar">
    <img src="https://midstream-primary.co.za/wp-content/uploads/2021/09/MCP-1.png">
</div>

<div class="header-green">
Laerskool Midstream College Primary — Event Hub
</div>
""", unsafe_allow_html=True)

# =========================
# DATA
# =========================
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?gid=0&single=true&output=csv"
URL_REGEX = re.compile(r"(https?://[^\s<>\"']+)")

@st.cache_data(ttl=120)
def load_data():
    r = requests.get(DATA_URL, timeout=10)
    df = pd.read_csv(io.StringIO(r.text))
    df.columns = [c.strip().lower() for c in df.columns]

    def parse_dat_
