import streamlit as st
import pandas as pd
import requests, io

st.set_page_config(page_title="LMCP Hub", layout="centered")

# --- CSS VIR 'N SKOON LOOK ---
st.markdown("""
    <style>
    .stApp { background-color: #f0f2f6; }
    .event-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 10px solid #800000;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
    }
    .event-title { color: #800000; font-size: 1.2rem; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center; color:#800000;'>LMCP EVENT HUB</h1>", unsafe_allow_html=True)

# DIE MEES STABIELE SKAKEL TIPE
SHEET_ID = "1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8"
GID = "37057995"
# Ons gebruik die 'tq' (Query) pad - dit is blitsvinnig
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid={GID}"

@st.cache_data(ttl=5) # Die app sal die data vir 5 sekondes onthou voor hy weer vra
def get_data():
    try:
        response = requests.get(URL, timeout=5)
        if response.status_code == 200:
            return pd.read_csv(io.StringIO(response.content.decode('utf-8')), dtype=str).fillna("")
    except:
        return None
    return None

df = get_data()

if df is not None and not df.empty:
    st.success("✅ Inligting Opgedateer")
    
    # Ons gaan deur elke ry
    for i in range(len(df)):
        try:
            # Gebruik kolom-nommers (D=3, F=5, G=6)
            row = df.iloc[i]
            act = str(row.iloc[3]).strip()
            date = str(row.iloc[5]).strip()
            ven = str(row.iloc[6]).strip()

            if len(act) > 2 and "activity" not in act.lower():
                st.markdown(f"""
                    <div class="event-card">
                        <div class="event-title">{act}</div>
                        <div style="color:#008080;"><b>📅 {date}</b></div>
                        <div style="color:#555;">📍 {ven}</div>
                    </div>
                    """, unsafe_allow_html=True)
        except:
            continue
else:
    st.error("Kon nie die data by Google kry nie.")
    st.info("Wag 10 sekondes en probeer weer. Google is soms besig.")
    if st.button("Probeer nou weer"):
        st.cache_data.clear()
        st.rerun()
