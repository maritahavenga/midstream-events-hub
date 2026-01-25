import streamlit as st
import pandas as pd
import urllib.parse as up

st.set_page_config(page_title="Events Hub", layout="wide")

st.markdown("""<style>.stApp{background:#008080}.block-container{padding-top:0rem;max-width:800px}.card{background:white;padding:15px;border-radius:15px;border-left:12px solid #800000;margin-bottom:5px;box-shadow:0 4px 10px rgba(0,0,0,0.2)}.t{color:#800000;font-weight:bold;font-size:1rem}.v{color:#800000;font-weight:bold;text-decoration:underline}.stButton button{width:100%;background:#800000!important;color:white!important;font-weight:bold;height:3em;font-size:0.65rem!important;padding:0px!important}.box{background:#f1f3f5;padding:10px;border-radius:10px;margin-top:5px;border-left:5px solid #008080;color:#333;font-size:0.8rem}label{color:white!important;font-weight:bold}</style>""", unsafe_allow_html=True)

st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", use_container_width=True)
st.markdown("<h2 style='text-align:center;color:white;'>EVENTS HUB 2026</h2>", unsafe_allow_html=True)

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=2)
def load():
    df = pd.read_csv(URL)
    df.columns = [str(c).strip() for c in df.columns]
    return df

try:
    data = load()
    ch = st.selectbox("Filter:", ["All", "Sport", "Culture", "Academics"])
    df = data if ch == "All" else data[data['Category'].str.contains(ch, case=False, na=False)]

    for i, r in df.iterrows():
        ct = str(r.get('Category','')).lower()
        ic = "https://www.svgrepo.com/show/447475/whistle.svg"
        if "cult" in ct: ic = "https://www.svgrepo.com/show/396263/drama-masks.svg"
        elif "acad" in ct: ic = "https://www.svgrepo.com/show/532363/graduation-cap.svg"

        v, nfo = str(r.get('Venue','TBA')), str(r.get('Information',''))
        mu = f"https://www.google.com/maps/search/?api=1&query={up.quote(v + ' Midstream')}"
        lnk = nfo.startswith('http')
        bx = f'<div class="box">ℹ️ {nfo}</div>' if (nfo and nfo.lower()!='nan' and not lnk) else ""

        st.markdown(f'''<div class="card"><img src="{ic}" width="40" style="float:right"><div>📅 {r.get("Date","TBA")}</div><div class="t">{r.get("Event","Event")}</div><div>📍 <a href="{mu}" target="_blank" class="v">{v}</a></div>{bx}</div>''', unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)
        # Using a safer way to get links without using long names
        p_l = r.get('Program Link')
        t_l = r.get('Team/Cast Link')
        b_l = r.get('Transport/Sign-up')

        if pd.notna(p_l):
            with c1: st.link_button("📜 PROG", str(p_l))
        if pd.notna(t_l):
            with c2: st.link_button
