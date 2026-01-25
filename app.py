import streamlit as st
import pandas as pd

# 1. Branding
st.set_page_config(page_title="Midstream Events Hub", page_icon="🏆")
st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", width=180)

st.title("🏆 Midstream Events Hub")
st.markdown("---")

# 2. Link to your Google Sheet
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(SHEET_URL)
    df.columns = df.columns.str.strip()
    return df

try:
    data = load_data()
    
    # Simple Search
    search = st.text_input("🔍 Search for an event (e.g. Swimming, Grade 4):")
    if search:
        data = data[data.apply(lambda row: row.astype(str).str.contains(search, case=False).any(), axis=1)]

    # Display Events
    for index, row in data.iterrows():
        with st.expander(f"📅 {row['Date']} - {row['Event']}"):
            st.write(f"📍 **Venue:** {row['Venue']}")
            col1, col2, col3 = st.columns(3)
            with col1:
                if pd.notna(row['Program Link']): st.link_button("📜 Program", row['Program Link'])
            with col2:
                if pd.notna(row['Team/Cast Link']): st.link_button("🏃 Team List", row['Team/Cast Link'])
            with col3:
                if pd.notna(row['Transport/Sign-up']): st.link_button("🚌 Transport", row['Transport/Sign-up'])

except Exception as e:
    st.warning("The Events Hub is being updated. Please check back shortly!")
