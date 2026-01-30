import streamlit as st
import pandas as pd
import requests, io, time

st.set_page_config(page_title="LMCP Hub", layout="centered")

# BANNER
st.markdown("<h1 style='text-align:center;color:#800000;'>LAERSKOOL MIDSTREAM COLLEGE PRIMARY</h1>", unsafe_allow_html=True)

# HIERDIE ID IS VAN JOU SHEET - DIT VERANDER NIE
SID = "1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8"
# Ons gebruik die 'gviz' metode - dit is die vinnigste pad
U = f"https://docs.google.com/spreadsheets/d/{SID}/gviz/tq?tqx=out:csv"

def load_data():
    try:
        r = requests.get(U, timeout=10)
        if r.status_code == 200:
            df = pd.read_csv(io.StringIO(r.content.decode('utf-8')), dtype=str).fillna("")
            return df
        return None
    except:
        return None

df = load_data()

if df is not None and not df.empty:
    st.success(f"✅ Data gevind! ({len(df)} rye)")
    
    # Hierdie deel wys die data ongeag die kolom-name
    for _, r in df.iterrows():
        try:
            # Ons vat net die eerste paar kolomme wat gewoonlik data bevat
            col1 = str(r.iloc[3]) if len(r) > 3 else "" # Activity
            col2 = str(r.iloc[5]) if len(r) > 5 else "" # Date
            col3 = str(r.iloc[6]) if len(r) > 6 else "" # Venue
            
            if len(col1) < 2: continue

            st.markdown(f"""
            <div style="background:white; padding:15px; border-radius:10px; border-left:8px solid #800000; margin-bottom:10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                <b style="color:#800000; font-size:1.1rem;">{col1}</b><br>
                📅 {col2} | 📍 {col3}
            </div>
            """, unsafe_allow_html=True)
        except:
            continue
else:
    st.error("⚠️ Kan nog nie die data sien nie.")
    st.info("Maak seker jou Google Sheet is oop: Share -> Anyone with the link can view.")
    time.sleep(5)
    st.rerun()
