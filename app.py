import streamlit as st
import pandas as pd

st.set_page_config(page_title="LMCP Hub", layout="centered")

# --- STYL ---
st.markdown("""
    <style>
    .stApp { background-color: #f4f4f4; font-family: sans-serif; }
    .header { background: #800000; color: white; padding: 25px; text-align: center; border-radius: 0 0 20px 20px; margin-top: -60px; }
    .card { background: white; padding: 18px; border-radius: 12px; border-left: 8px solid #800000; margin-bottom: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="header"><h1>MIDSTREAM EVENT HUB</h1></div>', unsafe_allow_html=True)

# Direkte skakel
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?output=csv"

try:
    # Ons gebruik pandas direk om die URL te lees
    df = pd.read_csv(URL)
    
    if not df.empty:
        st.write("") # Spasie
        search = st.text_input("🔍 Soek aktiwiteit...", "")
        
        for i in range(len(df)):
            row = df.iloc[i]
            act = str(row.iloc[3]).strip() # Kolom D
            date = str(row.iloc[5]).strip() # Kolom F
            ven = str(row.iloc[6]).strip() # Kolom G
            
            if len(act) > 2 and "activity" not in act.lower():
                if search.lower() in act.lower() or search.lower() in ven.lower():
                    st.markdown(f"""
                        <div class="card">
                            <b style="color:#800000; font-size:1.1rem;">{act}</b><br>
                            <span style="color:#008080;"><b>📅 {date}</b></span><br>
                            <span style="color:#555;">📍 {ven}</span>
                        </div>
                        """, unsafe_allow_html=True)
except Exception as e:
    st.warning("Google verfris tans die konneksie. Die inligting sal binnekort weer verskyn.")
