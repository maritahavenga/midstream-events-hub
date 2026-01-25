import streamlit as st
import pandas as pd
import urllib.parse as up
import re

st.set_page_config(page_title="Events Hub", layout="wide")

# CSS Styling
st.markdown("""<style>
.stApp{background:#008080}.block-container{padding-top:0rem;max-width:800px}
.card{background:white;padding:20px;border-radius:15px;border-left:12px solid #800000;margin-bottom:5px;box-shadow:0 4px 10px rgba(0,0,0,0.2)}
.t{color:#800000;font-weight:bold;font-size:1.2rem}
.v{color:#800000;font-weight:bold;text-decoration:underline}
.stButton button{width:100%;background:#800000!important;color:white!important;font-weight:bold;height:3.5em}
label{color:white!important;font-weight:bold}
.info-box{background:#f1f3f5;padding:12px;border-radius:8px;margin-top:10px;font-size:0.95rem;border-left:4px solid #008080;color:#333;line-height:1.4}
</style>""",unsafe_allow_html=True)

# Banner
st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", use_container_width=True)
st.markdown("<h1 style='text-align:center;color:white;'>EVENTS HUB 2026</h1>",unsafe_allow_html=True)

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=10)
def load():
    df = pd.read_csv(URL)
    df.columns = [str(c).strip() for c in df.columns]
    return df

def make_clickable(text):
    return re.sub(r'(https?://[^\s]+)', r'<a href="\1" target="_blank" style="color:#800000;font-weight:bold;text-decoration:underline;">Click to View Letter</a>', text)

try:
    data = load()
    choice = st.selectbox("Filter:", ["All", "Sport", "Culture", "Academics"])
    df = data if choice == "All" else data[data['Category'].str.contains(choice, case=False, na=False)]

    for i, r in df.iterrows():
        cat = str(r.get('Category','')).lower()
        
        # Using guaranteed high-uptime official-style icons
        icon = "https://i.postimg.cc/mD3mX6P1/sport.png" # Sport Whistle
        if "cult" in cat: icon = "https://i.postimg.cc/q7Sj2X7p/culture.png" # Drama Masks
        elif "acad" in cat: icon = "https://i.postimg.cc/BZ8fFfJ8/academic.png" # Book/Graduation

        # Map Link
        v = str(r.get('Venue','TBA'))
        m_url = f"https://www.google.com/maps/search/?api=1&query={up.quote(v + ' Midstream')}"

        # Information Logic
        raw_info = str(r.get('Information', ''))
        info_html = ""
        if raw_info.strip() != "" and raw_info.lower() != "nan":
            info_html = f'<div class="info-box">ℹ️ {make_clickable(raw_info)}</div>'

        st.markdown(f'''<div class="card">
            <img src="{icon}" width="60" style="float:right">
            <div style="color:#555;font-weight:bold">📅 {r.get("Date","TBA")}</div>
            <div class="t">{r.get("Event","Event")}</div>
            <div style="margin-top:8px">📍 Venue: <a href="{m_url}" target="_blank" class="v">{v}</a></div>
            {info_html}
        </div>''', unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        if pd.notna(r.get('Program Link')):
            with c1: st.link_button("📜 PROGRAM", str(r.get('Program Link')))
        if pd.notna(r.get('Team/Cast Link')):
            with c2: st.link_button("🏃 TEAM LIST", str(r.get('Team/Cast Link')))
        if pd.notna(r.get('Transport/Sign-up')):
            with c3: st.link_button("🚌 BUS / SIGN-UP", str(r.get('Transport/Sign-up')))
        st.markdown("<br>", unsafe_allow_html=True)
except Exception as e:
    st.info("Syncing Events...")
