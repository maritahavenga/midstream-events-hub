import streamlit as st
import pandas as pd
import requests, io

# Bladsy instellings
st.set_page_config(page_title="LMCP Event Hub", layout="centered")

# --- DIE MOOI LOOK (CSS) ---
st.markdown("""
    <style>
    .stApp { background-color: #f4f4f4; }
    .header-banner {
        background: linear-gradient(135deg, #800000 0%, #a00000 100%);
        color: white;
        padding: 30px;
        border-radius: 0 0 25px 25px;
        text-align: center;
        margin-top: -60px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
        font-family: sans-serif;
    }
    .event-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        border-left: 10px solid #800000;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        font-family: sans-serif;
    }
    .event-title { color: #800000; font-size: 1.3rem; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- BANNER ---
st.markdown("""
    <div class="header-banner">
        <h1 style='margin:0;'>LAERSKOOL MIDSTREAM COLLEGE</h1>
        <p style='margin:0; opacity:0.9;'>Primary Event Hub</p>
    </div>
    """, unsafe_allow_html=True)

# JOU WERKende SKAKEL
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?output=csv"

def get_data():
    try:
        # Ons gebruik 'n timeout en 'n browser header
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(URL, headers=headers, timeout=10)
        if r.status_code == 200:
            return pd.read_csv(io.StringIO(r.content.decode('utf-8')))
        return None
    except:
        return None

df = get_data()

st.write("") 

if df is not None and not df.empty:
    search = st.text_input("🔍 Soek vir aktiwiteit...", "")
    
    found_any = False
    for index, row in df.iterrows():
        try:
            # Kolomme: 3=Activity, 5=Date, 6=Venue
            act = str(row.iloc[3]).strip()
            date = str(row.iloc[5]).strip()
            ven = str(row.iloc[6]).strip()
            
            if len(act) < 2 or "activity" in act.lower() or "nan" in act.lower():
                continue
            
            if search.lower() in act.lower() or search.lower() in ven.lower():
                found_any = True
                st.markdown(f"""
                    <div class="event-card">
                        <div class="event-title">{act}</div>
                        <div style="color:#008080; font-weight:bold;">📅 {date}</div>
                        <div style="color:#555;">📍 {ven.upper()}</div>
                    </div>
                    """, unsafe_allow_html=True)
        except:
            continue

    if not found_any and search == "":
        st.info("Besig om data te sinkroniseer... Verfris asseblief oor 'n paar sekondes.")
else:
    st.warning("Wag tans vir Google om die data-stroom oop te maak. Klik op die knoppie hieronder as dit nie verskyn nie.")

# REFRESH KNOPPIE
if st.button("🔄 Herlaai Nou"):
    st.rerun()

st.caption("© 2026 Midstream College Primary Hub")
