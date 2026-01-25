import streamlit as st
import pandas as pd
import urllib.parse as up

st.set_page_config(page_title="Events Hub", page_icon="🏆", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #008080; }
    .block-container { padding-top: 0rem; max-width: 800px; }
    .card {
        background: white; padding: 20px; border-radius: 15px;
        border-left: 12px solid #800000; margin-bottom: 5px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }
    .t { color: #800000; font-weight: bold; font-size: 1.2rem; }
    .v { color: #800000; font-weight: bold; text-decoration: underline; }
    .stButton button { width: 100%; background: #800000!important; color: white!important; font-weight: bold; height: 3em; }
    /* Style the filter label */
    .stSelectbox label { color: white !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", use_container_width=True)
st.markdown("<h1 style='text-align:center;color:white;'>EVENTS HUB 2026</h1>", unsafe_allow_html=True)

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=15)
def load():
    df = pd.read_csv(URL)
    df.columns = [str(c).strip() for c in df.columns]
    return df

try:
    data = load()
    
    # 1. ADD FILTER AT THE TOP
    categories = ["All", "Sport", "Culture", "Academics"]
    choice = st.selectbox("Filter by Category:", categories)

    # Filter the data based on choice
    if choice != "All":
        df = data[data['Category'].str.contains(choice, case=False, na=False)]
    else:
        df = data

    for i, r in df.iterrows():
        cat = str(r.get('Category','')).lower()
        
        # 2. UPDATED ICONS
        icon = "https://openmoji.org/data/color/svg/1F4DF.svg" # Default
        if "cult" in cat: icon = "https://openmoji.org/data/color/svg/1F3AD.svg" # Masks
        elif "sport" in cat: icon = "https://openmoji.org/data/color/svg/1F45F.svg" # Shoe
        elif "acad" in cat: icon = "https://openmoji.
