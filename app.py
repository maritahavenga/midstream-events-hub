import streamlit as st
import pandas as pd

st.title("LMCP TOETS")

# Direkte skakel
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?output=csv"

try:
    # Ons gebruik pandas se mees basiese lees-metode
    df = pd.read_csv(URL)
    
    if not df.empty:
        st.write("✅ DATA IS HIER!")
        # Wys net die eerste 10 rye in 'n gewone tabel
        st.table(df.head(10))
    else:
        st.write("Die lêer is leeg.")
except Exception as e:
    st.write("❌ FOUTMELDING:")
    st.code(str(e))

if st.button("Herlaai"):
    st.rerun()
