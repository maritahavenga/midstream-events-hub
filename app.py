import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import re
from datetime import datetime, timedelta
import requests, io, time, urllib.parse
from streamlit_autorefresh import st_autorefresh

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(page_title="LMCP Event Hub", layout="centered")
st_autorefresh(interval=120000, key="refresh")

today = datetime.now().date()

# --------------------------------------------------
# GLOBAL STYLES + NAVBAR
# --------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700&display=swap');

#MainMenu, footer, header {visibility:hidden;}
.stApp {background:#008080;}
.block-container {max-width:650px; padding-top:140px;}

.navbar {
    position:fixed;
    top:0; left:0; right:0;
    background:white;
    border-bottom:3px solid #800000;
    padding:14px 20px;
    display:flex;
    align-items:center;
    gap:18px;
    z-index:9999;
}
.navbar img {height:52px;}
.nav-title {
    font-family:'Source Sans 3', sans-serif;
    font-weight:700;
    font-size:1.15rem;
    color:#800000;
    line-height:1.25;
}

.filter-box {
    background:white;
    padding:18px;
    border-radius:18px;
    box-shadow:0 6px 14px rgba(0,0,0,0.18);
    margin-bottom:40px;
}

label {color:#333 !important; font-weight:600;}
</style>

<div class="navbar">
    <img src="https://midstream-primary.co.za/wp-content/uploads/2021/09/MCP-1.png">
    <div class="nav-title">
        Laerskool Midstream College Primary<br>
        Event Hub
    </div>
</div>
""", unsafe_allow_html=True)

# --------------------------------------------------
# CARD STYLES
# --------------------------------------------------
CARD_STYLE = """
<style>
.card {
    background:white;
    padding:22px;
    border-radius:20px;
    border-left:12px solid #800000;
    margin-bottom:70px;
    box-shadow:0 8px 18px rgba(0,0,0,0.18);
    font-family:'Source Sans 3', sans-serif;
}

.card-date {
    font-size:0.85rem;
    color:#555;
    margin-bottom:6px;
}

.card-title {
    color:#800000;
    font-weight:700;
    font-size:1.1rem;
    margin-bottom:6px;
}

.venue a {
    text-decoration:none;
    color:#333;
    font-weight:500;
}

.team {
    background:#fff3f3;
    padding:16px;
    border-radius:14px;
    margin-top:16px;
    border:1px dashed #800000;
    font-size:0.95rem;
    line-height:1.55;
}

.note {
    background:#f8f9fa;
    padding:16px;
    border-radius:14px;
    margin-top:16px;
    border-left:5px solid #008080;
    font-size:0.9rem;
}

.btn-row {
    display:flex;
    gap:16px;
    margin-top:18px;
    flex-wrap:wrap;
}

.btn {
    background:#800000;
    color:white;
    font-weight:600;
    font-size:0.8rem;
    padding:12px 22px;
    border-radius:14px;
    text-decoration:none;
}
</style>
"""

# --------------------------------------------------
# DATA
# --------------------------------------------------
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

# --------------------------------------------------
# FILTER PANEL
# --------------------------------------------------
with st.container():
    st.markdown('<div class="filter-box">', unsafe_allow_html=True)

    if "activity_filter" not in st.session_state:
        st.session_state.activity_filter = []

    activities = sorted(raw_df.iloc[:,1].dropna().unique())

    activity = st.multiselect("Activity", activities, st.session_state.activity_filter)
    st.session_state.activity_filter = activity

    c1, c2 = st.columns(2)
    with c1:
        view = st.radio("View", ["Upcoming", "Results"], horizontal=True)
    with c2:
        cat = st.selectbox("Category", ["All", "Sport", "Culture", "Academics"])

    seven_days = st.toggle("Show only next 7 days", value=True)
    search = st.text_input("Search").lower().strip()

    st.markdown('</div>', unsafe_allow_html=True)

# --------------------------------------------------
# FILTER LOGIC
# --------------------------------------------------
df = raw_df.copy()

if view == "Upcoming":
    df = df[df["dt_fixed"].isna() | (df["dt_fixed"].dt.date >= today)]
else:
    df = df[df["dt_fixed"].notna() & (df["dt_fixed"].dt.date < today)]

if seven_days and view == "Upcoming":
    df = df[df["dt_fixed"].isna() | (df["dt_fixed"].dt.date <= today + timedelta(days=7))]

if cat != "All":
    df = df[df.iloc[:,0].astype(str).str.lower().str.contains(cat.lower())]

if activity:
    df = df[df.iloc[:,1].astype(str).str.lower().isin([a.lower() for a in activity])]

if search:
    df = df[df.astype(str).apply(lambda r: r.str.lower().str.contains(search, na=False)).any(axis=1)]

df = df.sort_values("dt_fixed", na_position="last")

# --------------------------------------------------
# DISPLAY CARDS
# --------------------------------------------------
for _, r in df.iterrows():
    sport = str(r.iloc[1]).strip()
    age = "" if str(r.iloc[2]).lower() == "nan" else str(r.iloc[2])
    venue = str(r.iloc[4]).strip()
    date_str = r["dt_fixed"].strftime("%d %B %Y") if pd.notnull(r["dt_fixed"]) else "TBA"

    maps_link = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote_plus(venue)}"

    team, note, buttons = "", "", []

    for idx, lbl in [(5,"PROGRAMME"),(6,"TEAM"),(7,"CONFIRM"),(8,"INFO")]:
        val = str(r.iloc[idx]).strip()
        if not val or val.lower() == "nan":
            continue

        urls = extract_urls(val)
        clean = re.sub(URL_REGEX, "", val).strip()

        if lbl == "TEAM":
            team = clean
        elif lbl == "PROGRAMME":
            for u in urls:
                buttons.append(f'<a class="btn" href="{u}" target="_blank">PROGRAMME</a>')
        elif lbl == "CONFIRM":
            for u in urls:
                buttons.append(f'<a class="btn" href="{u}" target="_blank">CONFIRM</a>')
        elif lbl == "INFO" and sport.lower() != "swimming":
            note = clean

    html = f"""
    <meta charset="UTF-8">
    {CARD_STYLE}
    <div class="card">
        <div class="card-date">📅 {date_str}</div>
        <div class="card-title">{sport} {age}</div>
        <div class="venue"><a href="{maps_link}" target="_blank">📍 {venue}</a></div>
        {f'<div class="team"><b>Teams</b><br>{team}</div>' if team else ''}
        {f'<div class="note">{note}</div>' if note else ''}
        {f'<div class="btn-row">{"".join(buttons)}</div>' if buttons else ''}
    </div>
    """

    components.html(html, height=600, scrolling=False)

# --------------------------------------------------
# FOOTER
# --------------------------------------------------
st.markdown("""
<div style="background:#800000;color:white;text-align:center;padding:18px;margin-top:50px;font-size:0.85rem;">
Midstream College Primary · info@midstreamprimary.co.za · 012 940 2222
</div>
""", unsafe_allow_html=True)
