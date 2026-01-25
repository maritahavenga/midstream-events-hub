import streamlit as st
import pandas as pd
import urllib.parse as up

st.set_page_config(page_title="Events Hub", page_icon="🏆")
st.markdown("<style>.stApp{background:#008080}.card{background:white;padding:20px;border-radius:15px;border-left:12px solid #800000;margin-bottom:5px;box-shadow:0 4px 10px rgba(0,0,0,0.2)}.t{color:#800000;font-weight:bold;font-size:1.2rem}.v{color:#800000;font-weight:bold;text-decoration:underline}.stButton button{width:100%;background:#800000!important;color:white!important;font-weight:bold;height:3em}</style>",unsafe_allow_html=True)

st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", width=120)
st.markdown("<h1 style='text-align:center;color:white;'>EVENTS HUB 2026</h1>",unsafe_allow_html=True)

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=15)
def load():
    df = pd.read_csv(URL)
    df.columns = [str(c).strip() for c in df.columns]
    return df

try:
    df = load()
    for i, r in df.iterrows():
        cat = str(r.get('Category','')).lower()
        icon = "https://cdn-icons-png.flaticon.com/512/3163/3163635.png"
        if "cult" in cat: icon = "https://cdn-icons-png.flaticon.com/512/3163/3163732.png"
        
        v = str(r.get('Venue','TBA'))
        m_url = f"https://www.google.com/maps/search/?api=1&query={up.quote(v + ' South Africa')}"

        st.markdown(f'<div class="card"><img src="{icon}" width="40" style="float:right"><div style="color:#555;font-weight:bold">📅 {r.get("Date","TBA")}</div><div class="t">{r.get("Event","Event")}</div><div style="margin-top:8px">📍 Venue: <a href="{m_url}" target="_blank" class="v">{v}</a></div></div>',unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        cols = df.columns
        if any('Prog' in c for c in cols) and pd.notna(r.get('Program Link')):
            with c1: st.link_button("📜 Program", str(r.get('Program Link')))
        if any('Team' in c for c in cols) and pd.notna(r.get('Team/Cast Link')):
            with c2: st.link_button("🏃 Team", str(r.get('Team/Cast Link')))
        if any('Trans' in c for c in cols) and pd.notna(r.get('Transport/Sign-up')):
            with c3: st.link_button("🚌 Bus", str(r.get('Transport/Sign-up')))
        st.markdown("<br>",unsafe_allow_html=True)
except:
    st.info("Refreshing...")
