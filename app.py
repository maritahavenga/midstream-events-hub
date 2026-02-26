# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import requests, io, re, pytz, hashlib
from datetime import datetime, timedelta
from requests.exceptions import RequestException, Timeout

# =============================
# PAGE CONFIG
# =============================
st.set_page_config(page_title="LMCP Hub", page_icon="📌", layout="wide")

UPCOMING_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"
SUBMISSIONS_CSV_URL = "https://docs.google.com/spreadsheets/d/1jB78iGRp3pmwib7k_MfdwzMC402QY9MPtHKC3TAAlPQ/export?format=csv&gid=1864466191"

LOGO_URL = "https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg"
FACILITIES_MAP_URL = "https://drive.google.com/file/d/1PR-o4unbkpy7wq0Rg3nUf3wP1gHn_662/view?usp=sharing"

TZ = pytz.timezone("Africa/Johannesburg")
now_dt = datetime.now(TZ)
today = now_dt.date()

VIEW_OPTIONS = ["All", "Next 7 Days", "Term Documents", "Assessment Schedule", "Test Breakdown", "New Updates"]
NEW_UPDATES_DEFAULT_HOURS = 72
BADGE_ANIMATE_MINUTES = 10

# =============================
# DATE PARSING (RANGE SUPPORT)
# =============================
DATE_RANGE_RE = re.compile(r"^\s*(\d{1,2})\s*[-–]\s*(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{2,4})\s*$")

def parse_date_sa(s):
    raw = str(s or "").strip()
    if not raw or raw.lower() in ["nan", "none"]:
        return None
    cleaned = re.sub(r"\s+", " ", raw.replace(".", "/").replace("-", "/"))
    d1 = pd.to_datetime(cleaned, dayfirst=True, errors="coerce")
    if not pd.isnull(d1): return d1.to_pydatetime()
    d2 = pd.to_datetime(cleaned, dayfirst=False, errors="coerce")
    if not pd.isnull(d2): return d2.to_pydatetime()
    return None

def parse_date_range_sa(s):
    raw = str(s or "").strip()
    if not raw:
        return None, None

    m = DATE_RANGE_RE.match(raw.replace(".", "/"))
    if m:
        d1, d2, mm, yy = m.groups()
        yy = int(yy)
        if yy < 100:
            yy += 2000
        start = parse_date_sa(f"{int(d1):02d}/{int(mm):02d}/{yy}")
        end = parse_date_sa(f"{int(d2):02d}/{int(mm):02d}/{yy}")
        return start, end

    parts = [p.strip() for p in re.split(r"\s*[-–]\s*", raw) if p.strip()]
    if len(parts) == 2:
        return parse_date_sa(parts[0]), parse_date_sa(parts[1])

    d = parse_date_sa(raw)
    return d, d

def format_date_long_sa_range(s):
    start, end = parse_date_range_sa(s)
    if not start:
        return str(s or "").strip()

    if end and start.date() == end.date():
        return f"{start.day} {start.strftime('%B %Y')}"

    if end and (start.month == end.month) and (start.year == end.year):
        return f"{start.day} {start.strftime('%B')} - {end.day} {end.strftime('%B %Y')}"

    if end:
        return f"{start.day} {start.strftime('%B %Y')} - {end.day} {end.strftime('%B %Y')}"

    return f"{start.day} {start.strftime('%B %Y')}"

# =============================
# HELPERS
# =============================
URL_RE = re.compile(r"(https?://[^\s\)\]\}<>\"']+)", re.IGNORECASE)

def safe_txt(x):
    s = str(x or "")
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").strip()

def is_http(u):
    s = str(u or "").strip().lower()
    return s.startswith("http://") or s.startswith("https://")

# =============================
# VENUE (Astro + Hub supported)
# =============================
VENUE_MAP = {
    "musiekkamer": "Music Room",
    "saal": "Hall",
    "ouditorium": "Auditorium",
    "veld": "Field",
    "bondev": "Bondev Field",
    "swembad": "Swimming Pool",
    "tennis bane": "Tennis Courts",
    "netbal bane": "Netball Courts",
    "cricket oval": "Cricket Oval",
    "astro": "Astro",
    "bondev astro": "Bondev Astro",
    "meerkat astro": "Meerkat Astro",
    "hub": "Hub",
    "the hub": "Hub",
}

CAMPUS_VENUE_LABELS = {
    "music room","hall","auditorium","field","bondev field",
    "swimming pool","tennis courts","netball courts","cricket oval",
    "astro","bondev astro","meerkat astro","hub"
}

def normalize_venue(v):
    s = str(v or "").strip().lower()
    for k, vv in VENUE_MAP.items():
        if k in s:
            return vv
    return str(v or "").strip()

def is_midstream_campus_venue(ven_norm):
    return ven_norm.lower() in CAMPUS_VENUE_LABELS

# =============================
# LOAD DATA
# =============================
@st.cache_data(ttl=180)
def load_csv(url):
    r = requests.get(url, timeout=(6, 25))
    r.raise_for_status()
    return pd.read_csv(io.StringIO(r.text), dtype=str).fillna("")

df = load_csv(UPCOMING_CSV_URL)

# =============================
# BUILD RESULTS
# =============================
res = []

for i in range(len(df)):

    d_raw = str(df["Date / Due Date"].iloc[i]).strip()
    d_start, d_end = parse_date_range_sa(d_raw)

    if d_end and d_end.date() < today:
        continue

    if d_start and d_start.date() > (today + timedelta(days=7)):
        pass

    sort_dt = d_start if d_start else datetime(2099,1,1)

    res.append({
        "i": i,
        "dt": sort_dt,
        "title": str(df["Activity/Subject Name"].iloc[i]).lower(),
        "new": False
    })

res_sorted = sorted(res, key=lambda x: (x["dt"], x["title"]))

# =============================
# DISPLAY
# =============================
st.markdown("## 📅 Events")

for item in res_sorted:
    i = item["i"]

    title = safe_txt(df["Activity/Subject Name"].iloc[i])
    d_raw = str(df["Date / Due Date"].iloc[i]).strip()
    date_line = format_date_long_sa_range(d_raw)

    ven_norm = normalize_venue(df["Venue"].iloc[i])

    venue_href = FACILITIES_MAP_URL if is_midstream_campus_venue(ven_norm) else \
        f"https://www.google.com/maps/search/?api=1&query={ven_norm.replace(' ','+')}"

    ribbon = ""

    st.markdown(f"""
<div class="card">
  <div class="card-title">{title}</div>

  <div style="display:flex;justify-content:space-between;margin-top:8px;">
    <div class='meta'>📅 <b>{safe_txt(date_line)}</b></div>
    {ribbon}
  </div>

  <div class='meta'>📍 
    <a href='{venue_href}' target='_blank' style='color:#008080;font-weight:900;text-decoration:none;'>
    {safe_txt(ven_norm).upper()}
    </a>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown(
    "<br><center style='font-size:0.85rem;color:#94a3b8;'>LAERSKOOL MIDSTREAM COLLEGE PRIMARY Digital Hub 2026</center>",
    unsafe_allow_html=True,
)
