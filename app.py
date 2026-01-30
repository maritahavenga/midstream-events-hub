import streamlit as st
import pandas as pd
import requests, io, datetime

st.set_page_config(page_title="LMCP Hub", layout="centered")

# --- BANNER ---
st.markdown("<h1 style='text-align:center;color:#800000;'>LAERSKOOL MIDSTREAM COLLEGE PRIMARY</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:#008080;font-weight:bold;text-align:center;'>Digital Event Hub</p>", unsafe_allow_html=True)

# Die CSV skakel vanaf jou foto
U = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?output=csv"

@st.cache_data(ttl=1)
def ld():
    try:
        r = requests.get(f"{U}&nocache={datetime.datetime.now().timestamp()}", timeout=15)
        if r.status_code == 200:
            # Ons lees die data en ignoreer leë rye aan die begin
            df = pd.read_csv(io.StringIO(r.content.decode('utf-8')), dtype=str).fillna("")
            return df
        return pd.DataFrame()
    except:
        return pd.DataFrame()

df = ld()

if not df.empty:
    # Ons gaan deur elke ry en kyk of daar werklik data is
    found_data = False
    for _, r in df.iterrows():
        try:
            # Ons gebruik die kolomme presies soos op jou foto
            act = str(r.iloc[3]).strip()  # Kolom D: Activity/Subject
            date = str(r.iloc[5]).strip() # Kolom F: Date
            ven = str(r.iloc[6]).strip()  # Kolom G: Venue
            info = str(r.iloc[10]).strip() # Kolom K: Information

            # As die aktiwiteit leeg is, ignoreer hierdie ry
            if len(act) < 2 or act.lower() == "nan":
                continue
            
            found_data = True
            st.markdown(f"""
            <div style="background:white; padding:20px; border-radius:12px; border-left:10px solid #800000; margin-bottom:15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); font-family:sans-serif;">
                <b style="color:#800000; font-size:1.2rem;">{act}</b><br>
                <span style="color:#555;">📅 {date}</span><br>
                <b style="color:#008080;">📍 {ven.upper()}</b><br>
                <p style="font-size:0.9rem; color:#333; margin-top:10px;">{info}</p>
            </div>
            """, unsafe_allow_html=True)
        except:
            continue
    
    if not found_data:
        st.warning("⚠️ Die konneksie werk, maar dit lyk of die rye in jou Sheet leeg is. Vul asseblief data in Kolom D, F en G in.")
else:
    st.info("🔄 Besig om data vanaf Google te verfris... Maak seker die 'Upcoming' tab is die een wat gepubliseer is.")

if st.button("Herlaai Nou"):
    st.cache_data.clear()
    st.rerun()
