import streamlit as st
import pandas as pd
import requests, io

st.set_page_config(page_title="LMCP Hub", layout="centered")

# BANNER
st.markdown("<h1 style='text-align:center;color:#800000;'>LAERSKOOL MIDSTREAM COLLEGE PRIMARY</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:#008080;font-weight:bold;'>Digital Event Hub</p>", unsafe_allow_html=True)

# NUWE DIREKTE SKAKEL
U = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?output=csv"

@st.cache_data(ttl=1)
def load_data():
    try:
        # Ons gebruik 'n timeout om te verhoed dat dit vir ewig hang
        r = requests.get(U, timeout=10)
        if r.status_code == 200:
            return pd.read_csv(io.StringIO(r.content.decode('utf-8')), dtype=str).fillna("")
        return pd.DataFrame()
    except:
        return pd.DataFrame()

df = load_data()

st.markdown("---")

if not df.empty:
    st.success(f"✅ Konneksie gemaak! {len(df)} rye gevind.")
    # Wys die rou data as 'n tabel om te sien wat Google stuur
    st.dataframe(df)
else:
    st.error("⚠️ Kan nog nie data trek nie. Google se bediener is dalk besig om die skakel op te dateer.")
    if st.button("Herlaai"):
        st.cache_data.clear()
        st.rerun()
