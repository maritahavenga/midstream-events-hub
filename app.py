import streamlit as st
import pandas as pd
import urllib.parse as up

st.set_page_config(page_title="Events Hub", layout="wide")

st.markdown("""<style>
.stApp{background:#008080}.block-container{padding-top:0rem;max-width:800px}
.card{background:white;padding:20px;border-radius:15px;border-left:12px solid #800000;margin-bottom:5px;box-shadow:0 4px 10px rgba(0,0,0,0.2)}
.t{color:#800000;font-weight:bold;font-size:1.1rem}.v{color:#800000;font-weight:bold;text-decoration:underline}
/* Thinner buttons for 4-column layout */
.stButton button {
    width: 100%; background: #800000!important; color: white!important; 
    font-weight: bold; height: 3em; font-size: 0.75rem!important; 
    padding: 0px!important; border-radius: 8px;
}
.box{background:#f1f3f5;padding:12px;border-radius:10px;margin-top:10px;border-left:5px solid #008080;color:#333;font-size:0.9rem}
label{color:white!important;font-weight:bold}
</style>""", unsafe_allow_html=True)

st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", use_container_width=True)
st.markdown("<h1 style='text-align:center;color:white;'>EVENTS HUB 2026</h1>", unsafe_allow_html=True)

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=2)
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
        icon = "https://www.svgrepo.com/show/447475/whistle.svg"
        if "cult" in cat: icon = "https://www.svgrepo.com/show/396263/drama-masks.svg"
        elif "acad" in cat: icon = "https://www.svgrepo.com/show/532363/graduation-cap.svg"

        v, info = str(r.get('Venue','TBA')), str(r.get('Information',''))
        m_url = f"https://www.google.com/maps/search/?api=1&query={up.quote(v + ' Midstream')}"
        
        is_link = info.startswith('http')
        info_html = f'<div class="box">ℹ️ <b>Note:</b> {info}</div>' if (info and info.lower() != 'nan' and not is_link) else ""

        st.markdown(f'''<div class="card"><img src="{icon}" width="50" style="float:right"><div style="color:#555;font-weight:bold">📅 {r.get("Date","TBA")}</div><div class="t">{r.get("Event","
