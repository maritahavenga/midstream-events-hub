import streamlit as st
import pandas as pd
import requests, io
import time

st.set_page_config(page_title="LMCP Event Hub", layout="centered")

# --- STYLE ---
st.markdown("""
    <style>
    .event-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        border-left: 10px solid #800000;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .header-style {
        text-align: center;
        background: #800000;
        color: white;
        padding: 20px;
        border-radius: 0 0 20px 20px;
        margin-top: -60px;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="header-style"><h1>LMCP EVENT HUB</h1></div>', unsafe_allow_html=True)

# JOU SKAKEL
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?output=csv"

# ONS HAAL @st.cache_data UIT SODAT HY NIE "VRIES" NIE
def load_data_force():
    for i in range(3): # Probeer 3 keer as Google stadig is
        try:
            r = requests.get(URL, timeout=5)
            if r.status_code == 200:
                data = r.content.decode('utf-8')
                df = pd.read_csv(io.StringIO(data), dtype=str).fillna("")
                if not df.empty:
                    return df
            time.sleep(1) # Wag 'n sekonde voor weer probeer
        except:
            continue
    return pd.DataFrame()

df = load_data_force()

st.write("") # Spasie

if not df.empty:
    st.success("✅ Data is lewendig")
    for _, row in df.iterrows():
        try:
            act = str(row.iloc[3]).strip()
            date = str(row.iloc[5]).strip()
            ven = str(row.iloc[6]).strip()
            
            if len(act) < 2 or "activity" in act.lower(): continue

            st.markdown(f"""
                <div class="event-card">
                    <b style="color:#800000; font-size:1.2rem;">{act}</b><br>
                    <span style="color:#555;">📅 {date} | 📍 {ven}</span>
                </div>
                """, unsafe_allow_html=True)
        except:
            continue
else:
    st.error("Google neem te lank om te antwoord.")
    if st.button("Dwing Herlaai"):
        st.rerun()
