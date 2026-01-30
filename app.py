import streamlit as st
import pandas as pd
import requests, io, datetime

st.set_page_config(page_title="LMCP Hub", layout="centered")

# --- BANNER ---
st.markdown("<h1 style='text-align:center;color:#800000;'>LAERSKOOL MIDSTREAM COLLEGE PRIMARY</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:#008080;font-weight:bold;text-align:center;'>Digital Event Hub</p>", unsafe_allow_html=True)

# Die skakel vanaf jou foto
U = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?output=csv"

@st.cache_data(ttl=1)
def ld():
    try:
        # Ons voeg 'n tydstempel by om Google te dwing om vars data te stuur
        r = requests.get(f"{U}&nocache={datetime.datetime.now().timestamp()}", timeout=15)
        if r.status_code == 200:
            # Ons lees die data rou in
            data = r.content.decode('utf-8')
            df = pd.read_csv(io.StringIO(data), dtype=str).fillna("")
            return df
        return pd.DataFrame()
    except:
        return pd.DataFrame()

df = ld()

# As daar data is, wys dit in kaarte
if not df.empty and len(df.columns) > 5:
    st.markdown("---")
    for _, r in df.iterrows():
        try:
            # Ons gebruik die posisie van die kolomme (0, 1, 2, 3...)
            # Kolom 4 is indeks 3, Kolom 6 is indeks 5, ens.
            act = str(r.iloc[3]).strip()  # Activity
            date = str(r.iloc[5]).strip() # Date
            ven = str(r.iloc[6]).strip()  # Venue
            age = str(r.iloc[11]).replace(".0", "").strip() # Age/Grade

            if len(act) < 2 or act.lower() == "nan":
                continue

            st.markdown(f"""
            <div style="background:white; padding:20px; border-radius:12px; border-left:10px solid #800000; margin-bottom:15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); font-family:sans-serif;">
                <b style="color:#800000; font-size:1.2rem;">{act} (Gr/U{age})</b><br>
                <span style="color:#555;">📅 {date}</span><br>
                <b style="color:#008080;">📍 {ven.upper()}</b>
            </div>
            """, unsafe_allow_html=True)
        except:
            continue
else:
    st.warning("🔄 Besig om konneksie te verfris... Maak seker die Google Sheet het ten minste een ry data onder die opskrifte.")
    if st.button("Herlaai Nou"):
        st.cache_data.clear()
        st.rerun()

st.markdown("<br><br><center style='color:#999;font-size:0.8rem;'>LMCP Event Hub 2026</center>", unsafe_allow_html=True)
