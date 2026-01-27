import streamlit as st
st.set_page_config(page_title="LMCP Event Hub", layout="centered")

import pandas as pd
import re
from datetime import datetime, timedelta
import requests, io, urllib.parse

today = datetime.now().date()

# =========================
# STYLES
# =========================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700&display=swap');

html, body, .stApp {
    margin:0;
    padding:0;
    background:#008080;
    font-family:'Source Sans 3', sans-serif;
}

#MainMenu, footer, header {visibility:hidden;}
.block-container {
    max-width:760px;
    padding-top:0 !important;
}

.navbar {
    position:fixed;
    top:0; left:0; right:0;
    background:white;
    border-bottom:4px solid #800000;
    z-index:9999;
}
.navbar img {
    width:100%;
    max-height:130px;
    object-fit:contain;
}

.header-green {
    margin-top:130px;
    background:#008080;
    color:white;
    text-align:center;
    padding:18px;
    font-weight:700;
    font-size:1.35rem;
}

.filter-box {
    background:white;
    padding:22px;
    border-radius:18px;
    margin:28px 0;
    box-shadow:0 4px 14px rgba(0,0,0,0.18);
}

.card {
    background:white;
    padding:34px;
    border-radius:20px;
    border-left:10px solid #800000;
    margin-bottom:40px;
    box-shadow:0 6px 18px rgba(0,0,0,0.18);
}

.card-date {color:#666; font-size:0.9rem;}
.card-title {color:#800000; font-size:1.45rem; font-weight:700;}

.venue a {
    color:#333;
    text-decoration:none;
}
.venue a:hover {text-decoration:underline;}

.team {
    background:#fff3f3;
    padding:16px;
    border-radius:12px;
    margin-top:18px;
    font-size:0.95rem;
}

.btn-row {
    display:flex;
    flex-wrap:wrap;
    gap:14px;
    margin-top:22px;
}
.btn {
    background:#800000;
    color:white;
    padding:12px 26px;
    border-radius:14px;
    font-weight:600;
    text-decoration:none;
}
.btn:hover {opacity:0.9;}
</style>

<div class="navbar">
    <img src="https://midstream-primary.co.za/wp-content/uploads/2021/09/MCP-1.png">
</div>

<div class="header-green">
Laerskool Midstream College Primary — Event Hub
</div>
""", unsafe_allow_html=True)

# =========================
# DATA
# =========================
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?gid=0&single=true&output=csv"
URL_REGEX = re.compile(r"(https?://[^\s<>\"']+)")

@st.cache_data(ttl=120)
def load_data():
    r = requests.get(DATA_URL, timeout=10)
    df = pd.read_csv(io.StringIO(r.text))
    df.columns = [c.strip().lower() for c in df.columns]

    def parse_date(x):
        if pd.isna(x):
            return pd.NaT
        s = str(x)
        if not re.search(r"\d{4}", s):
            s += f" {datetime.now().year}"
        return pd.to_datetime(s, dayfirst=True, errors="coerce")

    df["date_fixed"] = df["date"].apply(parse_date)
    return df

df = load_data()

# =========================
# FILTERS
# =========================
with st.container():
    st.markdown('<div class="filter-box">', unsafe_allow_html=True)

    activities = sorted(df["activity"].dropna().astype(str).unique())
    ages = sorted(df["age"].dropna().astype(str).unique()) if "age" in df else []
    categories = sorted(df["category"].dropna().astype(str).unique()) if "category" in df else []

    activity_filter = st.multiselect("Activity", activities)
    age_filter = st.multiselect("Age Group", ages)
    category_filter = st.multiselect("Category", categories)

    col1, col2 = st.columns(2)
    if "range" not in st.session_state:
        st.session_state.range = "7"

    if col1.button("All Events"):
        st.session_state.range = "all"
    if col2.button("Next 7 Days"):
        st.session_state.range = "7"

    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# APPLY FILTERS
# =========================
df = df[df["date_fixed"].isna() | (df["date_fixed"].dt.date >= today)]

if st.session_state.range == "7":
    df = df[df["date_fixed"].isna() | (df["date_fixed"].dt.date <= today + timedelta(days=7))]

if activity_filter:
    df = df[df["activity"].astype(str).isin(activity_filter)]
if age_filter:
    df = df[df["age"].astype(str).isin(age_filter)]
if category_filter:
    df = df[df["category"].astype(str).isin(category_filter)]

df = df.sort_values("date_fixed", na_position="last")

# =========================
# CARDS
# =========================
for _, r in df.iterrows():
    date_str = r["date_fixed"].strftime("%d %B %Y") if pd.notna(r["date_fixed"]) else "TBA"
    venue = str(r.get("venue", ""))
    maps = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote_plus(venue)}"

    buttons = []
    for label in ["programme", "confirm"]:
        raw = "" if pd.isna(r.get(label)) else str(r.get(label))
        for u in URL_REGEX.findall(raw):
            buttons.append(f'<a class="btn" href="{u}" target="_blank">{label.upper()}</a>')

    team_text = ""
    if pd.notna(r.get("team")):
        team_text = re.sub(URL_REGEX, "", str(r.get("team"))).strip()

    st.markdown(f"""
    <div class="card">
        <div class="card-date">📅 {date_str}</div>
        <div class="card-title">{r.get("activity","")} {r.get("age","")}</div>
        <div class="venue"><a href="{maps}" target="_blank">📍 {venue}</a></div>
        {f'<div class="team"><b>Teams</b><br>{team_text}</div>' if team_text else ''}
        {f'<div class="btn-row">{"".join(buttons)}</div>' if buttons else ''}
    </div>
    """, unsafe_allow_html=True)

# =========================
# FOOTER
# =========================
st.markdown("""
<div style="background:#800000;color:white;text-align:center;padding:18px;margin-top:50px;font-size:0.85rem;">
Midstream College Primary · info@midstreamprimary.co.za · 012 940 2222
</div>
""", unsafe_allow_html=True)
