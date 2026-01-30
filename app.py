import streamlit as st
import pandas as pd
import requests, io

st.set_page_config(page_title="LMCP Hub")

# JOU SHEET ID
ID = "1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8"
# Hierdie skakel dwing Google om die HELE dokument te stuur
URL = f"https://docs.google.com/spreadsheets/d/{ID}/export?format=csv"

st.title("LMCP EVENT HUB")

try:
    # Ons haal die data direk
    response = requests.get(URL, timeout=10)
    df = pd.read_csv(io.StringIO(response.content.decode('utf-8')))
    
    if not df.empty:
        st.success("✅ Data is hier!")
        st.dataframe(df) # Dit wys die rou tabel
    else:
        st.warning("Die dokument is leeg.")
except Exception as e:
    st.error("Google weier steeds toegang. Dit is moontlik die skool se sekuriteits-instellings.")
