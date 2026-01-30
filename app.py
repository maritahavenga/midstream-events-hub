import streamlit as st
import pandas as pd
import requests, io, re, pytz
from datetime import datetime

st.set_page_config(page_title="LMCP Hub", layout="centered")

# --- BANNER ---
st.markdown("""
<div style='text-align:center; padding: 10px;'>
    <h1 style='color:#800000; font-family:sans-serif; margin-bottom:0;'>LAERSKOOL MIDSTREAM COLLEGE PRIMARY</h1>
    <p style='color:#008080; font-size:1.2rem; margin-top:5px; font-weight:bold;'>Digital Event Hub</p>
</div>
""", unsafe_allow_html=True)

# DIE NUWE SKAKEL VANAF JOU FOTO
U = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?output=csv"

def cl(v): return str(v).replace(".0", "").replace("nan", "").strip()

@st.cache_data(ttl=1)
def ld():
    try:
        r = requests.get(f"{U}&v={datetime.now().timestamp()}", timeout=15)
        if r.status_code == 200:
            return pd.read_csv(io.StringIO(r.content.decode('utf-8')), dtype=str).fillna("")
        return pd.DataFrame()
    except: return pd.DataFrame()

df = ld()

if not df.empty:
    try:
        # Ons gebruik die name van jou foto
        C_ACT = "Activity/Subject Name"
        C_DATE = "Date / Due Date"
        C_AGE = "Age Group (9,10) / Grade (1,2,3)"
        C_VEN = "Venue"

        st.markdown("<div style='background-color:#f9f9f9; padding:20px; border-radius:15px; margin-bottom:20px;'>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1: sa = st.multiselect("Filter Activity", sorted(df[C_ACT].unique()))
        with c2: sg = st.multiselect("Filter Grade/Age", sorted(df[C_AGE].unique()))
        st.markdown("</div>", unsafe_allow_html=True)

        for _, r in df.iterrows():
            act = str(r[C_ACT]).replace("nan", "").strip()
            age = cl(r[C_AGE])
            
            if sa and act not in sa: continue
            if sg and age not in sg: continue
            
            st.markdown(f"""
            <div style="background:white; padding:20px; border-radius:12px; border-left:10px solid #800000; margin-bottom:20px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
                <b style="color:#800000; font-size:1.2rem;">{act} (Gr/U{age})</b><br>
                <span style="color:#555;">📅 {r[C_DATE]}</span><br>
                <b style="color:#008080;">📍 {str(r[C_VEN]).upper()}</b>
            </div>
            """, unsafe_allow_html=True)

    except Exception as e:
        st.error("Wagt op Google om die kolomme korrek te stuur...")
else:
    st.info("🔄 Data word gelaai... Verfris die bladsy oor 30 sekondes.")
    if st.button("Force Refresh"):
        st.cache_data.clear()
        st.rerun()

st.markdown("<br><center style='font-size:0.8rem;color:#999;'>LAERSKOOL MIDSTREAM COLLEGE PRIMARY Digital Hub 2026</center>", unsafe_allow_html=True)
