import streamlit as st
import pandas as pd
import requests, io

st.set_page_config(page_title="LMCP Hub", layout="wide")

# Skakel na jou sheet (die ID is uit jou foto)
ID = "1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8"
URL = f"https://docs.google.com/spreadsheets/d/{ID}/export?format=csv"

st.title("LAERSKOOL MIDSTREAM COLLEGE PRIMARY")

# Probeer net die data laai sonder fancy boodskappe
try:
    r = requests.get(URL)
    df = pd.read_csv(io.StringIO(r.content.decode('utf-8')))
    
    st.write("### Aktiewe Inligting:")
    # Hierdie wys die rou data van jou Google Sheet
    st.dataframe(df)
    
except Exception as e:
    st.write("Wag tans vir Google...")
    st.write(e)
