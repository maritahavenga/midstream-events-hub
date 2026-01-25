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
}
div[data-baseweb="select"] > div { background-color: #800000 !important; border: none !important; }
div[data-baseweb="select"] * { color: white !important; }
label { color: white !important; font-weight: bold; }
</style>""", unsafe_allow_html=True)

st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", use_container_width=True)
st.markdown("<h2 style='text-align:center;color:white;'>EVENTS HUB 2026</h2>", unsafe_allow_html=True)

# THE LIVE LINK (Make sure this matches your 'Publish to Web' link)
U = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=1) # Set to 1 second for instant updates
def load():
    return pd.read_csv(U)

def clean(v):
    return str(v).strip() if pd.notna(v) else ""

try:
    df = load()
    ch = st.selectbox("Filter Events:", ["All", "Sport", "Culture", "Academics"])
    if ch != "All":
        df = df[df.iloc[:, 0].str.contains(ch, case=False, na=False)]

    for _, r in df.iterrows():
        # Get by Position
        evt, dat, ven = clean(r.iloc[1]), clean(r.iloc[2]), clean(r.iloc[3])
        p_l, t_l, s_l, i_l = clean(r.iloc[4]), clean(r.iloc[5]), clean(r.iloc[6]), clean(r.iloc[7])
        
        mu = f"https://www.google.com/maps/search/?api=1&query={up.quote(ven + ' Midstream')}"
        is_i_lnk = "http" in i_l.lower()
        
        bx = f'<div class="box"><b>Note:</b> {i_l}</div>' if (i_l and i_l.lower()!='nan' and not is_i_lnk) else ""

        # BUTTON LOGIC
        btn_html = '<div class="btn-row">'
        if "http" in p_l.lower(): btn_html += f'<a href="{p_l}" target="_blank" class="btn">PROGRAMME</a>'
        if "http" in t_l.lower(): btn_html += f'<a href="{t_l}" target="_blank" class="btn">TEAM</a>'
        if "http" in s_l.lower(): btn_html += f'<a href="{s_l}" target="_blank" class="btn">CONFIRM</a>'
        if is_i_lnk: btn_html += f'<a href="{i_l}" target="_blank" class="btn">INFORMATION</a>'
        btn_html += '</div>'

        st.markdown(f'''<div class="card">
            <div style="font-size:0.85rem">📅 {dat}</div>
            <div class="t">{evt}</div>
            <div style="font-size:0.85rem">📍 <a href="{mu}" target="_blank" class="v">{ven}</a></div>
            {bx}
            {btn_html}
        </div>''', unsafe_allow_html=True)
except Exception as e:
    st.error(f"Error: {e}")
