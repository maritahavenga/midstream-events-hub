import streamlit as st
import pandas as pd

# 1. Page Configuration & Professional Styling
st.set_page_config(page_title="Midstream Events Hub", page_icon="🏆", layout="centered")

st.markdown("""
    <style>
    /* Professional Teal Background */
    .stApp { background-color: #008080; }
    
    /* Event Card Styling */
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
    .event-info { color: #333; margin-top: 8px; font-size: 0.95rem; }
    
    /* Maroon Buttons */
    .stButton button {
        width: 100%;
        background-color: #800000 !important;
        color: white !important;
        border-radius: 8px;
        font-weight: bold;
        border: none;
        height: 3.2em;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .stButton button:hover { background-color: #a00000 !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. Centered Logo
col_l, col_m, col_r = st.columns([1, 2, 1])
with col_m:
    st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", use_container_width=True)

st.markdown("<h1 style='text-align: center; color: white; font-family: sans-serif;'>EVENTS HUB 2026</h1>", unsafe_allow_html=True)
st.markdown("---")

# 3. Data Connection
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=15)
def load_data():
    df = pd.read_csv(SHEET_URL)
    df.columns = [str(c).strip() for c in df.columns]
    return df

try:
    df = load_data()
    
    for index, row in df.iterrows():
        # Set Sport vs Culture Icons (using reliable hosted icons)
        category = str(row.get('Category', '')).lower()
        # Sport icon (Whistle/Running) or Culture icon (Masks/Art)
        icon_url = "https://cdn-icons-png.flaticon.com/512/3163/3163635.png" # Default Sport Whistle
        
        if "cult" in category:
            icon_url = "https://cdn-icons-png.flaticon.com/512/3163/3163732.png" # Drama Masks

        # Display the Card
        st.markdown(f"""
            <div class="event-card">
                <img src="{icon_url}" width="45" style="float: right; opacity: 0.8;">
                <div class="event-date">📅 {row.get('Date', 'TBA')}</div>
                <div class="event-title">{row.get('Event', 'Unnamed Event')}</div>
                <div class="event-info">📍 {row.get('Venue', 'TBA')}</div>
            </div>
        """, unsafe_allow_html=True)
        
        # Action Buttons
        c1, c2, c3 = st.columns(3)
        
        # Program Link
        p_col = [c for c in df.columns if 'Program' in c]
        if p_col and pd.notna(row.get(p_col[0])) and str(row.get(p_col[0])).startswith('http'):
            with c1: st.link_button("📜 Program", str(row.get(p_col[0])))
        
        # Team Link
        t_col = [c for c in df.columns if 'Team' in c]
        if t_col and pd.notna(row.get(t_col[0])) and str(row.get(t_col[0])).startswith('http'):
            with c2: st.link_button("🏃 Team", str(row.get(t_col[0])))

        # Transport Link
        b_col = [c for c in df.columns if 'Transport' in c]
        if b_col and pd.notna(row.
