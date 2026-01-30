import streamlit as st
import pandas as pd
import requests, io

# 1. Stel bladsy wydte en titel in
st.set_page_config(page_title="LMCP Event Hub", layout="centered")

# 2. Skool-spesifieke CSS (Die "Look & Feel")
st.markdown("""
    <style>
    .stApp { background-color: #f4f4f4; }
    /* Die Rooi Banner */
    .header-banner {
        background: linear-gradient(135deg, #800000 0%, #a00000 100%);
        color: white;
        padding: 30px;
        border-radius: 0 0 25px 25px;
        text-align: center;
        margin-top: -60px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }
    /* Die Event Kaartjies */
    .event-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        border-left: 10px solid #800000;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .event-title { color: #800000; font-size: 1.3rem; font-weight: bold; margin-bottom: 5px; }
    .event-date { color: #008080; font-weight: bold; font-size: 1.1rem; }
    .event-venue { color: #555; font-size: 0.95rem; }
    </style>
    """, unsafe_allow_html=True)

# --- BANNER ---
st.markdown("""
    <div class="header-banner">
        <h1 style='margin:0; font-size:1.8rem;'>LAERSKOOL MIDSTREAM COLLEGE</h1>
        <p style='margin:0; opacity:0.9;'>Digital Event Hub</p>
    </div>
    """, unsafe_allow_html=True)

# 3. DATA KONNEKSIE
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?output=csv"

@st.cache_data(ttl=60)
def load_data():
    try:
        r = requests.get(URL, timeout=10)
        df = pd.read_csv(io.StringIO(r.content.decode('utf-8')), dtype=str).fillna("")
        return df
    except:
        return pd.DataFrame()

df = load_data()

st.write("") # Spasie

if not df.empty:
    # --- FILTERS (KNOPPIES EN SOEK) ---
    search = st.text_input("🔍 Soek vir sport of aktiwiteit...", "")
    
    st.markdown("### Opkomende Events")
    
    found = False
    for i in range(len(df)):
        try:
            row = df.iloc[i]
            act = str(row.iloc[3]).strip()  # Activity
            date = str(row.iloc[5]).strip() # Date
            ven = str(row.iloc[6]).strip()  # Venue
            
            # Filter leë rye en opskrifte
            if len(act) < 2 or "activity" in act.lower():
                continue
            
            # Pas soek-filter toe
            if search.lower() not in act.lower() and search.lower() not in ven.lower():
                continue

            found = True
            
            # Vertoon die "Card"
            st.markdown(f"""
                <div class="event-card">
                    <div class="event-title">{act}</div>
                    <div class="event-date">📅 {date}</div>
                    <div class="event-venue">📍 {ven.upper()}</div>
                </div>
                """, unsafe_allow_html=True)
        except:
            continue

    if not found:
        st.info("Geen aktiwiteite gevind nie.")
else:
    st.error("Kon nie die inligting laai nie. Verfris asseblief die bladsy.")

# --- HERLAAI KNOPPIE ---
st.markdown("---")
if st.button("🔄 Verfris Data"):
    st.cache_data.clear()
    st.rerun()

st.caption("© 2026 Midstream College Primary Hub")
