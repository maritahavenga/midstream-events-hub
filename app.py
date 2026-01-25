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
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
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
    return df

# Helper to clean and check links
def get_lnk(val):
    s = str(val).strip()
    return s if "http" in s.lower() else None

try:
    data_raw = load()
    ch = st.selectbox("Filter Events:", ["All", "Sport", "Culture", "Academics"])
    df = data_raw if ch == "All" else data_raw[data_raw.iloc[:, 0].str.contains(ch, case=False, na=False)]

    for _, r in df.iterrows():
        evt, dat, ven = str(r.iloc[1]), str(r.iloc[2]), str(r.iloc[3])
        p_l, t_l, s_l, i_l = get_lnk(r.iloc[4]), get_lnk(r.iloc[5]), get_lnk(r.iloc[6]), str(r.iloc[7]).strip()
        
        mu = f"https://www.google.com/maps/search/?api=1&query={up.quote(ven + ' Midstream')}"
        
        # Info logic: check if Column H is a link or text
        is_info_lnk = "http" in i_l.lower()
        bx = f'<div class="box"><b>Note:</b> {i_l}</div>' if (i_l and i_l.lower()!='nan' and not is_info_lnk) else ""

        btn_html = '<div class="btn-row">'
        if p_l: btn_html += f'<a href="{p_l}" target="_blank" class="btn">PROGRAMME</a>'
        if t_l: btn_html += f'<a href="{t_l}" target="_blank" class="btn">TEAM</a>'
        if s_l: btn_html += f'<a href="{s_l}" target="_blank" class="btn">CONFIRM</a>'
        if is_info_lnk: btn_html += f'<a href="{i_l}" target="_blank" class="btn">INFORMATION</a>'
        btn_html += '</div>'

        st.markdown(f'''<div class="card">
            <div style="font-size:0.85rem">📅 {dat}</div>
            <div class="t">{evt}</div>
            <div style="font-size:0.85rem">📍 <a href="{mu}" target="_blank" class="v">{ven}</a></div>
            {bx}
            {btn_html}
        </div>''', unsafe_allow_html=True)
except:
    st.info("Syncing...")
