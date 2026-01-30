import streamlit as st
import pandas as pd
import requests, io

st.set_page_config(page_title="Data Check", layout="wide")

st.title("LMCP Data Scanner")

# JOU SHEET ID
ID = "1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8"
# Hierdie skakel dwing Google om die DATA van die eerste tab te gee
URL = f"https://docs.google.com/spreadsheets/d/{ID}/export?format=csv"

try:
    # Ons trek die data
    r = requests.get(URL)
    data = r.content.decode('utf-8')
    
    # Ons laai dit in 'n tabel
    df = pd.read_csv(io.StringIO(data))
    
    if df.empty:
        st.error("Google stuur 'n leë lêer. Is die data dalk op die tweede tab?")
    else:
        st.success(f"Sukses! Ek sien {len(df)} rye data.")
        # WYS DIE HELE TABEL
        st.write("Hier is wat ek sien:")
        st.table(df.head(20)) # Wys die eerste 20 rye

except Exception as e:
    st.write("Fout met konneksie:")
    st.write(e)
