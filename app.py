import streamlit as st
import pandas as pd
import requests, io

# 1. Stel bladsy wydte en titel in
st.set_page_config(page_title="LMCP Event Hub", layout="centered")

# 2. Skool-spesifieke CSS
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
    .event-title { color: #800000; font-size: 1.3rem; font-weight: bold; margin-bottom: 5px; }
    .event-date { color: #008080; font-weight: bold; font-size: 1.1rem; }
    .event-venue { color: #555; font-size: 0.95rem; }
    </style>
    """, unsafe_allow_html=True)

# --- BANNER ---
st.markdown("""
    <div class="header-banner">
        <h1 style='margin:0; font-size:1.8rem; font-family: sans-serif;'>LAERSKOOL MIDSTREAM COLLEGE</h1>
        <p style='margin:0; opacity:0.9; font-family: sans-serif;'>Digital Event Hub</p>
    </div>
    """, unsafe_allow_html=True)

# 3. DATA KONNEKSIE (Sonder Cache wat kan vries)
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?output=csv"

def load_data_direct():
    try:
        # Ons dwing Google om vars data te gee met 'n random nommer
        import time
        t = int(time.time())
        r = requests.get(f"{URL}&refresh={t}", timeout=10)
        if r.status_code == 200:
            df = pd.read_csv(io.StringIO(r.content.decode('utf-8')), dtype=str).fillna("")
            return df
    except:
        return None
    return None

df = load_data_direct()

st.write("") 

if df is not None and not df.empty:
    search = st.text_input("🔍 Soek vir sport of aktiwiteit...", "")
    
    st.markdown("### Opkomende Events")
    
    found_any = False
    for i in range(len(df)):
        try:
            row = df.iloc[i]
            act = str(row.iloc[3]).strip()  # Activity
            date = str(row.iloc[5]).strip() # Date
            ven = str(row.iloc[6]).strip()  # Venue
            
            if len(act) < 2 or "activity" in act.lower():
                continue
            
            if search.lower() in act.lower() or search.lower() in ven.lower():
                found_any = True
                st.markdown(f"""
                    <div class="event-card">
                        <div class="event-title">{act}</div>
                        <div class="event-date">📅 {date}</div>
                        <div class="event-venue">📍 {ven.upper()}</div>
                    </div>
                    """, unsafe_allow_html=True)
        except:
            continue

    if not found_any:
        st.info("Geen aktiwiteite gevind nie.")
else:
    # As die data weg is, wys ons 'n help-knoppie
    st.warning("Google se konneksie is tans traag. Klik op die knoppie hieronder om te herlaai.")
    if st.button("🔄 Herlaai Data"):
        st.rerun()

st.markdown("---")
st.caption("© 2026 Midstream College Primary Hub")
