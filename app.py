import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import re
from datetime import datetime
import requests
import io
import time
from streamlit_autorefresh import st_autorefresh
import urllib.parse

# ----------------------------
# Page Config
# ----------------------------
st.set_page_config(page_title="LMCP Live Fixtures", layout="centered")
st_autorefresh(interval=120000, key="datarefresh")

today = datetime.now().date()

# ----------------------------
# Global Styling
# ----------------------------
st.markdown("""
<style>
#MainMenu, footer, header {visibility:hidden;}
.stApp {background:#008080;}
.block-container {max-width:600px; padding:1rem;}
label {color:white !important; font-weight:bold;}
</style>
""", unsafe_allow_html=True)

CARD_STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

.card {
    background:white;
    padding:18px;
    border-radius:18px;
    border-left:10px solid #800000;
    margin-bottom:18px;
    box-shadow:0 4px 14px rgba(0,0,0,0.16);
    font-family:'Inter', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
    width:100%;
    box-sizing:border-box;
}

.date {
    color:#777;
    font-size:0.85rem;
    letter-spacing:0.2px;
}

.title {
    color:#800000;
    font-weight:700;
    margin:6px 0 4px 0;
    font-size:1.05rem;
    line-height:1.35;
    word-wrap:break-word;
}

.venue a {
    color:#333;
    text-decoration:none;
    font-weight:500;
    font-size:0.9rem;
}

.venue a:hover {
    text-decoration:underline;
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
    word-wrap:break-word;
}

.note {
    background:#f8f9fa;
    padding:12px;
    border-radius:12px;
    margin-top:10px;
    border-left:4px solid #008080;
    color:#333;
    font-size:0.9rem;
    line-height:1.45;
    word-wrap:break-word;
}

.btn-row {
    display:flex;
    gap:12px;
    margin-top:14px;
    flex-wrap:wrap;
}

.btn {
    background:#800000;
    color:white;
    font-weight:600;
    font-size:0.78rem;
    padding:11px 20px;
    border-radius:10px;
    text-decoration:none;
    letter-spacing:0.3px;
}

.btn:hover {
    background:#5e0000;
}
</style>
"""

# ----------------------------
# Data Source
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

# ----------------------------
# Load Data
# ----------------------------
@st.cache_data(ttl=120)
def load_data():
    try:
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
    except:
        return pd.DataFrame()

raw_df = load_data()

if st.button("REFRESH DATA"):
    st.cache_data.clear()
    st.rerun()

# ----------------------------
# Filters
# ----------------------------
if "activity_filter" not in st.session_state:
    st.session_state.activity_filter = []

activities = raw_df.iloc[:,1].dropna().unique() if not raw_df.empty else []
activities = sorted([a for a in activities if str(a).lower() != "nan"])

selection = st.multiselect(
    "Select Activities:",
    activities,
    st.session_state.activity_filter
)
st.session_state.activity_filter = selection

col1, col2 = st.columns(2)
with col1:
    view = st.radio("View:", ["Upcoming", "Results"], horizontal=True)
with col2:
    cat = st.selectbox("Category:", ["All", "Sport", "Culture", "Academics"])

search = st.text_input("Search").lower().strip()

# ----------------------------
# Filtering + Display
# ----------------------------
if raw_df.empty:
    st.error("No data available.")
else:
    df = raw_df.copy()

    if view == "Upcoming":
        df = df[df["dt_fixed"].isna() | (df["dt_fixed"].dt.date >= today)]
    else:
        df = df[df["dt_fixed"].notna() & (df["dt_fixed"].dt.date < today)]

    if cat != "All":
        df = df[df.iloc[:,0].astype(str).str.lower().str.contains(cat.lower())]

    if selection:
        df = df[df.iloc[:,1].astype(str).str.lower().isin([s.lower() for s in selection])]

    if search:
        df = df[df.astype(str).apply(lambda r: r.str.lower().str.contains(search, na=False)).any(axis=1)]

    df = df.sort_values("dt_fixed", na_position="last")

    for _, r in df.iterrows():
        sport = str(r.iloc[1]).strip()
        age = "" if str(r.iloc[2]).lower() == "nan" else str(r.iloc[2])
        venue = str(r.iloc[4]).strip()
        date = r["dt_fixed"].strftime("%d %B %Y") if pd.notnull(r["dt_fixed"]) else "TBA"

        maps_query = urllib.parse.quote_plus(venue)
        maps_link = f"https://www.google.com/maps/search/?api=1&query={maps_query}"

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
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            {CARD_STYLE}
        </head>
        <body>
            <div class="card">
                <div class="date">{date}</div>
                <div class="title">{sport} {age}</div>
                <div class="venue">
                    <a href="{maps_link}" target="_blank">{venue}</a>
                </div>
                {f'<div class="team"><b>TEAMS</b><br>{team}</div>' if team else ''}
                {f'<div class="note">{note}</div>' if note else ''}
                {f'<div class="btn-row">{"".join(buttons)}</div>' if buttons else ''}
            </div>
        </body>
        </html>
        """

        components.html(html, scrolling=False)
