import streamlit as st
import pandas as pd
import urllib.parse as up

st.set_page_config(page_title="Events Hub", layout="wide")

st.markdown("""<style>.stApp{background:#008080}.block-container{padding-top:0rem;max-width:800px}.card{background:white;padding:20px;border-radius:15px;border-left:12px solid #800000;margin-bottom:5px;box-shadow:0 4px 10px rgba(0,0,0,0.2)}.t{color:#800000;font-weight:bold;font-size:1.1rem}.v{color:#800000;font-weight:bold;text-decoration:underline}.stButton button{width:100%;background:#800000!important;color:white!important;font-weight:bold;height:3em;font-size:0.7rem!important;padding:0px!important;border-radius:8px}.box{background:#f1f3f5;padding:12px;border-radius:10px;margin-top:5px;border-left:5px solid #008080;color:#333;font-size:0.85rem}label{color:white!important;font-weight:bold}</style>""", unsafe_allow_html=True)

st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", use_container_width=True)
st.markdown("<h2 style='text-align:center;color:white;'>EVENTS HUB 2026</h2>", unsafe_allow_html=True)

U = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=2)
def load():
    df = pd.read_csv(U)
    df.columns = [str(c).strip() for c in df.columns]
    return df

try:
    df_raw = load()
    ch = st.selectbox("Filter:", ["All", "Sport", "Culture", "Academics"])
    data = df_raw if ch == "All" else df_raw[df_raw['Category'].str.contains(ch, case=False, na=False)]

    for _, r in data.iterrows():
        evt, dat = str(r.get('Event','Event')), str(r.get('Date','TBA'))
        ven, nfo = str(r.get('Venue','TBA')), str(r.get('Information',''))
        
        mu = f"https://www.google.com/maps/search/?api=1&query={up.quote(ven + ' Midstream')}"
        is_l = nfo.startswith('http')
        # Only show grey box if there is text and it's NOT a link
        bx = f'<div class="box"><b>Note:</b> {nfo}</div>' if (nfo.strip() and nfo.lower()!='nan' and not is_l) else ""

        st.markdown(f'''<div class="card"><div>📅 {dat}</div><div class="t">{evt}</div><div>📍 <a href="{mu}" target="_blank" class="v">{ven}</a></div>{bx}</div>''', unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)
        
        # Check for each link and show button if present
        prog, team, bus = r.get('Program Link'), r.get('Team/Cast Link'), r.get('Transport')
        
        if pd.notna(prog) and str(prog).strip() != "":
            with c1: st.link_button("PROGRAM", str(prog))
        if pd.notna(team) and str(team).strip() != "":
            with c2: st.link_button("TEAM", str(team))
        if pd.notna(bus) and str(bus).strip() != "":
            with c3: st.link_button("BUS", str(bus))
        if is_l:
            with c4: st.link_button("INFO", nfo)
            
        st.markdown("<br>", unsafe_allow_html=True)
except Exception:
    st.info("Syncing events...")
