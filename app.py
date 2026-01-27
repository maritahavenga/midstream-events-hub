import streamlit as st
st.set_page_config(page_title="LMCP Event Hub", layout="centered")

import pandas as pd
import re
from datetime import datetime, timedelta
import requests, io, urllib.parse

# =========================
# CONSTANTS
# =========================
DATA_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-"
    "YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub"
    "?gid=0&single=true&output=csv"
)

URL_REGEX = re.compile(r"(https?://[^\s<>\"']+)")
TODAY = datetime.now().date()

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
    max-width:820px;
    padding-top:0rem !important;
    margin-top:-1rem;
}

.navbar {
    background:white;
    border-bottom:5px solid #800000;
}

.navbar img {
    width:100%;
    max-height:140px;
    object-fit:contain;
}

.header {
    background:#008080;
    color:white;
    text-align:center;
    padding:20px;
    font-size:1.4rem;
    font-weight:700;
}

.filter-box {
    background:white;
    padding:26px;
    border-radius:20px;
    margin:26px 0;
    box-shadow:0 6px 18px rgba(0,0,0,0.18);
}

.card {
    background:white;
    padding:38px;
    border-radius:22px;
    border-left:12px solid #800000;
    margin-bottom:40px;
    box-shadow:0 6px 18px rgba(0,0,0,0.18);
}

.card-date { color:#666; font-size:0.9rem; }
.card-title { color:#800000; font-size:1.5rem; font-weight:700; }

.venue a { color:#333; text-decoration:none; }
.venue a:hover { text-decoration:underline; }

.team {
    background:#fff3f3;
    padding:18px;
    border-radius:14px;
    margin-top:18px;
}

.btn-row {
    display:flex;
    flex-wrap:wrap;
    gap:16px;
    margin-top:22px;
}

.btn {
    background:#800000;
    color:white;
    padding:12px 28px;
    border-radius:16px;
    font-weight:600;
    text-decoration:none;
}

.footer {
    background:#800000;
    color:white;
    text-align:center;
    padding:18px;
    font-size:0.85rem;
    margin-top:50px;
}
</style>

<div class="navbar">
    <img src="https://midstream-primary.co.za/wp-content/uploads/2021/09/MCP-1.png">
</div>

<div class="header">
Laerskool Midstream College Primary Event Hub
</div>
""", unsafe_allow_html=True)

# =========================
# HELPERS
# =========================
def extract_all_urls(row):
    urls = []
    for val in row.values:
        if pd.notna(val):
            urls += URL_REGEX.findall(str(val))
    return list(dict.fromkeys(urls))

def parse_date(val):
    if pd.isna(val):
        return pd.NaT
    s = str(val)
    if not re.search(r"\d{4}", s):
        s += f" {datetime.now().year}"
    return pd.to_datetime(s, dayfirst=True, errors="coerce")

# =========================
# LOAD DATA
# =========================
@st.cache_data(ttl=120)
def load_data():
    r = requests.get(DATA_URL, timeout=10)
    df = pd.read_csv(io.StringIO(r.text))
    df.columns = [c.strip().lower() for c in df.columns]
    if "date" in df.columns:
        df["date_fixed"] = df["date"].apply(parse_date)
    else:
        df["date_fixed"] = pd.NaT
    return df

df = load_data()

# =========================
# FILTER VALUES (SAFE)
# =========================
activities = sorted(df["activity"].dropna().astype(str).unique()) if "activity" in df.columns else []
ages = sorted(df["age"].dropna().astype(str).unique()) if "age" in df.columns else []
categories = sorted(df["category"].dropna().astype(str).unique()) if "category" in df.columns else []

# =========================
# FILTER UI
# =========================
with st.container():
    st.markdown('<div class="filter-box">', unsafe_allow_html=True)

    activity_filter = st.multiselect("Activity", activities)
    age_filter = st.multiselect("Age Group", ages)
    category_filter = st.multiselect("Category", categories)

    col1, col2, col3 = st.columns(3)
    if "range" not in st.session_state:
        st.session_state.range = "7"

    if col1.button("Next 7 Days"):
        st.session_state.range = "7"
    if col2.button("All Events"):
        st.session_state.range = "all"
    if col3.button("Refresh"):
        st.cache_data.clear()

    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# APPLY FILTERS
# =========================
df = df[df["date_fixed"].isna() | (df["date_fixed"].dt.date >= TODAY)]

if st.session_state.range == "7":
    df = df[df["date_fixed"].isna() | (df["date_fixed"].dt.date <= TODAY + timedelta(days=7))]

if activity_filter:
    df = df[df["activity"].astype(str).isin(activity_filter)]
if age_filter and "age" in df.columns:
    df = df[df["age"].astype(str).isin(age_filter)]
if category_filter and "category" in df.columns:
    df = df[df["category"].astype(str).isin(category_filter)]

df = df.sort_values("date_fixed", na_position="last")

# =========================
# CARDS
# =========================
for _, r in df.iterrows():
    date_str = r["date_fixed"].strftime("%d %B %Y") if pd.notna(r["date_fixed"]) else "TBA"
    venue = str(r.get("venue","")).strip()

    maps = ""
    if venue:
        maps = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote_plus(venue)}"

    buttons = []
    for u in extract_all_urls(r):
        label = "OPEN"
        if "forms" in u:
            label = "CONFIRM"
        elif "drive" in u:
            label = "PROGRAMME"
        buttons.append(f'<a class="btn" href="{u}" target="_blank">{label}</a>')

    team_text = ""
    if pd.notna(r.get("team")):
        team_text = re.sub(URL_REGEX, "", str(r.get("team"))).strip()

    st.markdown(f"""
    <div class="card">
        <div class="card-date">📅 {date_str}</div>
        <div class="card-title">{r.get("activity","")} {r.get("age","")}</div>
        {f'<div class="venue"><a href="{maps}" target="_blank">📍 {venue}</a></div>' if venue else ''}
        {f'<div class="team"><b>Teams</b><br>{team_text}</div>' if team_text else ''}
        {f'<div class="btn-row">{"".join(buttons)}</div>' if buttons else ''}
    </div>
    """, unsafe_allow_html=True)

# =========================
# FOOTER
# =========================
st.markdown("""
<div class="footer">
Midstream College Primary · info@midstreamprimary.co.za · 012 940 2222
</div>
""", unsafe_allow_html=True)
