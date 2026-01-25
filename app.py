import streamlit as st
import pandas as pd

# 1. Branding
st.set_page_config(page_title="Midstream Events Hub", page_icon="🏆")

st.markdown("""
    <style>
    .stButton button {
        width: 100%;
        background-color: #008080 !important;
        color: white !important;
        font-weight: bold;
        border-radius: 10px;
        height: 3em;
    }
    h1 { color: #800000; }
    </style>
    """, unsafe_allow_html=True)

st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", width=150)
st.title("🏆 Midstream Events Hub")

# 2. Data Connection
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=30)
def load_data():
    df = pd.read_csv(SHEET_URL)
    # This cleans up the column names automatically
    df.columns = [c.strip() for c in df.columns]
    return df

try:
    df = load_data()
    
    # Check if we have data
    if df.empty:
        st.info("No events scheduled at the moment. Please check back later!")
    else:
        # Loop through each row
        for index, row in df.iterrows():
            event_name = str(row.get('Event', 'Unnamed Event'))
            event_date = str(row.get('Date', 'TBA'))
            
            with st.expander(f"📅 {event_date} - {event_name}", expanded=True):
                st.write(f"📍 **Venue:** {row.get('Venue', 'TBA')}")
                
                # Check each link before showing the button
                prog = row.get('Program Link')
                if pd.notna(prog) and str(prog).startswith('http'):
                    st.link_button("📜 VIEW PROGRAM", str(prog))
                
                team = row.get('Team/Cast Link')
                if pd.notna(team) and str(team).startswith('http'):
                    st.link_button("🏃 VIEW TEAM LIST", str(team))
                
                trans = row.get('Transport/Sign-up')
                if pd.notna(trans) and str(trans).startswith('http'):
                    st.link_button("🚌 TRANSPORT / SIGN-UP", str(trans))

except Exception as e:
    st.error("Waiting for Google Sheets to sync...")
    # This helps you see exactly what is wrong if it fails again
    # st.write(e)
