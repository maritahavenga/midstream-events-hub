import streamlit as st
import pandas as pd
import requests, io

st.set_page_config(page_title="LMCP Hub", layout="centered")

# --- BANNER ---
st.markdown("<h1 style='text-align:center;color:#800000;'>LAERSKOOL MIDSTREAM COLLEGE PRIMARY</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:#008080;font-weight:bold;text-align:center;'>Digital Event Hub</p>", unsafe_allow_html=True)

# JOU SHEET ID EN DIE REGTE GID
SID = "1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8"
GID = "37057995" 

# Die perfekte skakel wat reguit na daardie spesifieke tab gaan
URL = f"https://docs.google.com/spreadsheets/d/{SID}/export?format=csv&gid={GID}"

@st.cache_data(ttl=1)
def load_data():
    try:
        r = requests.get(URL, timeout=10)
        if r.status_code == 200:
            # Ons lees die data rou in
            df = pd.read_csv(io.StringIO(r.content.decode('utf-8')), dtype=str).fillna("")
            return df
        return pd.DataFrame()
    except:
        return pd.DataFrame()

df = load_data()

st.markdown("---")

if not df.empty:
    # As ons hier kom, is die konneksie uiteindelik daar!
    found_any = False
    
    for index, row in df.iterrows():
        try:
            # Ons gebruik die kolom-nommers (D=3, F=5, G=6)
            act = str(row.iloc[3]).strip()  # Activity
            date = str(row.iloc[5]).strip() # Date
            ven = str(row.iloc[6]).strip()  # Venue
            age = str(row.iloc[11]).replace(".0", "").strip() # Age/Grade (Kolom L)
            
            # Slaan leë rye of rye sonder 'n aktiwiteit oor
            if len(act) < 2 or act.lower() == "nan" or act.lower() == "activity":
                continue

            found_any = True
            st.markdown(f"""
            <div style="background:white; padding:20px; border-radius:12px; border-left:10px solid #800000; margin-bottom:15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); font-family:sans-serif;">
                <b style="color:#800000; font-size:1.2rem;">{act} (Gr/U{age})</b><br>
                <span style="color:#555;">📅 {date}</span><br>
                <b style="color:#008080;">📍 {ven.upper()}</b>
            </div>
            """, unsafe_allow_html=True)
        except:
            continue
            
    if not found_any:
        st.info("Konneksie is reg, maar dit lyk of die rye tans leeg is op die 'Upcoming' blad.")
else:
    st.error("⚠️ Google weier steeds toegang tot hierdie spesifieke tab. Maak seker die hele dokument is 'Public'.")

if st.button("Herlaai"):
    st.cache_data.clear()
    st.rerun()
