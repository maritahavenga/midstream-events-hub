import streamlit as st
import pandas as pd
import urllib.parse as up
import re

st.set_page_config(page_title="Events Hub", layout="centered")

st.markdown("""<style>
.stApp{background:#008080}.block-container{padding:1rem;max-width:500px}
.card{background:white!important;padding:15px;border-radius:15px;border-left:10px solid #800000;margin-bottom:15px;box-shadow:0 4px 10px rgba(0,0,0,0.2)}
.t{color:#800000!important;font-weight:bold;font-size:1.1rem;margin:5px 0}.v{color:#800000!important;font-weight:bold;text-decoration:underline}
.box{background:#f1f3f5;padding:10px;border-radius:10px;margin:10px 0;border-left:5px solid #008080;color:#333;font-size:0.85rem}
.btn-row {display: flex!important; gap: 4px!important; justify-content: space-between!important; margin-top: 15px!important; width: 100%!important;}
.btn {
    flex: 1!important; background: #800000!important; color: white!important; 
    text-align: center!important; text-decoration: none!important;
    font-weight: bold!important; font-size: 0.62rem!important; padding: 12px 1px!important;
    border-radius: 6px!important; display: block!important; white-space: nowrap!important;
}
div[data-baseweb="select"] > div { background-color: #800000 !important; border: none !important; }
div[data-baseweb="select"] * { color: white !important; }
label { color: white !important; font-weight: bold; }
.stButton>button { width: 100%; background-color: #800000; color: white; border: none; font-weight: bold; margin-top: 28px; height: 42px; }
</style>""", unsafe_allow_html=True)

st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", use_container_width=True)
st.markdown("<h2 style='text-align:center;color:white;'>EVENTS HUB 2026</h2>", unsafe_allow_html=True)

U = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=1)
def load():
    return pd.read_csv(U)

def get_l(val):
    t = str(val).strip()
    m = re.search(r'https?://[^\s<>"]+', t)
    return m.group(0) if m else None

try:
    df_raw = load()
    
    # Setup columns for the top bar
    c1, c2, c3 = st.columns([2, 2, 1])
    
    with c1:
        cat = st.selectbox("Category:", ["All", "Sport", "Culture", "Academics"], key="cat_sel")

    # Narrow down the list based on the Category first
    if cat != "All":
        filtered_for_list = df_raw[df_raw.iloc[:, 0].str.contains(cat, case=False, na=False)]
    else:
        filtered_for_list = df_raw

    # Create the dynamic event list based on the category chosen
    event_list = ["All Events"] + sorted(filtered_for_list.iloc[:, 1].dropna().unique().tolist())

    with c2:
        q = st.selectbox("Find Event:", event_list, key="evt_sel")
        
    with c3:
        if st.button("Reset"):
            st.session_state.cat_sel = "All"
            st.session_state.evt_sel = "All Events"
            st.rerun()

    # Final Filter for the Cards
    df = filtered_for_list
    if q != "All Events":
        df = df[df.iloc[:, 1] == q]

    for _, r in df.iterrows():
        evt, dat, ven = str(r.iloc[1]), str(r.iloc[2]), str(r.iloc[3])
        p, t, s, i_r = get_l(r.iloc[4]), get_l(r.iloc[5]), get_l(r.iloc[6]), str(r.iloc[7]).strip()
        i_l = get_l(i_r)
        mu = f"https://www.google.com/maps/search/?api=1&query={up.quote(ven + ' Midstream')}"
        bx = f'<div class="box"><b>Note:</b> {i_r}</div>' if (i_r and i_r.lower()!='nan' and not i_l) else ""

        btn_html = '<div class="btn-row">'
        if p: btn_html += f'<a href="{p}" target="_blank" class="btn">PROGRAMME</a>'
        if t: btn_html += f'<a href="{t}" target="_blank" class="btn">TEAM</a>'
        if s: btn_html += f'<a href="{s}" target="_blank" class="btn">CONFIRM</a>'
        if i_l: btn_html += f'<a href="{i_l}" target="_blank" class="btn">INFORMATION</a>'
        btn_html += '</div>'

        st.markdown(f'''<div class="card">
            <div style="font-size:0.85rem; color:#333;">📅 {dat}</div>
            <div class="t">{evt}</div>
            <div style="font-size:0.85rem; color:#333;">📍 <a href="{mu}" target="_blank" class="v">{ven}</a></div>
            {bx}{btn_html}</div>''', unsafe_allow_html=True)
except Exception:
    st.info("Refreshing...")
