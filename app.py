import streamlit as st
st.set_page_config(page_title="LMCP Event Hub", layout="centered")

# --------------------------------------------------
# IMPORTS
# --------------------------------------------------
import streamlit.components.v1 as components
import pandas as pd
import re
from datetime import datetime, timedelta
import requests, io, time, urllib.parse

# --------------------------------------------------
# AUTORELOAD EVERY 2 MINUTES
# --------------------------------------------------
from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=120000, key="refresh")

today = datetime.now().date()

# --------------------------------------------------
# STYLES, NAVBAR, FULL-WIDTH LOGO, GREEN HEADER
# --------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700&display=swap');

#MainMenu, footer, header {visibility:hidden;}
.stApp {background:#008080;}
.block-container {max-width:650px; padding-top:100px;}

/* Navbar + full width logo */
.navbar {
    position:fixed;
    top:0; left:0; right:0;
    background:white;
    border-bottom:3px solid #800000;
    z-index:9999;
    text-align:center;
}
.navbar img {
    width:100%;
    max-height:120px;
    object-fit:contain;
}

/* Green header strip under logo */
.green-header {
    background:#008080;
    color:white;
    text-align:center;
    padding:14px 10px;
    font-family:'Source Sans 3', sans-serif;
    font-weight:700;
    font-size:1.25rem;
}

/* Filter panel */
.filter-box {
    background:white;
    padding:18px;
    border-radius:18px;
    box-shadow:0 6px 14px rgba(0,0,0,0.18);
    margin-bottom:40px;
}

label {color:#333 !important; font-weight:600;}

/* Streamlit input fields */
.stTextInput>div>div>input,
.stSelectbox>div>div>div>div,
.stMultiSelect>div>div>div {
    background:white;
    border:2px solid #800000;
    border-radius:8px;
    padding:6px 10px;
    color:#333;
}
.stTextInput>div>div>input:focus,
.stSelectbox>div>div>div>div:focus,
.stMultiSelect>div>div>div:focus {
    outline:none;
    border-color:#800000;
    box-shadow:0 0 0 2px rgba(128,0,0,0.2);
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
# CARD STYLE
# --------------------------------------------------
CARD_STYLE = """
<style>
.card {
    background:white;
    padding:28px;
    border-radius:20px;
    border-left:12px solid #800000;
    margin-bottom:40px;
    box-shadow:0 8px 18px rgba(0,0,0,0.18);
    font-family:'Source Sans 3', sans-serif;
    font-size:1rem;
}

.card-date {
    font-size:0.9rem;
    color:#555;
    margin-bottom:6px;
}

.card-title {
    color:#800000;
    font-weight:700;
    font-size:1.25rem;
    margin-bottom:6px;
}

.venue a {
    text-decoration:none;
    color:#333;
    font-weight:500;
    cursor:pointer;
}

.venue a:hover {
    text-decoration:underline;
}

.team {
    background:#fff3f3;
    padding:18px;
    border-radius:14px;
    margin-top:16px;
    border:1px dashed #800000;
    font-size:1rem;
    line-height:1.55;
}

.note {
    background:#f8f9fa;
    padding:18px;
    border-radius:14px;
    margin-top:16px;
    border-left:5px solid #008080;
    font-size:1rem;
}

.btn-row {
    display:flex;
    gap:16px;
    margin-top:18px;
    flex-wrap:wrap;
}

.btn {
    background:#A00000;
    color:white;
    font-weight:600;
    font-size:0.9rem;
    padding:12px 22px;
    border-radius:14px;
    text-decoration:none;
}
</style>
"""

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
    return URL_REGEX.findall(text)

@st.cache_data(ttl=120)
def load_data():
    r = requests.get(f"{URL_DATA}&cb={int(time.time())}", timeout=10)
    df = pd.read_csv(io.StringIO(r.content.decode("utf-8")))
    df.columns = [c.strip() for c in df.columns]
    year = datetime.now().year

    def parse_dt(x):
        s = str(x).strip()
        if not s or s.lower() == "nan": return pd.NaT
        if not re.search(r"\d{4}", s): s = f"{s} {year}"
        return pd.to_datetime(s, dayfirst=True, errors="coerce")

    df["dt_fixed"] = df.iloc[:,3].apply(parse_dt)
    return df

raw_df = load_data()

# --------------------------------------------------
# REFRESH BUTTON
# --------------------------------------------------
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.experimental_rerun()

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

    cat = st.selectbox("Category", ["All", "Sport", "Culture", "Academics"])

    # 7 DAY / ALL VIEW BUTTONS
    col_all, col_7 = st.columns(2)
    if "days_filter" not in st.session_state:
        st.session_state.days_filter = "7 days"

    if col_all.button("All View"):
        st.session_state.days_filter = "all"
    if col_7.button("Next 7 Days"):
        st.session_state.days_filter = "7 days"

    st.markdown('</div>', unsafe_allow_html=True)

# --------------------------------------------------
# FILTER LOGIC (skip past events)
# --------------------------------------------------
df = raw_df.copy()
df = df[df["dt_fixed"].isna() | (df["dt_fixed"].dt.date >= today)]

if st.session_state.days_filter == "7 days":
    df = df[df["dt_fixed"].isna() | (df["dt_fixed"].dt.date <= today + timedelta(days=7))]

if cat != "All":
    df = df[df.iloc[:,0].astype(str).str.lower().str.contains(cat.lower())]

if activity:
    df = df[df.iloc[:,1].astype(str).str.lower().isin([a.lower() for a in activity])]

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
        if not val or val.lower() == "nan": continue

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
        elif lbl == "INFO":
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

    components.html(html, height=None, scrolling=False)

# --------------------------------------------------
# FOOTER
# --------------------------------------------------
st.markdown("""
<div style="background:#800000;color:white;text-align:center;padding:18px;margin-top:50px;font-size:0.85rem;">
Midstream College Primary · info@midstreamprimary.co.za · 012 940 2222
</div>
""", unsafe_allow_html=True)
