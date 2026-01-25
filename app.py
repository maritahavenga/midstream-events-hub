import streamlit as st
import pandas as pd
import urllib.parse as up

st.set_page_config(page_title="Events Hub", layout="centered")

st.markdown("""<style>
.stApp{background:#008080}.block-container{padding:1rem;max-width:500px}
.card{background:white;padding:15px;border-radius:15px;border-left:10px solid #800000;margin-bottom:15px;box-shadow:0 4px 10px rgba(0,0,0,0.2)}
.t{color:#800000;font-weight:bold;font-size:1.1rem;margin:5px 0}.v{color:#800000;font-weight:bold;text-decoration:underline}
.box{background:#f1f3f5;padding:10px;border-radius:10px;margin:10px 0;border-left:5px solid #008080;color:#333;font-size:0.85rem}
.btn-row {display: flex; gap: 4px; justify-content: space-between; margin-top: 10px;}
.btn {
    flex: 1; background: #800000; color: white !important; 
    text-align: center; text-decoration: none !important;
    font-weight: bold; font-size: 0.62rem; padding: 12px 1px;
    border-radius: 6px; display: block; white-space: nowrap;
    letter-spacing: -0.2px;
}
div[data-baseweb="select"] > div { background-color: #800000 !important; border: none !important; }
div[data-baseweb="select"] * { color: white !important; }
label { color: white !important; font-weight: bold; }
</style>""", unsafe_allow_html=True)

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
    ch = st.selectbox("Filter Events:", ["All", "Sport", "Culture", "Academics"])
    data = df_raw if ch == "All" else df_raw[df_raw['Category'].str.contains(ch, case=False, na=False)]

    for _, r in data.iterrows():
        evt, dat, ven = str(r.get('Event','')), str(r.get('Date','')), str(r.get('Venue',''))
        nfo = str(r.get('Information','')).strip()
        mu = f"https://www.google.com/maps/search/?api=1&query={up.quote(ven + ' Midstream')}"
        
        is_l = nfo.lower().startswith('http')
        bx = f'<div class="box"><b>Note:</b> {nfo}</div>' if (nfo and nfo.lower()!='nan' and not is_l) else ""

        btn_html = '<div class="btn-row">'
        # We look for the columns and clean the data immediately
        links = {
            "PROGRAMME": str(r.get('Program Link','')).strip(),
            "TEAM": str(r.get('Team/Cast Link','')).strip(),
            "CONFIRM": str(r.get('Transport','')).strip()
        }
        
        for label, val in links.items():
            if val.lower().startswith("http"):
                btn_html += f'<a href="{val}" target="_blank" class="btn">{label}</a>'
        
        if is_l:
            btn_html += f'<a href="{nfo}" target="_blank" class="btn">INFORMATION</a>'
        
        btn_html += '</div>'

        st.markdown(f'''<div class="card">
            <div style="font-size:0.85rem">📅 {dat}</div>
            <div class="t">{evt}</div>
            <div style="font-size:0.85rem">📍 <a href="{mu}" target="_blank" class="v">{ven}</a></div>
            {bx}
            {btn_html}
        </div>''', unsafe_allow_html=True)

except Exception:
    st.info("Syncing events...")
