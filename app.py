import streamlit as st
import pandas as pd
import requests
import io
import re
import pytz
from datetime import datetime
import streamlit.components.v1 as v1
from streamlit_autorefresh import st_autorefresh

# ================= PAGE =================
st.set_page_config(page_title="LMCP Hub", layout="centered")
st_autorefresh(interval=120000, key="r")

DATA_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/"
    "pub?gid=37057995&single=true&output=csv"
)

# ================= HELPERS =================
def cl(v):
    return str(v).replace(".0", "").replace("nan", "").strip()

def tr(text, activity):
    text = str(text)
    activity = str(activity).lower()

    if any(x in activity for x in ["eat", "ht", "hooftaal", "eerste"]):
        return "Afrikaans Eerste Addisionele Taal" if "eat" in activity else "Afrikaans Hooftaal"

    repl = {
        "Saal": "Hall",
        "Veld": "Field",
        "Atletiek": "Athletics",
        "Wiskunde": "Math",
        " G ": " Girls ",
        " G": " Girls"
    }

    for k, v in repl.items():
        text = re.sub(rf"\b{k}\b", v, text, flags=re.IGNORECASE)

    return text

def c_a(name):
    name = str(name).lower()

    sports = [
        "athletics", "atletiek",
        "hockey",
        "rugby",
        "netball", "netbal",
        "tennis"
    ]

    for s in sports:
        if s in name:
            return s.capitalize().replace("Netbal", "Netball").replace("Atletiek", "Athletics")

    if any(x in name for x in ["eat", "ht", "hooftaal", "eerste"]):
        return "Afrikaans EAT" if "eat" in name else "Afrikaans HT"

    return name.capitalize()

# ================= DATA LOAD =================
@st.cache_data(ttl=15)
def load_data():
    try:
        response = requests.get(DATA_URL, timeout=8)
        csv_text = response.content.decode("utf-8")
        df = pd.read_csv(io.StringIO(csv_text), dtype=str)
        return df.fillna("")
    except Exception:
        return pd.DataFrame()

df = load_data()

# ================= UI =================
if df.empty:
    st.error("Data could not be loaded.")
    st.stop()

st.markdown(
    "<div style='ba
