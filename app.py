import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import re
from datetime import datetime, timedelta
import requests
import io
import time
import urllib.parse
from streamlit_autorefresh import st_autorefresh

# ----------------------------
# Page Config
# ----------------------------
st.set_page_config(page_title="LMCP Events Hub", layout="centered")
st_autorefresh(interval=120000, key="datarefresh")

today = datetime.now().date()

# ----------------------------
# Navbar
# ----------------------------
st.markdown("""
<style>
#MainMenu, footer, header {visibility:hidden;}
.stApp {background:#008080;}

.navbar {
    position:fixed;
    top:0;
    left:0;
    right:0;
    background:white;
    border-bottom:2px solid #800000;
    padding:10px 16px;
    z-index:9999;
    display:flex;
    align-items:center;
    gap:14px;
}
.navbar img {height:46px;}
.nav-title {
    font-family:'Cinzel', serif;
    font-size:1.3rem;
    font-weight:700;
    color:#800000;
}
.nav-spacer {height:90px;}

.block-container {max-width:600px; padding:1rem;}
label {color:white !important; font-weight:bold;}
</style>

<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700&display=swap" rel="stylesheet">

<div class="navbar">
    <img src="https://midstream-primary.co.za/wp-content/uploads/2021/09/MCP-1.png">
    <div class="nav-title">Events Hub</div>
</div>
<div class="nav-spacer"></div>
""", unsafe_allow_html=True)

# ----------------------------
# Card Styling
# ----------------------------
CARD_STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

.card {
    background:white;
    padding:16px;
    border-radius:16px;
    border-left:10px solid #800000;
    margin-bottom:14px;
    box-shadow:0 4px 12px rgba(0,0,0,0.15);
    font-family:'Inter', system-ui, sans-serif;
}

.date-in {
    font-size:0.85rem;
    color:#666;
    margin-bottom:4px;
}

.title {
    color:#800000;
    font-weight:700;
    font-size:1.05rem;
    margin-bottom:4px;
}

.venue a {
    color:#333;
    text-decoration:none;
    font-weight:500;
}

.team {
    background:#fff3f3;
    padding:12px;
    border-radius:12px;
    margin-top:10px;
    border:1px dashed #800000;
    color:#800000;
    font-size:0.9rem;
    line-height:1.45;
}

.note {
    background:#f8f9fa;
    padding:12px;
    border-radius:12px;
    margin-top:10px;
    border-left:4px solid #008080;
    font-size:0.9rem;
}

.btn-row {
    display:flex;
    gap:12px;
    margin-top:12px;
    flex-wrap:wrap;
}

.btn {
    background:#800000;
    color:white;
    font-weight:600;
    font-size:0.78rem;
    padding:10px 18px;
    border-radius:10px;
    text-decoration:none;
}
</style>
"""

# ----------------------------
# Data
# ----------------------------
URL_DATA = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-"
    "YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub"
    "?gid=0&single=true&output=csv"
)

URL_REGEX = re.compile(r"(https?://[^\s<>\"']+)")

def extract_urls(text):
    return URL_REGEX.findall(text)

@st.cache_data(ttl=120)
def load_data():
    r = requests.get(f"{URL_DATA}&cb={int(time.time())}", timeout=10)
    df = pd.read_csv(io.StringIO(r.content.decode("utf-8")))
    df.columns = [c.strip() for c in df.columns]

    year = datetime.now().year
    def parse_dt(x):
        s = str(x).strip()
        if not s or s.lower() == "nan":
            return pd.NaT
        if not re.search(r"\d{4}", s):
            s = f"{s} {year}"
        return pd.to_datetime(s, dayfirst=True, errors="coerce")

    df["dt_fixed"] = df.iloc[:,3].apply(parse_dt)
    return df

raw_df = load_data()

# ----------------------------
# Filters (UNCHANGED)
# ----------------------------
if "activity_filter" not in st.session_state:
    st.session_state.activity_filter = []

activities = sorted(raw_df.iloc[:,1].dropna().unique())

activity_selection = st.multiselect(
    "Select Activities:",
    activities,
    st.session_state.activity_filter
)
st.session_state.activity_filter = activity_selection

col1, col2 = st.columns(2)
with col1:
    view = st.radio("View:", ["Upcoming", "Results"], horizontal=True)
with col2:
    cat = st.selectbox("Category:", ["All", "Sport", "Culture", "Academics"])

seven_days = st.toggle("Limit to next 7 days (turn OFF to see all upcoming fixtures)", value=True)

search = st.text_input("Search").lower().strip()

# ----------------------------
# Filtering
# ----------------------------
df = raw_df.copy()

if view == "Upcoming":
    df = df[df["dt_fixed"].isna() | (df["dt_fixed"].dt.date >= today)]
else:
    df = df[df["dt_fixed"].notna() & (df["dt_fixed"].dt.date < today)]

if seven_days and view == "Upcoming":
    df = df[df["dt_fixed"].isna() | (df["dt_fixed"].dt.date <= today + timedelta(days=7))]

if cat != "All":
    df = df[df.iloc[:,0].astype(str).str.lower().str.contains(cat.lower())]

if activity_selection:
    df = df[df.iloc[:,1].astype(str).str.lower().isin([a.lower() for a in activity_selection])]

if search:
    df = df[df.astype(str).apply(lambda r: r.str.lower().str.contains(search, na=False)).any(axis=1)]

df = df.sort_values("dt_fixed", na_position="last")

# ----------------------------
# Display
# ----------------------------
for _, r in df.iterrows():
    sport = str(r.iloc[1]).strip()
    age = "" if str(r.iloc[2]).lower() == "nan" else str(r.iloc[2])
    venue = str(r.iloc[4]).strip()
    date_str = r["dt_fixed"].strftime("%A, %d %B %Y") if pd.notnull(r["dt_fixed"]) else "TBA"

    maps_link = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote_plus(venue)}"

    team, note, buttons = "", "", []

    for idx, lbl in [(5,"PROGRAMME"),(6,"TEAM"),(7,"CONFIRM"),(8,"INFO")]:
        val = str(r.iloc[idx]).strip()
        if not val or val.lower() == "nan":
            continue

        urls = extract_urls(val)
        text = re.sub(URL_REGEX, "", val).strip()

        if lbl == "TEAM":
            team = text
        elif lbl == "PROGRAMME":
            for u in urls:
                buttons.append(f'<a class="btn" href="{u}" target="_blank">PROGRAMME</a>')
        elif lbl == "CONFIRM":
            for u in urls:
                buttons.append(f'<a class="btn" href="{u}" target="_blank">CONFIRM</a>')
        elif lbl == "INFO" and sport.lower() != "swimming":
            note = text

    html = f"""
    <meta charset="UTF-8">
    {CARD_STYLE}
    <div class="card">
        <div class="date-in">📅 {date_str}</div>
        <div class="title">{sport} {age}</div>
        <div class="venue"><a href="{maps_link}" target="_blank">📍 {venue}</a></div>
        {f'<div class="team"><b>TEAMS</b><br>{team}</div>' if team else ''}
        {f'<div class="note">{note}</div>' if note else ''}
        {f'<div class="btn-row">{"".join(buttons)}</div>' if buttons else ''}
    </div>
    """

    components.html(html, height=520, scrolling=True)

# ----------------------------
# Footer
# ----------------------------
st.markdown("""
<div style="background:#800000;color:white;text-align:center;padding:14px;margin-top:30px;font-size:0.85rem;">
Midstream College Primary · info@midstreamprimary.co.za · 012 940 2222
</div>
""", unsafe_allow_html=True)
