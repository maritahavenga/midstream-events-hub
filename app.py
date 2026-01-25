import streamlit as st
import pandas as pd
import urllib.parse

# 1. Styling
st.set_page_config(page_title="Midstream Events Hub", page_icon="🏆")
st.markdown("""
    <style>
    .stApp { background-color: #008080; }
    .event-card {
        background-color: white; padding: 20px; border-radius: 15px;
        border-left: 12px solid #800000; margin-bottom: 5px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }
    .event-title { color: #800000; font-weight: bold; font-size: 1.2rem; }
    .venue-link { color: #800000 !important; font-weight: bold; text-decoration: underline; }
    .stButton button { width: 100%; background-color: #800000 !important; color: white !important; border-radius: 8px; font-weight: bold; height: 3em; }
    </style>
    """, unsafe_allow_html=True)

# 2. Logo
st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", width=150)
st.markdown("<h1 style='text-align: center; color: white;'>EVENTS HUB 2026</h1>", unsafe_allow_html=True)

# 3. Data
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=15)
def load_data():
    df = pd.read_csv(URL)
    df.columns = [str(c).strip() for c in df.columns]
    return df

try:
    df = load_data()
    for i, row in df.iterrows():
        # Icons
        cat = str(row.get('Category','')).lower()
        icon = "https://cdn-icons-png.flaticon.com/512/3163/3163635.png"
        if "cult" in cat: icon = "https://cdn-icons-png.flaticon.com/512/3163/3163732.png"

        # Map Link
        v = str(row.get('Venue', 'TBA'))
        map_url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(v + ' South Africa')}"

        st.markdown(f"""
            <div class="event-card">
                <img src="{icon}" width="40" style="float: right;">
                <div style="color: #555; font-weight: bold;">📅 {row.get('Date','TBA')}</div>
                <div class="event-title">{row.get('Event','Event')}</div>
                <div style="margin-top:8px;">📍 Venue: <a href="{map_url}" target="_blank" class="venue-link">{v}</a></div>
            </div>
        """, unsafe_allow_html=True)

        # Buttons
        c1, c2, c3 = st.columns(3)
        cols = df.columns
        
        p = [c for c in cols if 'Program' in c]
        if p and pd.notna(row.get(p[0])) and str(row.get(p[0])).startswith('http'):
            with c1: st.link_button("📜 Program", str(row.get(p[0])))

        t = [c for c in cols if 'Team' in c]
        if t and pd.notna(row.get(t[0])) and str(row.get(t[0])).startswith('http'):
            with c2: st.link_button("🏃 Team", str(row.get(t[0])))

        b = [c for c in cols if 'Transport' in c]
        if b and pd.notna(row.get(b[0])) and str(row.get(b[0])).startswith('http'):
            with c3: st.link_button("
