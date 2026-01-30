import streamlit as st
import pandas as pd
import requests, io

# Stel die bladsy styl in
st.set_page_config(page_title="LMCP Event Hub", layout="centered")

# --- CUSTOM CSS VIR DIE LOOK & FEEL ---
st.markdown("""
    <style>
    .main { background-color: #f5f5f5; }
    .event-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        border-left: 10px solid #800000;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        transition: transform 0.2s;
    }
    .event-card:hover { transform: scale(1.02); }
    .event-title { color: #800000; font-size: 1.3rem; font-weight: bold; margin-bottom: 5px; }
    .event-info { color: #008080; font-weight: 600; font-size: 1rem; }
    .event-detail { color: #555; font-size: 0.9rem; margin-top: 5px; }
    .header-style {
        text-align: center;
        background: linear-gradient(135deg, #800000 0%, #a00000 100%);
        color: white;
        padding: 30px;
        border-radius: 0 0 30px 30px;
        margin-top: -60px;
        margin-bottom: 30px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }
    </style>
    """, unsafe_allow_html=True)

# --- HEADER ---
st.markdown("""
    <div class="header-style">
        <h1 style='margin:0; font-size:1.8rem;'>LAERSKOOL MIDSTREAM COLLEGE</h1>
        <p style='margin:0; opacity:0.9; font-weight:300;'>PRIMARY EVENT HUB</p>
    </div>
    """, unsafe_allow_html=True)

# --- DATA LAAI ---
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?output=csv"

@st.cache_data(ttl=60) # Verfris elke minuut
def load_data():
    try:
        r = requests.get(URL, timeout=10)
        df = pd.read_csv(io.StringIO(r.content.decode('utf-8')), dtype=str).fillna("")
        return df
    except:
        return pd.DataFrame()

df = load_data()

# --- DISPLAY ---
if not df.empty:
    # Opsie om te soek
    search = st.text_input("🔍 Soek vir 'n sport of aktiwiteit...", "").lower()
    
    st.markdown("### Opkomende Aktiwiteite")
    
    found_count = 0
    for _, row in df.iterrows():
        try:
            # Kolom D=3 (Activity), F=5 (Date), G=6 (Venue), L=11 (Age)
            act = str(row.iloc[3]).strip()
            date = str(row.iloc[5]).strip()
            ven = str(row.iloc[6]).strip()
            age = str(row.iloc[11]).replace(".0", "").strip()
            info = str(row.iloc[10]).strip() # Kolom K vir ekstra inligting

            # Filter uit leë rye
            if len(act) < 2 or "activity" in act.lower(): continue
            
            # Soek funksie
            if search and search not in act.lower() and search not in ven.lower(): continue

            found_count += 1
            
            # Die "Card" ontwerp
            st.markdown(f"""
                <div class="event-card">
                    <div class="event-title">{act} {f'(U/{age})' if age else ''}</div>
                    <div class="event-info">📅 {date} &nbsp;&nbsp; | &nbsp;&nbsp; 📍 {ven.upper()}</div>
                    {f'<div class="event-detail">ℹ️ {info}</div>' if info else ''}
                </div>
                """, unsafe_allow_html=True)
        except:
            continue
            
    if found_count == 0:
        st.info("Geen aktiwiteite gevind vir jou soektog nie.")
else:
    st.warning("Data word tans vanaf Google gelaai...")

# --- FOOTER ---
st.markdown("---")
if st.button("🔄 Verfris Inligting"):
    st.cache_data.clear()
    st.rerun()

st.caption("© 2026 Laerskool Midstream College Primary | Digital Communication Hub")
