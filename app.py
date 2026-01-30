import streamlit as st
import pandas as pd
import requests, io

st.set_page_config(page_title="LMCP Hub", layout="centered")

# --- BANNER ---
st.markdown("<h1 style='text-align:center;color:#800000;'>LAERSKOOL MIDSTREAM COLLEGE PRIMARY</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:#008080;font-weight:bold;text-align:center;'>Digital Event Hub</p>", unsafe_allow_html=True)

# ONS GEBRUIK DIE DIREKTE ID VANAF JOU SKERMSKOOT
SHEET_ID = "1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8"
# Ons teiken die 'Upcoming' tab spesifiek
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

@st.cache_data(ttl=1)
def load_data():
    try:
        # Hierdie metode dwing Google om die data as 'n rou lêer te gee
        r = requests.get(URL, timeout=10)
        df = pd.read_csv(io.StringIO(r.content.decode('utf-8')), dtype=str).fillna("")
        return df
    except:
        return pd.DataFrame()

df = load_data()

st.markdown("---")

if not df.empty:
    # Wys 'n sukses boodskap sodat ons weet die konneksie is gemaak
    st.success(f"Konneksie suksesvol! {len(df)} rye gevind.")
    
    for _, r in df.iterrows():
        try:
            # Ons gebruik indekse (0,1,2,3) sodat name nie pla nie
            act = str(r.iloc[3]).strip()  # Kolom D
            date = str(r.iloc[5]).strip() # Kolom F
            ven = str(r.iloc[6]).strip()  # Kolom G
            
            # Slaan leë rye oor
            if len(act) < 2 or act.lower() == "nan":
                continue

            st.markdown(f"""
            <div style="background:white; padding:15px; border-radius:10px; border-left:8px solid #800000; margin-bottom:15px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                <b style="color:#800000; font-size:1.1rem;">{act}</b><br>
                📅 {date} | 📍 {ven}
            </div>
            """, unsafe_allow_html=True)
        except:
            continue
else:
    st.error("⚠️ Kan nie data trek nie. Maak seker die Google Sheet is op 'Anyone with the link' gestel.")
    if st.button("Probeer weer"):
        st.cache_data.clear()
        st.rerun()
