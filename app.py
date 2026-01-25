import streamlit as st
import pandas as pd
import urllib.parse

# 1. Page Configuration
st.set_page_config(page_title="Midstream Events Hub", page_icon="🏆", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #008080; }
    .event-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        border-left: 12px solid #800000;
        margin-bottom: 5px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }
    .event-title { color: #800000; font-weight: bold; font-size: 1.3rem; margin-bottom: 2px; }
    .event-date { color: #555; font-weight: bold; font-size: 1rem; }
    .venue-link { 
        color: #800000 !important; 
        text-decoration: underline; 
        font-weight: bold;
        font-size: 1rem;
    }
    .stButton button { width: 100%; background-color: #800000 !important; color: white !important; border-radius: 8px; font-weight: bold; height: 3.2em; }
    </style>
    """, unsafe_allow_html=True)

# 2. Logo and Title
col_l, col_m, col_r = st.columns([1, 2, 1])
with col_m:
    st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", use_container_width=True)
st.markdown("<h1 style='text-align: center; color: white;'>EVENTS HUB 2026</h1>", unsafe_allow_html=True)

# 3. Data Connection
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=15)
def load_data():
    df = pd.read_csv(SHEET_URL)
    df.columns = [str(c).strip() for c in df.columns]
    return df

# Start of the data processing block
try:
    df = load_data()
    for index, row in df.iterrows():
        # Category Icons
        cat = str(row.get('Category', '')).lower()
        icon = "https://cdn-icons-png.flaticon.com/512/3163/3163635.png"
        if "cult" in cat: 
            icon = "https://cdn-icons-png.flaticon.com/512/3163/3163732.png"

        # Map Link Logic
        venue = str(row.get('Venue', 'TBA'))
        clean_venue = urllib.parse.quote(venue + " South Africa")
        map_url = f"https://www.google.com/maps/search/?api=1&query={clean_venue}"

        # Display Card
        st.markdown(f"""
            <div class="event-card">
                <img src="{icon}" width="45" style="float: right; opacity: 0.8;">
                <div class="event-date">📅 {row.get('Date', 'TBA')}</div>
                <div class="event-title">{row.get('Event', 'Event')}</div>
                <div style="margin-top:10px; color:#333;">📍 Venue: 
                    <a href="{map_url}" target="_blank" class="venue-link">{venue}</a>
                </div>
                <p style="font-size:0.8rem; color:#666;">(Tap venue name for GPS directions)</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Action Buttons
        c1, c2, c3 = st.columns(3)
        
        p_col = [c for c in df.columns if 'Program' in c]
        if p_col and pd.notna(row.get(p_col[0])) and str(row.get(p_col[0])).startswith('http'):
            with c1: st.link_button("📜 Program", str(row.get(p_col[0])))
        
        t_col = [c for c in df.columns if 'Team' in c]
        if t_col and pd.notna(row.get(t_col[0])) and str(row.get(t_col[0])).startswith('http'):
            with c2: st.
