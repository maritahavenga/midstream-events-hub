import streamlit as st
import pandas as pd
import requests, io

st.set_page_config(page_title="LMCP Event Hub", layout="centered")

# --- DIE LOOK ---
st.markdown("""
    <style>
    .stApp { background-color: #f7f7f7; }
    .card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        border-left: 10px solid #800000;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center; color:#800000;'>LMCP EVENT HUB</h1>", unsafe_allow_html=True)

# ONS GEBRUIK DIE PUBLIEKE CSV SKAKEL WAT JY VROEËR GESTUUR HET
# Hierdie skakel het gewerk in jou browser, so dit MOET werk in die app.
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?output=csv"

def load_data():
    try:
        # Ons gebruik 'n 'header' om soos 'n menslike browser te klink
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(URL, headers=headers, timeout=15)
        if r.status_code == 200:
            content = r.content.decode('utf-8')
            return pd.read_csv(io.StringIO(content), dtype=str).fillna("")
    except Exception as e:
        return None
    return None

df = load_data()

if df is not None and not df.empty:
    st.success("✅ Inligting is opgedateer")
    
    # Ons begin kyk vanaf ry 1 (om opskrifte oor te slaan indien nodig)
    for i in range(len(df)):
        try:
            row = df.iloc[i]
            # Ons soek die data in kolomme 3 (Activity), 5 (Date), 6 (Venue)
            act = str(row.iloc[3]).strip()
            date = str(row.iloc[5]).strip()
            ven = str(row.iloc[6]).strip()

            if len(act) > 2 and "activity" not in act.lower():
                st.markdown(f"""
                    <div class="card">
                        <b style="color:#800000; font-size:1.2rem;">{act}</b><br>
                        <span style="color:#008080;"><b>📅 {date}</b></span><br>
                        <span style="color:#555;">📍 {ven}</span>
                    </div>
                    """, unsafe_allow_html=True)
        except:
            continue
else:
    st.error("Google se 'Publish' skakel is tans traag.")
    st.info("Kopieer hierdie skakel en plak dit in jou browser om te kyk of dit werk:")
    st.code(URL)
    if st.button("Probeer weer"):
        st.rerun()
