import streamlit as st
import pandas as pd

# 1. Branding & Style
st.set_page_config(page_title="Midstream Events Hub", page_icon="🏆")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    h1, h2 { color: #800000; } 
    /* This makes buttons look bigger and easier to press on phones */
    .stButton button {
        width: 100%;
        height: 3em;
        background-color: #008080 !important;
        color: white !important;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", width=180)
st.title("🏆 Midstream Events Hub")

# 2. Data Connection
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=30) # Updated more frequently (30 seconds)
def load_data():
    df = pd.read_csv(SHEET_URL)
    df.columns = df.columns.str.strip()
    return df

try:
    data = load_data()
    
    # Display Events
    for index, row in data.iterrows():
        with st.expander(f"📅 {row['Date']} - {row['Event']}", expanded=True):
            st.write(f"📍 **Venue:** {row['Venue']}")
            
            # Action Buttons
            if pd.notna(row['Program Link']):
                st.link_button("📜 VIEW PROGRAM", str(row['Program Link']), use_container_width=True)
            
            if pd.notna(row['Team/Cast Link']):
                st.link_button("🏃 VIEW TEAM LIST", str(row['Team/Cast Link']), use_container_width=True)
            
            if pd.notna(row['Transport/Sign-up']):
                st.link_button("🚌 TRANSPORT / SIGN-UP", str(row['Transport/Sign-up']), use_container_width=True)

except Exception as e:
    st.warning("The Events Hub is being updated. Please refresh in a moment.")
