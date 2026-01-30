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
    r = str(a).strip()
    t = str(t).replace(" G ", " Girls ").replace(" G", " Girls")

    if re.search(r'(?i)\b(EAT|HT|Hooftaal|Eerste)\b', r):
        return "Afrikaans " + (
            "Eerste Addisionele Taal"
            if "eat" in r.lower() or "eerste" in r.lower()
            else "Hooftaal"
        )

    d = {
        "Saal": "Hall",
        "Veld": "Field",
        "Atletiek": "Athletics",
        "Wiskunde": "Math"
    }
    for k, v in d.items():
        t = re.sub(rf'\b{k}\b', v, t, flags=re.IGNORECASE)

    return t

def c_a(n):
    n = n.lower()
    for x in ["]()
