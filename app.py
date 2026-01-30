import streamlit as st
import pandas as pd
import requests, io
import random

st.set_page_config(page_title="LMCP Hub", layout="centered")

# --- STYLE ---
st.markdown("""
    <style>
    .event-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        border-left: 10px solid #800000;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        margin-bottom: 15px;
    }
    .stApp { background-color: #f4f4f4; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center; color:#800000;'>LMCP EVENT HUB</h1>", unsafe_allow_html=True)

# ONS VOEG 'N RANDOM NOMMER BY SODAT GOOGLE NIE DIE OU DATA WYS NIE
cache_buster = random.randint(1, 100000)
URL = f"https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?output=csv&x={cache_buster}"

def load_now():
    try:
        # Ons vra Google baie direk vir die data
        r = requests.get(URL, timeout=15)
        if r.status_code == 200:
            df = pd.read_csv(io.StringIO(r.content.decode('utf-8')), dtype=str).fillna("")
            return df
    except:
        return None
    return None

df = load_now()

if df is not None and not df.empty:
    st.success("Data suksesvol gelaai!")
    for i in range(len(df)):
        try:
            row = df.iloc[i]
            act = str(row.iloc[3]).strip()  # Activity
            date = str(row.iloc[5]).strip() # Date
            ven = str(row.iloc[6]).strip()  # Venue
            
            if len(act) > 2 and "activity" not in act.lower():
                st.markdown(f"""
                    <div class="event-card">
                        <b style="color:#800000; font-size:1.2rem;">{act}</b><br>
                        <span style="color:#008080;"><b>📅 {date}</b></span><br>
                        <span style="color:#555;">📍 {ven}</span>
                    </div>
                    """, unsafe_allow_html=True)
        except:
            continue
else:
    st.warning("Google is tans besig om die data voor te berei. Verfris asseblief die bladsy oor 10 sekondes.")
    if st.button("Probeer weer"):
        st.rerun()
