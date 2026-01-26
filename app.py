import streamlit as st
import pandas as pd
import re
from datetime import datetime
import pytz
import requests
import io
import time
import html
from streamlit_autorefresh import st_autorefresh

# --------------------------------------------------
# Page Configuration
# --------------------------------------------------
st.set_page_config(page_title="LMCP Live Fixtures", layout="centered")
st_autorefresh(interval=120000, key="datarefresh")

# --------------------------------------------------
# Styling
# --------------------------------------------------
st.markdown("""
<style>
#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
.stApp{background:#008080}.block-container{padding:1rem;max-width:500px}
.card{background:white!important;padding:18px;border-radius:15px;border-left:12px solid #800000;margin-bottom:15px;box-shadow:0 4px 10px rgba(0,0,0,0.2)}
.t{color:#800000!important;font-weight:bold;font-size:1.2rem;margin:5px 0}
.box{background:#f8f9fa;padding:12px;border-radius:10px;margin:10px 0;border-left:5px solid #008080;color:#333;font-size:0.9rem;white-space: pre-wrap;}
.team-box{background:#fff3f3;padding:10px;border-radius:8px;margin:5px 0;border:1px dashed #800000;color:#800000;font-size:0.85rem;white-space: pre-wrap;}
.btn-row {display:flex;gap:6px;flex-wrap:wrap;margin-top:10px}
.btn {background:#800000;color:white!important;font-weight:bold;font-size:0.7rem;padding:10px 14px;border-radius:6px;text-decoration:none}
label { color:white !important; font-weight:bold; }
.stTextInput, .stSelectbox { width: 50% !important; }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# Data Source
# --------------------------------------------------
URL_DATA = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-"
    "YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub"
    "?gid=0&single=true&output=csv"
)

# --------------------------------------------------
# URL Helpers (FIXED)
# --------------------------------------------------
URL_REGEX = re.compile(r"(https?://[^\s<>\"']+)")

def extract_urls(text: str):
    return URL_REGEX.findall(text)

# --------------------------------------------------
# Load Data
# --------------------------------------------------
def load_data():
    response = requests.get(f"{URL_DATA}&cb={int(time.time())}", timeout=10)
    df = pd.read_csv(io.StringIO(response.content.decode("utf-8")))
    df.columns = [str(c).strip() for c in df.columns]

    current_year = datetime.now().year

    def parse_dt(x):
        s = str(x).strip()
        if not s or s.lower() == "nan":
            return pd.NaT
        if not re.search(r"\d{4}", s):
            s = f"{s} {current_year}"
        return pd.to_datetime(s, dayfirst=True, errors="coerce")

    df["dt_fixed"] = df.iloc[:, 3].apply(parse_dt)
    return df

# --------------------------------------------------
# Header
# --------------------------------------------------
st.image(
    "https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg",
    use_container_width=True
)

raw_df = load_data()

SA_TIME = pytz.timezone("Africa/Johannesburg")
today = datetime.now(SA_TIME).date()

# --------------------------------------------------
# Sticky Activity Filter (SESSION STATE)
# --------------------------------------------------
if "activity_filter" not in st.session_state:
    st.session_state.activity_filter = ""

activity = st.text_input(
    "🏃 Activity (sticky filter)",
    value=st.session_state.activity_filter,
    placeholder="e.g. Athletics, Swimming"
)

st.session_state.activity_filter = activity.strip().lower()

search_q = st.text_input(
    "🔍 Search",
    placeholder="e.g. u13"
).lower().strip()

# --------------------------------------------------
# View & Category Filters
# --------------------------------------------------
col1, col2 = st.columns(2)
with col1:
    view = st.radio("View:", ["Upcoming", "Results"], horizontal=True)
with col2:
    cat = st.selectbox("Category:", ["All", "Sport", "Culture", "Academics"])

# --------------------------------------------------
# Filtering Logic (ATHLETICS SAFE)
# --------------------------------------------------
if view == "Upcoming":
    df = raw_df[
        raw_df["dt_fixed"].isna() |
        (raw_df["dt_fixed"].dt.date >= today)
    ]
else:
    df = raw_df[
        raw_df["dt_fixed"].notna() &
        (raw_df["dt_fixed"].dt.date < today)
    ]

df = df.sort_values("dt_fixed", na_position="last")

if cat != "All":
    df = df[
        df.iloc[:, 0]
        .astype(str)
        .str.strip()
        .str.lower()
        == cat.lower()
    ]

if st.session_state.activity_filter:
    df = df[
        df.iloc[:, 1]
        .astype(str)
        .str.lower()
        .str.contains(st.session_state.activity_filter)
    ]

if search_q:
    mask = df.astype(str).apply(
        lambda c: c.str.lower().str.contains(search_q, na=False)
    )
    df = df[mask.any(axis=1)]

# --------------------------------------------------
# Display Cards
# --------------------------------------------------
for _, r in df.iterrows():

    sport = str(r.iloc[1]).strip()
    age_raw = str(r.iloc[2]).strip()
    age = age_raw if age_raw.lower() != "nan" else ""

    date_str = (
        r["dt_fixed"].strftime("%d %B %Y")
        if pd.notnull(r["dt_fixed"])
        else "TBA"
    )

    venue = str(r.iloc[4]).strip()

    prog_link = ""
    other_btns = []
    team_text = ""
    note_text = ""

    for idx, lbl in [(5, "PROGRAMME"), (6, "TEAM"), (7, "CONFIRM"), (8, "INFORMATION")]:
        val = str(r.iloc[idx]).strip()
        if not val or val.lower() == "nan":
            continue

        urls = extract_urls(val)
        clean_text = html.escape(URL_REGEX.sub("", val).strip())

        # URLs
        for u in urls:
            if lbl == "PROGRAMME":
                prog_link = u
            else:
                other_btns.append(
                    f'<a href="{u}" target="_blank" class="btn">{lbl}</a>'
                )

        # Text
        if clean_text:
            if lbl == "TEAM":
                team_text = clean_text
            elif lbl == "INFORMATION":
                note_text = clean_text

    st.markdown(f"""
    <div class="card">
        <div style="font-size:0.85rem;color:#666">🗓️ {date_str}</div>
        <div class="t">{sport} {age}</div>
        <div style="font-size:0.85rem;color:#333">📍 {venue}</div>
        {f'<div class="team-box"><b>TEAMS:</b><br>{team_text}</div>' if team_text else ''}
        {f'<div class="btn-row">{" ".join(other_btns)}</div>' if other_btns else ''}
        {f'<div class="box"><b>Note:</b><br>{note_text}</div>' if note_text else ''}
        {f'<div class="btn-row"><a href="{prog_link}" target="_blank" class="btn">PROGRAMME</a></div>' if prog_link else ''}
    </div>
    """, unsafe_allow_html=True)
