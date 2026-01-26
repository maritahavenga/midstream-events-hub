import streamlit as st
st.set_page_config(page_title="LMCP Event Hub", layout="centered")

# --------------------------------------------------
# IMPORTS
# --------------------------------------------------
import streamlit.components.v1 as components
import pandas as pd
import re
from datetime import datetime, timedelta
import requests, io, time, urllib.parse

# --------------------------------------------------
# AUTORELOAD EVERY 2 MINUTES
# --------------------------------------------------
from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=120000, key="refresh")

today = datetime.now().date()

# --------------------------------------------------
# STYLES, NAVBAR, FULL-WIDTH LOGO, GREEN HEADER
# --------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700&display=swap');

#MainMenu, footer, header {visibility:hidden;}
.stApp {background:#008080;}
.block-container {max-width:650px; padding-top:100px;}

/* Navbar + full width logo */
.navbar {
    position:fixed;
    top:0; left:0; right:0;
    background:white;
    border-bottom:3px solid #800000;
    z-index:9999;
    text-align:center;
}
.navbar img {
    width:100%;
    max-height:120px;
    object-fit:contain;
}

/* Green header strip under logo */
.green-header {
    background:#008080;
    color:white;
    text-align:center;
    padding:14px 10px;
    font-family:'Source Sans 3', sans-serif;
    font-weight:700;
    font-size:1.25rem;
}

/* Filter panel */
.filter-box {
    background:white;
    padding:18px;
    border-radius:18px;
    box-shadow:0 6px 14px rgba(0,0,0,0.18);
    margin-bottom:40px;
}

label {color:#333 !important; font-weight:600;}

/* Streamlit input fields */
.stTextInput>div>div>input,
.stSelectbox>div>div>div>div,
.stMultiSelect>div>div>div {
    background:white;
    border:2px solid #800000;
    border-radius:8px;
    padding:6px 10px;
    color:#333;
}
.stTextInput>div>div>input:focus,
.stSelectbox>div>div>div>div:focus,
.stMultiSelect>div>div>div:focus {
    outline:none;
    border-color:#800000;
    box-shadow:0 0 0 2px rgba(128,0,0,0.2);
}
</style>

<div class="navbar">
    <img src="https://midstream-primary.co.za/wp-content/uploads/2021/09/MCP-1.png">
</div>
<div class="green-header">
    Laerskool Midstream College Primary — Event Hub
</div>
""", unsafe_allow_html=True)

# --------------------------------------------------
# CARD STYLE
# --------------------------------------------------
CARD_STYLE = """
<style>
.card {
    background:white;
    padding:28px;
    border-radius:20px;
    border-left:12px solid #800000;
    margin-bottom:40px;
    box-shadow:0 8px 18px rgba(0,0,0,0.18);
    font-family:'Source Sans 3', sans-serif;
    font-size:1rem;
}

.card-date {
    font-size:0.9rem;
    color:#555;
    margin-bottom:6px;
}

.card-title {
    color:#800000;
    font-weight:700;
    font-size:1.25rem;
    margin-bottom:6px;
}

.venue a {
    text-decoration:none;
    color:#333;
    font-weight:500;
    cursor:pointer;
}

.venue a:hover {
    text-decoration:underline;
}

.team {
    background:#fff3f3;
    padding:18px;
    border-radius:14px;
    margin-top:16px;
    border:1px dashed #800000;
    font-size:1rem
