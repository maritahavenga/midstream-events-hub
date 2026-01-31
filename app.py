import re
import streamlit as st
import pandas as pd

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="LMCP Event Hub", layout="wide")

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

# =============================
# STYLING (modern, less “robot”)
# =============================
st.markdown("""
<style>
    .stApp { background: #f6f7fb; }
    .topbar {
        background: linear-gradient(90deg, #800000, #a00000);
        color: white;
        padding: 18px 22px;
        border-radius: 16px;
        margin-bottom: 14px;
        box-shadow: 0 10px 18px rgba(0,0,0,0.10);
    }
    .topbar h1 { margin: 0; font-size: 22px; letter-spacing: 0.5px; }
    .topbar p { margin: 2px 0 0; opacity: 0.95; }

    .panel {
        background: white;
        border-radius: 16px;
        padding: 14px 16px;
        box-shadow: 0 6px 16px rgba(0,0,0,0.08);
        margin-bottom: 12px;
        border: 1px solid rgba(0,0,0,0.04);
    }
    .pill {
        display: inline-block;
        padding: 6px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 600;
        background: rgba(128,0,0,0.08);
        color: #800000;
        margin-right: 8px;
    }
    .card {
        background: white;
        border-radius: 18px;
        padding: 16px 16px 14px;
        border: 1px solid rgba(0,0,0,0.05);
        box-shadow: 0 10px 18px rgba(0,0,0,0.08);
        margin-bottom: 12px;
    }
    .title { font-size: 18px; font-weight: 800; margin: 0; }
    .sub { font-size: 13px; color: #177; font-weight: 700; margin-top: 6px; }
    .meta { color: #555; font-size: 14px; margin-top: 8px; line-height: 1.4; }
    .info {
        background: #f1f3f6;
        padding: 10px 12px;
        border-radius: 12px;
        margin-top: 10px;
        border-left: 4px solid #177;
        font-size: 14px;
    }
    .smallnote { font-size: 12px; color: #777; margin-top: 8px; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="topbar">
  <h1>MIDSTREAM COLLEGE</h1>
  <p>Primary Event Hub</p>
</div>
""", unsafe_allow_html=True)

# =============================
# HELPERS
# =============================
U_TO_GR = {
    "U7": "Gr 1",
    "U8": "Gr 2",
    "U9": "Gr 3",
    "U10": "Gr 4",
    "U11": "Gr 5",
    "U12": "Gr 6",
    "U13": "Gr 7",
}
GR_TO_U = {v: k for k, v in U_TO_GR.items()}

def safe_str(x) -> str:
    return "" if pd.isna(x) else str(x).strip()

def normalize_category(cat: str) -> str:
    c = safe_str(cat).lower()
    if "sport" in c:
        return "Sport"
    if "cultur" in c or "culture" in c:
        return "Culture"
    if "academ" in c:
        return "Academics"
    # fallback: guess academics if not explicitly sport/culture
    return "Academics"

def normalize_afrikaans_subject(text: str) -> str:
    t = safe_str(text)

    # Afrikaans EAT -> Afrikaans Eerste Addisionele Taal
    if re.search(r"\bafrikaans\b", t, flags=re.I) and re.search(r"\beat\b", t, flags=re.I):
        # keep other text but ensure the Afrikaans part is correct
        t = re.sub(r"Afrikaans\s*EAT", "Afrikaans Eerste Addisionele Taal", t, flags=re.I)

    # Afrikaans HT -> Afrikaans Hooftaal (as per your required spelling)
    if re.search(r"\bafrikaans\b", t, flags=re.I) and re.search(r"\bht\b", t, flags=re.I):
        t = re.sub(r"Afrikaans\s*HT", "Afrikaans Hooftaal", t, flags=re.I)

    return t

def is_afrikaans_activity(text: str) -> bool:
    t = safe_str(text)
    return ("Afrikaans" in t) and (re.search(r"\b(EAT|HT)\b", t, flags=re.I) is not None)

def parse_under(value: str) -> str:
    """Convert age
