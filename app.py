import streamlit as st
import pandas as pd
import requests, io

st.set_page_config(page_title="LMCP Hub", layout="centered")

st.markdown("<h1 style='text-align:center;color:#800000;'>LAERSKOOL MIDSTREAM COLLEGE PRIMARY</h1>", unsafe_allow_html=True)

# JOU SHEET ID
ID = "1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8"

# ONS TEIKEN NOU DIE 'Upcoming' TAB SPESIFIEK BY SY NAAM
URL = f"https://docs.google.com/spreadsheets/d/{ID}/gviz/tq?tqx=out:csv&sheet=Upcoming"

@st.cache_data(ttl=1)
def load_data():
    try:
        r = requests.get(URL, timeout=10)
        df = pd.read_csv(io.StringIO(r.content.decode('utf-8')), dtype=str).fillna("")
        return df
    except:
        return pd.DataFrame()

df = load_data()

if not df.empty:
    st.write("### 📅 Opkomende Aktiwiteite")
    
    for index, row in df.iterrows():
        try:
            # Ons gebruik kolom-indekse: D=3, F=5, G=6
            act = str(row.iloc[3]).strip()  # Activity
            date = str(row.iloc[5]).strip() # Date
            ven = str(row.iloc[6]).strip()  # Venue
            
            # Slaan leë rye oor
            if len(act) < 2 or act.lower() == "nan":
                continue

            st.markdown(f"""
            <div style="background:white; padding:20px; border-radius:12px; border-left:10px solid #800000; margin-bottom:15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <b style="color:#800000; font-size:1.2rem;">{act}</b><br>
                <span style="color:#555;">📅 {date}</span><br>
                <b style="color:#008080;">📍 {ven.upper()}</b>
            </div>
            """, unsafe_allow_html=True)
        except:
            continue
else:
    st.error("Kon nie die 'Upcoming' tab vind nie. Maak seker die naam onderaan jou Sheet is presies 'Upcoming'.")
    if st.button("Probeer weer"):
        st.rerun()
