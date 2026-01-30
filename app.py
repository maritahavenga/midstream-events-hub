import streamlit as st
import pandas as pd
import requests
import io

# 1. Page Config moet HEEL BO wees
st.set_page_config(page_title="LMCP Hub", layout="centered")

# 2. Eenvoudige Styl sonder snaakse karakters
st.markdown("""
<style>
    .nav-bar {
        background-color: #800000;
        color: white;
        padding: 20px;
        text-align: center;
        border-radius: 10px;
    }
    .card {
        background: white;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #800000;
        margin-top: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="nav-bar"><h1>MIDSTREAM COLLEGE</h1><p>PRIMARY EVENT HUB</p></div>', unsafe_allow_html=True)

# 3. Direkte Data Pad
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?output=csv"

def get_data():
    try:
        r = requests.get(URL, timeout=10)
        return pd.read_csv(io.StringIO(r.content.decode('utf-8')))
    except:
        return None

df = get_data()

if df is not None:
    st.success("Connection to Google Active!")
    # Toets om te sien of hy kolomme lees
    st.write("Found", len(df), "events.")
    
    # Vertoon net die eerste 5 om te toets
    for i in range(min(5, len(df))):
        row = df.iloc[i]
        st.markdown(f"""
        <div class="card">
            <b>{row.iloc[3]}</b><br>
            📅 {row.iloc[5]} | 📍 {row.iloc[6]}
        </div>
        """, unsafe_allow_html=True)
else:
    st.error("Google is still blocking the connection. Waiting...")

if st.button("Refresh"):
    st.rerun()
