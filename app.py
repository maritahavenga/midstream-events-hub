import streamlit as st
import pandas as pd
import requests, io, re, pytz
from datetime import datetime
import streamlit.components.v1 as v1
from streamlit_autorefresh import st_autorefresh

# ---------------- PAGE ----------------
st.set_page_config(page_title="LMCP Hub", layout="centered")
st_autorefresh(interval=120000, key="r")

U = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

# ---------------- HELPERS ----------------
def cl(v):
    return str(v).replace(".0", "").replace("nan", "").strip()

def tr(t, a):
    t = str(t)
    a = str(a)

    if re.search(r'(?i)\b(EAT|HT|Hooftaal|Eerste)\b', a):
        return "Afrikaans " + (
            "Eerste Addisionele Taal"
            if "eat" in a.lower() or "eerste" in a.lower()
            else "Hooftaal"
        )

    replacements = {
        "Saal": "Hall",
        "Veld": "Field",
        "Atletiek": "Athletics",
        "Wiskunde": "Math",
        " G ": " Girls ",
        " G": " Girls"
    }

    for k, v in replacements.items():
        t = re.sub(rf"\b{k}\b", v, t, flags=re.IGNORECASE)

    return t

def c_a(n):
    n = str(n).lower()

    sports = [
        "athletics", "atletiek",
        "hockey",
        "rugby",
        "netball", "netbal",
        "tennis"
    ]

    for s in sports:
        if s in n:
            return s.capitalize().replace("Netbal", "Netball").replace("Atletiek", "Athletics")

    if any(x in n for x in ["eat", "ht", "hooftaal", "eerste"]):
        return "Afrikaans " + (
            "Eerste Addisionele Taal"
            if "eat" in n or "eerste" in n
            else "Hooftaal"
        )

    return n.capitalize()

# ---------------- DATA ----------------
@st.cache_data(ttl=10)
def ld():
    try:
        r = requests.get(f"{U}&cb={datetime.now().timestamp()}", timeout=5)
        return pd.read_csv(io.StringIO(r.content.decode("utf-8")), dtype=str).fillna("")
