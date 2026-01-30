import streamlit as st
import pandas as pd
import requests, io

st.set_page_config(page_title="LMCP Event Hub", layout="centered")

# Skool Kleure en Styl
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .event-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        border-left: 10px solid #800000;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        margin-bottom: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center; color:#800000;'>LAERSKOOL MIDSTREAM COLLEGE</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#008080; font-weight:bold;'>PRIMARY EVENT HUB</p>", unsafe_allow_html=True)

# JOU WERKende SKAKEL
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?output=csv"

def laai_data():
    try:
        # Ons sê vir Google ons is 'n browser (User-Agent)
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(URL, headers=headers, timeout=15)
        if r.status_code == 200:
            df = pd.read_csv(io.StringIO(r.content.decode('utf-8')), dtype=str).fillna("")
            return df
    except:
        return None
    return None

df = laai_data()

st.markdown("---")

if df is not None and not df.empty:
    found = False
    for i in range(len(df)):
        try:
            row = df.iloc[i]
            # Aktiwiteit is in Kolom D (Index 3)
            act = str(row.iloc[3]).strip()
            # Datum is in Kolom F (Index 5)
            date = str(row.iloc[5]).strip()
            # Plek is in Kolom G (Index 6)
            ven = str(row.iloc[6]).strip()

            if len(act) > 2 and "activity" not in act.lower():
                found = True
                st.markdown(f"""
                <div class="event-card">
                    <b style="color:#800000; font-size:1.2rem;">{act}</b><br>
                    <span style="color:#008080;"><b>📅 {date}</b></span><br>
                    <span style="color:#555;">📍 {ven}</span>
                </div>
                """, unsafe_allow_html=True)
        except:
            continue
    
    if not found:
        st.info("Die konneksie is reg, maar daar is tans geen aktiwiteite in die sheet nie.")
else:
    st.warning("Google is tans besig om die inligting te verwerk. Verfris asseblief oor 'n paar sekondes.")

if st.button("Herlaai"):
    st.rerun()
