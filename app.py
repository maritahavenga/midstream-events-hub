import streamlit as st
import pandas as pd
import requests, io

st.set_page_config(page_title="LMCP Hub", layout="centered")

# --- BANNER ---
st.markdown("<h1 style='text-align:center;color:#800000;'>LAERSKOOL MIDSTREAM COLLEGE PRIMARY</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:#008080;font-weight:bold;text-align:center;'>Digital Event Hub</p>", unsafe_allow_html=True)

# ONS GEBRUIK NOU DIE PUBLIEKE 'PUB' SKAKEL MAAR TEIKEN DIE GID DIREK
SID = "1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8"
GID = "37057995"
URL = f"https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid={GID}&single=true&output=csv"

@st.cache_data(ttl=1)
def load_data():
    try:
        # Ons dwing Google om die data as 'n rou lêer te gee sonder om vrae te vra
        r = requests.get(URL, timeout=10)
        if r.status_code == 200:
            df = pd.read_csv(io.StringIO(r.content.decode('utf-8')), dtype=str).fillna("")
            return df
        return pd.DataFrame()
    except:
        return pd.DataFrame()

df = load_data()

st.markdown("---")

if not df.empty:
    # AS DIT WERK, SAL ONS DIE RYE SIEN
    for index, row in df.iterrows():
        try:
            # Kolom D=3, F=5, G=6
            act = str(row.iloc[3]).strip()
            date = str(row.iloc[5]).strip()
            ven = str(row.iloc[6]).strip()
            
            if len(act) < 2 or "activity" in act.lower():
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
    st.error("⚠️ Google blokkeer steeds die 'pyp'.")
    st.write("Probeer die volgende: Gaan na jou Sheet -> File -> Share -> Publish to web.")
    st.write("Maak seker 'Entire Document' en 'CSV' is gekies, en klik 'Publish'.")
