import streamlit as st
st.set_page_config(page_title="LMCP Event Hub", layout="centered")

# --------------------------------------------------
# IMPORTS
# --------------------------------------------------
import pandas as pd
import re
from datetime import datetime, timedelta
import requests, io, time, urllib.parse

# --------------------------------------------------
# BASIC SETUP
# --------------------------------------------------
today = datetime.now().date()

# --------------------------------------------------
# STYLES
# --------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700&display=swap');

#MainMenu, footer, header {visibility:hidden;}
.stApp {background:#008080;}
.block-container {max-width:720px; padding-top:150px;}

.navbar {
    position:fixed;
    top:0; left:0; right:0;
    background:white;
    border-bottom:4px solid #800000;
    z-index:9999;
    text-align:center;
}
.navbar img {
    width:100%;
    max-height:130px;
    object-fit:contain;
}

.green-header {
    background:#008080;
    color:white;
    text-align:center;
    padding:16px 10px;
    font-family:'Source Sans 3', sans-serif;
    font-weight:700;
    font-size:1.3rem;
}

.filter-box {
    background:white;
    padding:20px;
    border-radius:18px;
    box-shadow:0 6px 14px rgba(0,0,0,0.18);
    margin-bottom:24px;
}

label {color:#333 !important; font-weight:600;}

.stTextInput input,
.stSelectbox div,
.stMultiSelect div {
    border:2px solid #800000 !important;
    border-radius:8px !important;
}

.card {
    background:white;
    padding:34px;
    border-radius:20px;
    border-left:12px solid #800000;
    margin-bottom:40px;
    box-shadow:0 8px 18px rgba(0,0,0,0.18);
    font-family:'Source Sans 3', sans-serif;
}

.card-date {font-size:0.9rem; color:#555;}
.card-title {color:#800000; font-size:1.35rem; font-weight:700;}

.venue a {
    color:#333;
    text-decoration:none;
}
.venue a:hover {text-decoration:underline;}

.team {
    background:#fff3f3;
    padding:18px;
    border-radius:14px;
    margin-top:16px;
    border:1px dashed #800000;
}

.btn-row {
    display:flex;
    gap:14px;
    margin-top:18px;
    flex-wrap:wrap;
}
.btn {
    background:#800000;
    color:white;
    padding:12px 22px;
    border-radius:14px;
    font-weight:600;
    text-decoration:none;
}
</style>

<div class="navbar">
    <img src="https://midstream-primary.co.za/wp-content/uploads/2021/09/MCP-1.png">
</div>

<div class="green-header">
Laerskool Midstream College Primary — Event Hub
</div>
""", unsafe_allow_html=True)

# --------------------------------------------------
# DATA SOURCE
# --------------------------------------------------
URL_DATA = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-"
    "YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub"
    "?gid=0&single=true&output=csv"
)

URL_REGEX = re.compile(r"(https?://[^\s<>\"']+)")

def extract_urls(text):
    return URL_REGEX.findall(text or "")

@st.cache_data(ttl=120)
def load_data():
    r = requests.get(URL_DATA, timeout=10)
    df = pd.read_csv(io.StringIO(r.text))
    df.columns = [c.strip().lower() for c in df.columns]

    def parse_date(x):
        if pd.isna(x): return pd.NaT
        s = str(x)
        if not re.search(r"\d{4}", s):
            s += f" {datetime.now().year}"
        return pd.to_datetime(s, dayfirst=True, errors="coerce")

    df["date_fixed"] = df["date"].apply(parse_date)
    return df

df = load_data()

# --------------------------------------------------
# REFRESH BUTTON (NO RERUN, SAFE)
# --------------------------------------------------
st.markdown('<div style="text-align:right;">', unsafe_allow_html=True)
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
st.markdown('</div>', unsafe_allow_html=True)

# --------------------------------------------------
# FILTERS
# --------------------------------------------------
with st.container():
    st.markdown('<div class="filter-box">', unsafe_allow_html=True)

    activities = sorted(df["activity"].dropna().astype(str).unique())
    activity_filter = st.multiselect("Activity", activities)

    cat = st.selectbox("Category", ["All"] + sorted(df["category"].dropna().astype(str).unique()))

    col1, col2 = st.columns(2)
    if "range" not in st.session_state:
        st.session_state.range = "7"

    if col1.button("All Events"):
        st.session_state.range = "all"
    if col2.button("Next 7 Days"):
        st.session_state.range = "7"

    st.markdown('</div>', unsafe_allow_html=True)

# --------------------------------------------------
# APPLY FILTERS
# --------------------------------------------------
df = df[df["date_fixed"].isna() | (df["date_fixed"].dt.date >= today)]

if st.session_state.range == "7":
    df = df[df["date_fixed"].isna() | (df["date_fixed"].dt.date <= today + timedelta(days=7))]

if cat != "All":
    df = df[df["category"].str.lower() == cat.lower()]

if activity_filter:
    df = df[df["activity"].isin(activity_filter)]

df = df.sort_values("date_fixed", na_position="last")

# --------------------------------------------------
# RENDER CARDS
# --------------------------------------------------
for _, r in df.iterrows():
    date_str = r["date_fixed"].strftime("%d %B %Y") if pd.notna(r["date_fixed"]) else "TBA"
    venue = str(r["venue"])
    maps = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote_plus(venue)}"

    buttons = []
    for label in ["programme", "confirm"]:
        for u in extract_urls(r.get(label, "")):
            buttons.append(f'<a class="btn" href="{u}" target="_blank">{label.upper()}</a>')

    st.markdown(f"""
    <div class="card">
        <div class="card-date">📅 {date_str}</div>
        <div class="card-title">{r["activity"]} {r.get("age","")}</div>
        <div class="venue"><a href="{maps}" target="_blank">📍 {venue}</a></div>
        {f'<div class="team"><b>Teams</b><br>{r["team"]}</div>' if pd.notna(r.get("team")) else ''}
        {f'<div class="btn-row">{"".join(buttons)}</div>' if buttons else ''}
    </div>
    """, unsafe_allow_html=True)

# --------------------------------------------------
# FOOTER
# --------------------------------------------------
st.markdown("""
<div style="background:#800000;color:white;text-align:center;padding:18px;margin-top:40px;font-size:0.85rem;">
Midstream College Primary · info@midstreamprimary.co.za · 012 940 2222
</div>
""", unsafe_allow_html=True)
