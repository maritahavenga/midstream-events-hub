import streamlit as st
import pandas as pd
import urllib.parse as up

st.set_page_config(page_title="Events Hub", layout="wide")

# 1. Styling - Including the Info Box look
st.markdown("""<style>
.stApp{background:#008080}.block-container{padding-top:0rem;max-width:800px}
.card{background:white;padding:20px;border-radius:15px;border-left:12px solid #800000;margin-bottom:5px;box-shadow:0 4px 10px rgba(0,0,0,0.2)}
.t{color:#800000;font-weight:bold;font-size:1.2rem}
.v{color:#800000;font-weight:bold;text-decoration:underline}
.stButton button{width:100%;background:#800000!important;color:white!important;font-weight:bold;height:3.5em}
.info-text-box{background:#f1f3f5;padding:15px;border-radius:10px;margin-top:10px;border-left:5px solid #008080;color:#333;font-size:0.95rem}
label{color:white!important;font-weight:bold}
</style>""",unsafe_allow_html=True)

# 2. Header
st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", use_container_width=True)
st.markdown("<h1 style='text-align:center;color:white;'>EVENTS HUB 2026</h1>",unsafe_allow_html=True)

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=5)
def load():
    df = pd.read_csv(URL)
    df.columns = [str(c).strip() for c in df.columns]
    return df

try:
    data = load()
    choice = st.selectbox("Filter:", ["All", "Sport", "Culture", "Academics"])
    df = data if choice == "All" else data[data['Category'].str.contains(choice, case=False, na=False)]

    for i, r in df.iterrows():
        cat = str(r.get('Category','')).lower()
        # High-reliability icons
        icon = "https://cdn-icons-png.flaticon.com/128/3349/3349234.png" # Whistle
        if "cult" in cat: icon = "https://cdn-icons-png.flaticon.com/128/3163/3163732.png" # Masks
        elif "acad" in cat: icon = "https://cdn-icons-png.flaticon.com/128/2232/2232688.png" # Book

        v = str(r.get('Venue','TBA'))
        m_url = f"https://www.google.com/maps/search/?api=1&query={up.quote(v + ' Midstream')}"

        # Information Logic: Detect if it's a link or just text
        info_val = str(r.get('Information', ''))
        is_link = info_val.startswith('http')
        
        info_html = ""
        # Only show the box if it's TEXT (not a link)
        if pd.notna(r.get('Information')) and info_val.strip() != "" and not is_link:
            info_html = f'<div class="info-text-box">ℹ️ <b>Note:</b> {info_val}</div>'

        st.markdown(f'''<div class="card"><img src="{icon}" width="50"
