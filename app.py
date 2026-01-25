import streamlit as st
import pandas as pd
import urllib.parse # This helps clean the venue names for the map

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
    .event-info { color: #333; margin-top: 8px; font-size: 0.95rem; margin-bottom: 10px;}
    .stButton button { width: 100%; background-color: #800000 !important; color: white !important; border-radius: 8px; font-weight: bold; height: 3.2em; }
    </style>
    """, unsafe_allow_html=True)

st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", width=150)
st.markdown("<h1 style='text-align: center; color: white;'>EVENTS HUB 2026</h1>", unsafe_allow_html=True)

SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=15)
def load_data():
    df = pd.read_csv(SHEET_URL)
    df.columns = [str(c).strip() for c in df.columns]
    return df

try:
    df = load_data()
    for index, row in df.iterrows():
        # Category Icons
        cat = str(row.get('Category', '')).lower()
        icon = "https://cdn-icons-png.flaticon.com/512/3163/3163635.png"
        if "cult" in cat: icon = "https://cdn-icons-png.flaticon.com/512/3163/3163732.png"

        # Display Card
        st.markdown(f"""
            <div class="event-card">
                <img src="{icon}" width="45" style="float: right; opacity: 0.8;">
                <div class="event-date">📅 {row.get('Date', 'TBA')}</div>
                <div class="event-title">{row.get('Event', 'Event')}</div>
                <div class="event-info">📍 {row.get('Venue', 'TBA')}</div>
            </div>
        """, unsafe_allow_html=True)

        # GOOGLE MAPS EMBED
        venue = str(row.get('Venue', ''))
        if venue and venue != 'TBA':
            # This creates a "Search" URL for Google Maps
            clean_venue = urllib.parse.quote(venue + " South Africa")
            map_url = f"https://www.google.com/maps?q={clean_venue}&output=embed"
            st.components.v1.iframe(map_url, height=200)

        # Action Buttons
        c1, c2, c3 = st.columns(3)
        p_col = [c for c in df.columns if 'Program' in c]
        if p_col and pd.notna(row.get(p_col[0])) and str(row.get(p_col[0])).startswith('http'):
            with c1: st.link_button("📜 Program", str(row.get(p_col[0])))
        
        t_col = [c for c in df.columns if 'Team' in c]
        if t_col and pd.notna(row.get(t_col[0])) and str(row.get(t_col[0])).startswith('http'):
            with c2: st.link_button("🏃 Team", str(row.get(t_col[0])))

        b_col = [c for c in df.columns if 'Transport' in c]
        if b_col and pd.notna(row.get(b_col[0])) and str(row.get(b_col[0])).startswith('http'):
            with c3: st.link_button("🚌 Bus", str(row.get(b_col[0])))
            
        st.markdown("<br>", unsafe_allow_html=True)

except Exception as e:
    st.error("Refreshing...")
