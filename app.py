import streamlit as st
import pandas as pd
import requests, io

st.set_page_config(page_title="LMCP Hub", layout="centered")

# --- CSS VIR DIE LOOK ---
st.markdown("""
    <style>
    .stApp { background-color: #f9f9f9; }
    .card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        border-left: 8px solid #800000;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 15px;
    }
    .title { color: #800000; font-weight: bold; font-size: 1.2rem; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center; color:#800000;'>LMCP EVENT HUB</h1>", unsafe_allow_html=True)

# ONS GEBRUIK DIE DIREKTE EXPORT SKAKEL (DIT IS STABILER AS 'PUBLISH')
SHEET_ID = "1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8"
GID = "37057995"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

def fetch_data():
    try:
        # Ons "masker" die app sodat Google dink dit is 'n gewone browser
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(URL, headers=headers, timeout=10)
        if r.status_code == 200:
            return pd.read_csv(io.StringIO(r.content.decode('utf-8')), dtype=str).fillna("")
        else:
            return None
    except:
        return None

df = fetch_data()

if df is not None and not df.empty:
    st.success("Konneksie Herstel!")
    for _, row in df.iterrows():
        try:
            act = str(row.iloc[3]).strip()  # Activity (Kolom D)
            date = str(row.iloc[5]).strip() # Date (Kolom F)
            ven = str(row.iloc[6]).strip()  # Venue (Kolom G)
            
            if len(act) < 2 or "activity" in act.lower(): continue

            st.markdown(f"""
                <div class="card">
                    <div class="title">{act}</div>
                    <div style="color:#008080; font-weight:bold;">📅 {date}</div>
                    <div style="color:#555;">📍 {ven}</div>
                </div>
                """, unsafe_allow_html=True)
        except:
            continue
else:
    st.error("Google blokkeer steeds die toegang.")
    st.info("As dit nog steeds wys, is die dokument dalk weer op 'Restricted' gestel onder die 'Share' knoppie.")
    if st.button("Probeer weer"):
        st.rerun()
