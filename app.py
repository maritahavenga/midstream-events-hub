
import streamlit as st
import pandas as pd
import requests, io, datetime

st.set_page_config(page_title="LMCP Hub", layout="centered")

# --- BANNER ---
st.markdown("<h1 style='text-align:center;color:#800000;'>LAERSKOOL MIDSTREAM COLLEGE PRIMARY</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:#008080;font-weight:bold;'>Digital Event Hub</p>", unsafe_allow_html=True)

# JOU SKAKEL VANAF DIE FOTO
U = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?output=csv"

@st.cache_data(ttl=1)
def ld():
    try:
        r = requests.get(f"{U}&v={datetime.datetime.now().timestamp()}", timeout=15)
        df = pd.read_csv(io.StringIO(r.content.decode('utf-8')), dtype=str).fillna("")
        return df
    except: return pd.DataFrame()

df = ld()

if not df.empty and len(df.columns) > 5:
    # ONS GEBRUIK KOLOM-NOMMERS (0 is Timestamp, 3 is Activity, 5 is Date, 6 is Venue, 11 is Age)
    st.write("### Aktiewe Events")
    
    for _, r in df.iterrows():
        try:
            act = str(r.iloc[3])  # Activity/Subject Name
            date = str(r.iloc[5]) # Date / Due Date
            ven = str(r.iloc[6])  # Venue
            age = str(r.iloc[11]).replace(".0", "") # Age/Grade
            
            # As daar nie 'n aktiwiteit is nie, slaan die ry oor
            if not act or act == "nan": continue

            st.markdown(f"""
            <div style="background:white; padding:15px; border-radius:10px; border-left:8px solid #800000; margin-bottom:15px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                <b style="color:#800000; font-size:1.1rem;">{act} (Gr/U{age})</b><br>
                📅 {date} | 📍 {ven}
            </div>
            """, unsafe_allow_html=True)
        except: continue
else:
    st.info("🔄 Besig om data vanaf Google te trek... Maak seker die eerste ry in jou sheet het data.")
    if st.button("Herlaai Nou"):
        st.cache_data.clear()
        st.rerun()
