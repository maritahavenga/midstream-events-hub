import streamlit as st
import pandas as pd
import urllib.parse as up

st.set_page_config(page_title="Events Hub", page_icon="🏆", layout="wide")

# Updated CSS to make the banner and container wider
st.markdown("""
    <style>
    .stApp { background-color: #008080; }
    /* This removes the extra padding at the top and sides */
    .block-container { padding-top: 0rem; padding-bottom: 0rem; max-width: 800px; }
    .card {
        background: white; padding: 20px; border-radius: 15px;
        border-left: 12px solid #800000; margin-bottom: 5px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }
    .t { color: #800000; font-weight: bold; font-size: 1.2rem; }
    .v { color: #800000; font-weight: bold; text-decoration: underline; }
    .stButton button { width: 100%; background: #800000!important; color: white!important; font-weight: bold; height: 3em; }
    /* Makes the logo image rounded and look like a proper banner */
    img { border-radius: 0px 0px 15px 15px; }
    </style>
    """, unsafe_allow_html=True)

# The Banner - now using full container width
st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", use_container_width=True)
st.markdown("<h1 style='text-align:center;color:white;margin-top:10px;'>EVENTS HUB 2026</h1>", unsafe_allow_html=True)

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=15)
def load():
    df = pd.read_csv(URL)
    df.columns = [str(c).strip() for c in df.columns]
    return df

try:
    df
