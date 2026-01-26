import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import re
from datetime import datetime, timedelta
import requests
import io
import time
import urllib.parse

# ----------------------------
# Page Config
# ----------------------------
st.set_page_config(page_title="LMCP Live Fixtures", layout="centered")

today = datetime.now().date()

# ----------------------------
# NAVBAR (FIXED)
# ----------------------------
st.markdown("""
<style>
.navbar {
    position:fixed;
    top:0;
    left:0;
    right:0;
    background:#ffffff;
    border-bottom:2px solid #800000;
    z-index:9999;
    padding:10px 20px;
    display:flex;
    align-items:center;
    gap:20px;
}
.navbar img {height:48px;}
.nav-btn {
    background:#800000;
    color:white;
    border:none;
    padding:8px 14px;
    border-radius:8px;
    font-weight:600;
    cursor:pointer;
}
.nav-spacer {height:90px;}
.footer {
    background:#800000;
    color:white;
    text-align:center;
    padding:14px;
    font-size:0.85rem;
}
</style>

<div class="navbar">
    <img src="https://midstream-primary.co.za/wp-content/uploads/2021/09/MCP-1.png">
</div>

<div class="nav-spacer"></div>
""", unsafe_allow_html=True)

# ----------------------------
# Controls
# ----------------------------
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Next 7 Days"):
        st.session_state["range"] = "7"

with col2:
    if st.button("All Upcoming"):
        st.session_state["range"] = "all"

with col3:
    if st.button("Results"):
        st.session_state["range"] = "results"

if "range" not in st.session_state:
    st.session_state["range"] = "7"

# ----------------------------
# Styling
# ----------------------------
CARD_STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

.card {
    background:white;
    padding:18px;
    border-radius:18px;
    border-left:10px solid #800000;
    margin-bottom:16px;
    box-shadow:0 4px 12px rgba(0,0,0,0.15);
    font-family:'Inter', sans-serif;
}
.title {color:#800000;font-weight:700;font-size:1.05rem;}
.date-head {
    margin:20px 0 10px;
    font-weight:700;
    color:white;
}
.venue a {color:#333;text-decoration:none;font-weight:500;}
.team {margin-top:8px;color:#800000;font-size:0.9rem;}
.btn-row {margin-top:12px;display:flex;gap:10px;flex-wrap:wrap;}
.btn {
    background:#800000;
    color:white;
    padding:10px 18px;
    border-radius:8px;
    font-size:0.75rem;
    text-decoration:none;
}
</style>
"""

# ----------------------------
# Data
# ----------------------------
URL_DATA = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?gid=0&single=true&output=csv"
URL_REGEX = re.compile(r"(https?://[^\s]+)")

@st.cache_data(ttl=120)
def load_data():
    df = pd.read_csv(URL_DATA)
    df.columns = [c.strip() for c in df.columns]

    def parse_dt(x):
        if pd.isna(x): return pd.NaT
        return pd.to_datetime(str(x) + f" {datetime.now().year}", dayfirst=True, errors="coerce")

    df["dt_fixed"] = df.iloc[:,3].apply(parse_dt)
    return df

df = load_data()

# ----------------------------
# Filter by Range
# ----------------------------
if st.session_state["range"] == "7":
    df = df[df["dt_fixed"].dt.date.between(today, today + timedelta(days=7))]
elif st.session_state["range"] == "all":
    df = df[df["dt_fixed"].dt.date >= today]
else:
    df = df[df["dt_fixed"].dt.date < today]

df = df.sort_values("dt_fixed")

# ----------------------------
# Group by Date
# ----------------------------
for date, group in df.groupby(df["dt_fixed"].dt.date):
    st.markdown(f"<div class='date-head'>{date.strftime('%A, %d %B %Y')}</div>", unsafe_allow_html=True)

    for _, r in group.iterrows():
        sport = r.iloc[1]
        age = "" if pd.isna(r.iloc[2]) else r.iloc[2]
        venue = r.iloc[4]
        maps = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote_plus(venue)}"

        team = "" if pd.isna(r.iloc[6]) else r.iloc[6]

        buttons = []
        for idx, label in [(5,"PROGRAMME"), (7,"CONFIRM")]:
            val = str(r.iloc[idx])
            urls = URL_REGEX.findall(val)
            for u in urls:
                buttons.append(f"<a class='btn' href='{u}' target='_blank'>{label}</a>")

        html = f"""
        <div class="card">
            <div class="title">{sport} {age}</div>
            <div class="venue"><a href="{maps}" target="_blank">{venue}</a></div>
            {f"<div class='team'><b>Teams:</b><br>{team}</div>" if team else ""}
            <div class="btn-row">{''.join(buttons)}</div>
        </div>
        """

        components.html(f"<meta charset='UTF-8'>{CARD_STYLE}{html}", height=420, scrolling=True)

# ----------------------------
# Footer
# ----------------------------
st.markdown("""
<div class="footer">
    Midstream College Primary · Tel: 012 940 2222 · info@midstreamprimary.co.za
</div>
""", unsafe_allow_html=True)
