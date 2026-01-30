import streamlit as st
import pandas as pd
import requests, io

st.title("🕵️ LMCP Data Scanner")

# Jou skakel
U = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?output=csv"

st.write("Besig om konneksie te toets...")

try:
    # Ons dwing Google om vars data te stuur
    r = requests.get(U, timeout=10)
    
    if r.status_code == 200:
        st.success("✅ Konneksie met Google is reg!")
        
        # Lees die rou teks
        raw_data = r.content.decode('utf-8')
        
        if len(raw_data.strip()) < 10:
            st.error("❌ Google stuur 'n leë lêer. Maak seker die data is op die eerste blad.")
        else:
            st.write("### Rou Data Gevind:")
            df = pd.read_csv(io.StringIO(raw_data))
            st.dataframe(df) # Wys die hele tabel
            
            st.write("### Kolom Name:")
            st.write(list(df.columns))
    else:
        st.error(f"❌ Google fout kode: {r.status_code}")

except Exception as e:
    st.error(f"❌ Kritieke Fout: {e}")

st.info("As die tabel hierbo leeg is, beteken dit jou 'Publish to Web' skakel wys na 'n leë tab in jou Excel.")
