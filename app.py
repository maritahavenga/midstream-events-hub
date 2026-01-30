import streamlit as st
import pandas as pd
import requests, io, time

st.set_page_config(page_title="LMCP Hub", layout="centered")

# BANNER
st.markdown("<h1 style='text-align:center;color:#800000;'>LAERSKOOL MIDSTREAM COLLEGE PRIMARY</h1>", unsafe_allow_html=True)

# JOU DIREKTE SHEET ID
SID = "1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8"
# Die gviz skakel is die mees betroubare pad
U = f"https://docs.google.com/spreadsheets/d/{SID}/gviz/tq?tqx=out:csv"

@st.cache_data(ttl=1)
def load_data():
    try:
        r = requests.get(U, timeout=10)
        if r.status_code == 200:
            df = pd.read_csv(io.StringIO(r.content.decode('utf-8')), dtype=str).fillna("")
            return df
        return None
    except:
        return None

df = load_data()

if df is not None and not df.empty:
    st.success(f"✅ Konneksie suksesvol! {len(df)} rye gevind.")
    
    for _, r in df.iterrows():
        try:
            # Ons gebruik kolomme gebaseer op jou nuutste foto (D, F, G)
            act = str(r.iloc[3]).strip()  # Activity
            date = str(r.iloc[5]).strip() # Date
            ven = str(r.iloc[6]).strip()  # Venue
            
            if len(act) < 2 or act.lower() == "nan":
                continue

            st.markdown(f"""
            <div style="background:white; padding:15px; border-radius:10px; border-left:10px solid #800000; margin-bottom:15px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                <b style="color:#800000; font-size:1.1rem;">{act}</b><br>
                📅 {date} | 📍 {ven}
            </div>
            """, unsafe_allow_html=True)
        except:
            continue
else:
    st.info("🔄 Google is besig om die nuwe tab-posisie te verwerk. Verfris die bladsy oor 'n minuut.")
    if st.button("Herlaai Nou"):
        st.cache_data.clear()
        st.rerun()
