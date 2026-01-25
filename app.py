import streamlit as st
import pandas as pd

# 1. Page Configuration & Styling
st.set_page_config(page_title="Midstream Events Hub", page_icon="🏆", layout="centered")

st.markdown("""
    <style>
    /* Professional Teal Background */
    .stApp {
        background-color: #008080;
    }
    /* Event Card Styling */
    .event-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        border-left: 10px solid #800000;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .event-title { color: #800000; font-weight: bold; font-size: 1.2rem; margin-bottom: 5px; }
    .event-info { color: #333; margin-bottom: 10px; }
    
    /* Buttons */
    .stButton button {
        width: 100%;
        background-color: #800000 !important;
        color: white !important;
        border-radius: 8px;
        font-weight: bold;
        border: none;
        height: 3em;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Header
st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", width=180)
st.markdown("<h1 style='text-align: center; color: white;'>Events Hub 2026</h1>", unsafe_allow_html=True)

# 3. Data Loading
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=10)
def load_data():
    df = pd.read_csv(SHEET_URL)
    df.columns = [str(c).strip() for c in df.columns]
    return df

try:
    df = load_data()
    
    for index, row in df.iterrows():
        # Choose Icon based on Category
        category = str(row.get('Category', '')).lower()
        icon_url = "https://midstream-primary.co.za/wp-content/uploads/2022/05/Sport-Icon.png" # Default
        
        if "cult" in category:
            icon_url = "https://midstream-primary.co.za/wp-content/uploads/2022/05/Culture-Icon.png"
        elif "sport" in category:
            icon_url = "https://midstream-primary.co.za/wp-content/uploads/2022/05/Sport-Icon.png"

        # Create the visual card
        with st.container():
            st.markdown(f"""
                <div class="event-card">
                    <img src="{icon_url}" width="50" style="float: right;">
                    <div class="event-title">📅 {row.get('Date', 'TBA')}</div>
                    <div class="event-title">{row.get('Event', 'Unnamed Event')}</div>
                    <div class="event-info">📍 {row.get('Venue', 'TBA')}</div>
                </div>
            """, unsafe_allow_html=True)
            
            # Action Buttons (Outside the HTML div for Streamlit functionality)
            col1, col2, col3 = st.columns(3)
            
            # Check for Program Link
            prog_col = [c for c in df.columns if 'Program' in c]
            if prog_col:
                val = row.get(prog_col[0])
                if pd.notna(val) and str(val).startswith('http'):
                    with col1: st.link_button("📜 Program", str(val))

            # Check for Team Link
            team_col = [c for c in df.columns if 'Team' in c]
            if team_col:
                val = row.get(team_col[0])
                if pd.notna(val) and str(val).startswith('http'):
                    with col2: st.link_button("🏃 Team", str(val))

            # Check for Transport Link
            trans_col = [c for c in df.columns if 'Transport' in c]
            if trans_col:
                val = row.get(trans_col[0])
                if pd.notna(val) and str(val).startswith('http'):
                    with col3: st.link_button("🚌 Bus", str(val))
            
            st.markdown("<br>", unsafe_allow_html=True)

except Exception as e:
    st.error("Refreshing content...")
