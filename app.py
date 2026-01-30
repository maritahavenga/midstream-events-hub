import streamlit as st
import pandas as pd
import requests, io

st.set_page_config(page_title="LMCP Hub", layout="centered")

# --- BANNER ---
st.markdown("<h1 style='text-align:center;color:#800000;'>LAERSKOOL MIDSTREAM COLLEGE PRIMARY</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:#008080;font-weight:bold;text-align:center;'>Digital Event Hub</p>", unsafe_allow_html=True)

# JOU NUWE KORREKTE SKAKEL
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?output=csv"

@st.cache_data(ttl=1)
def load_data():
    try:
        r = requests.get(URL, timeout=10)
        if r.status_code == 200:
            # Ons lees die data en ignoreer leë rye
            df = pd.read_csv(io.StringIO(r.content.decode('utf-8')), dtype=str).fillna("")
            return df
        return pd.DataFrame()
    except:
        return pd.DataFrame()

df = load_data()

st.markdown("---")

if not df.empty:
    found_any = False
    for index, row in df.iterrows():
        try:
            # Gebruik kolom-nommers gebaseer op jou sheet
            # Kolom D (index 3) is Activity, F (index 5) is Date, G (index 6) is Venue
            act = str(row.iloc[3]).strip()
            date = str(row.iloc[5]).strip()
            ven = str(row.iloc[6]).strip()
            
            # Slaan rye oor wat nie regte data bevat nie
            if len(act) < 2 or act.lower() == "nan" or "activity" in act.lower():
                continue

            found_any = True
            st.markdown(f"""
            <div style="background:white; padding:20px; border-radius:12px; border-left:10px solid #800000; margin-bottom:15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); font-family:sans-serif;">
                <b style="color:#800000; font-size:1.2rem;">{act}</b><br>
                <span style="color:#555;">📅 {date}</span><br>
                <b style="color:#008080;">📍 {ven.upper()}</b>
            </div>
            """, unsafe_allow_html=True)
        except:
            continue
    
    if not found_any:
        st.info("Die konneksie werk! Vul asseblief jou 'Upcoming' tab in die Google Sheet in om events te sien.")
else:
    st.error("Wag tans vir Google om die data-stroom te begin...")

if st.button("Verfris Data"):
    st.cache_data.clear()
    st.rerun()
