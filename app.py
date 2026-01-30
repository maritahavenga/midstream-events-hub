import streamlit as st
import pandas as pd
import requests, io

# 1. Stel die bladsy op heel eerste
st.set_page_config(page_title="LMCP Event Hub", layout="centered")

# 2. Dwing die Styl (CSS) - Ons sit dit heel bo sodat dit ALTYD laai
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
    .event-title { color: #800000; font-size: 1.3rem; font-weight: bold; }
    .btn-map {
        display: inline-block;
        background-color: #008080;
        color: white !important;
        padding: 8px 15px;
        border-radius: 8px;
        text-decoration: none;
        font-size: 0.8rem;
        margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# BANNER
st.markdown("""
    <div class="header-banner">
        <h1 style='margin:0; font-family:sans-serif;'>MIDSTREAM COLLEGE</h1>
        <p style='margin:0; opacity:0.9; font-family:sans-serif;'>Digital Event Hub</p>
    </div>
    """, unsafe_allow_html=True)

# 3. DATA PAD
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?output=csv"

@st.cache_data(ttl=5)
def fetch_data():
    try:
        r = requests.get(URL, timeout=10)
        return pd.read_csv(io.StringIO(r.content.decode('utf-8')), dtype=str).fillna("")
    except:
        return None

df = fetch_data()

st.write("") 

if df is not None and not df.empty:
    # Die soekbalk is nou terug
    search = st.text_input("🔍 Soek aktiwiteit...", "")
    
    for i in range(len(df)):
        try:
            row = df.iloc[i]
            # Ons gebruik weer die kolom-nommers (dis veiliger teen spelfoute)
            # A=0, B=1, C=2, D=3 (Activity), E=4, F=5 (Date), G=6 (Venue), H=7 (Map)
            act = str(row.iloc[3]).strip()
            date = str(row.iloc[5]).strip()
            ven = str(row.iloc[6]).strip()
            
            # Kyk of daar 'n skakel in kolom H (index 7) is
            map_url = ""
            if len(row) > 7:
                map_url = str(row.iloc[7]).strip()

            if len(act) > 2 and "activity" not in act.lower():
                if search.lower() in act.lower() or search.lower() in ven.lower():
                    st.markdown(f"""
                        <div class="event-card">
                            <div class="event-title">{act}</div>
                            <div style="color:#008080; font-weight:bold; font-family:sans-serif;">📅 {date}</div>
                            <div style="color:#555; font-family:sans-serif;">📍 {ven}</div>
                            {f'<a href="{map_url}" target="_blank" class="btn-map">📍 KAART</a>' if "http" in map_url else ""}
                        </div>
                        """, unsafe_allow_html=True)
        except:
            continue
else:
    st.error("Kon nie die data laai nie. Herlaai asseblief.")

# DIE KNOPPIE IS TERUG
st.markdown("---")
if st.button("🔄 Verfris Inligting"):
    st.cache_data.clear()
    st.rerun()
