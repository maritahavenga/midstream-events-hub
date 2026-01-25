import streamlit as st
import pandas as pd
import urllib.parse as up
import re # This helps us find links in your text

st.set_page_config(page_title="Events Hub", layout="wide")

st.markdown("""<style>.stApp{background:#008080}.block-container{padding-top:0rem;max-width:800px}.card{background:white;padding:20px;border-radius:15px;border-left:12px solid #800000;margin-bottom:5px;box-shadow:0 4px 10px rgba(0,0,0,0.2)}.t{color:#800000;font-weight:bold;font-size:1.2rem}.v{color:#800000;font-weight:bold;text-decoration:underline}.stButton button{width:100%;background:#800000!important;color:white!important;font-weight:bold;height:3.5em}label{color:white!important;font-weight:bold}.conf-text{color:#008080;font-size:0.8rem;text-align:center;font-weight:bold;margin-top:5px;}.info-box{background:#f0f2f6;padding:12px;border-radius:8px;margin-top:10px;font-size:0.9rem;border-left:4px solid #008080;color:#333; line-height:1.4;}</style>""",unsafe_allow_html=True)

st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", use_container_width=True)
st.markdown("<h1 style='text-align:center;color:white;'>EVENTS HUB 2026</h1>",unsafe_allow_html=True)

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=15)
def load():
    df = pd.read_csv(URL)
    df.columns = [str(c).strip() for c in df.columns]
    return df

def make_clickable(text):
    # This magic line turns any http link in your text into a clickable link
    return re.sub(r'(https?://[^\s]+)', r'<a href="\1" target="_blank" style="color:#800000; font-weight:bold; text-decoration:underline;">Click here to view letter</a>', text)

try:
    data = load()
    choice = st.selectbox("Filter Category:", ["All", "Sport", "Culture", "Academics"])
    df = data if choice == "All" else data[data['Category'].str.contains(choice, case=False, na=False)]

    for i, r in df.iterrows():
        cat = str(r.get('Category','')).lower()
        icon = "https://midstream-primary.co.za/wp-content/uploads/2022/05/Sport-Icon.png"
        if "cult" in cat: icon = "https://midstream-primary.co.za/wp-content/uploads/2022/05/Culture-Icon.png"
        elif "acad" in cat: icon = "https://midstream-primary.co.za/wp-content/uploads/2022/05/Academic-Icon.png"
        
        v = str(r.get('Venue','TBA'))
        m_url = f"https://www.google.com/maps/search/?api=1&query={up.quote(v + ' Midstream')}"

        # Get info text and make links clickable
        raw_info = str(r.get('Information', ''))
        info_html = ""
        if pd.notna(r.get('Information')) and raw_info.strip() != "" and raw_info != "nan":
            clickable_info = make_clickable(raw_info)
            info_html = f'<div class="info-box">ℹ️ {clickable_info}</div>'

        st.markdown(f'''<div class="card"><img src="{icon}" width="60" style="float:right"><div style="color:#555;font-weight:bold">📅 {r.get("Date","TBA")}</div><div class="t">{r.get("Event","Event")}</div><div style="margin-top:8px">📍 Venue: <a href="{m_url}" target="_blank" class="v">{v}</a></div>{info_html}</div>''', unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        if pd.notna(r.get('Program Link')):
            with c1: st.link_button("📜 PROGRAM", str(r.get('Program Link')))
        if pd.notna(r.get('Team/Cast Link')):
            with c2: st.link_button("🏃 TEAM LIST", str(r.get('Team/Cast Link')))
        if pd.notna(r.get('Transport/Sign-up')):
            with c3: 
                st.link_button("🚌 BUS / SIGN-UP", str(r.get('Transport/Sign-up')))
                st.markdown('<p class="conf-text">✓ Tap to Confirm</p>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
except:
    st.info("Syncing events...")
