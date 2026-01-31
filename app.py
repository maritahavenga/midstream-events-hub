import re
import streamlit as st
import pandas as pd
import requests
import io
import time

# =============================
# PAGE CONFIG (mobile friendly)
# =============================
st.set_page_config(page_title="LMCP Event Hub", layout="centered")

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

# =============================
# BRAND COLORS
# =============================
MAROON = "#6b0019"
TEAL = "#0f5b66"
BG = "#f6f7fb"
TEAL_SHADE = "#e8f3f5"

# =============================
# CSS (modern phone font + responsive)
# =============================
st.markdown(
    f"""
<style>
  .stApp {{
    background: {BG};
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Inter, Helvetica, Arial, sans-serif;
  }}

  section.main > div {{
    max-width: 900px;
  }}

  .lmcp-divider {{
    height: 10px;
    background: linear-gradient(90deg, {MAROON}, {TEAL});
    border-radius: 999px;
    margin: 10px 0 16px 0;
    border: 2px solid rgba(0,0,0,0.06);
  }}

  .lmcp-panel {{
    background: white;
    border-radius: 18px;
    padding: 14px 16px;
    border: 1px solid rgba(0,0,0,0.06);
    box-shadow: 0 8px 16px rgba(0,0,0,0.05);
    margin-bottom: 14px;
  }}

  .lmcp-card {{
    background: white;
    border-radius: 18px;
    padding: 16px;
    border: 1px solid rgba(0,0,0,0.06);
    box-shadow: 0 10px 18px rgba(0,0,0,0.06);
    margin-bottom: 14px;
  }}

  .lmcp-title {{
    font-size: 18px;
    font-weight: 900;
    margin: 0;
    letter-spacing: 0.2px;
  }}

  .lmcp-subtitle {{
    font-size: 14px;
    font-weight: 800;
    color: {TEAL};
    margin-top: 6px;
  }}

  .lmcp-meta {{
    margin-top: 10px;
    color: #555;
    font-size: 14px;
    line-height: 1.6;
  }}

  .lmcp-info {{
    background: {TEAL_SHADE};
    border-left: 6px solid {MAROON};
    border-radius: 14px;
    padding: 12px 14px;
    margin-top: 10px;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.75), 0 6px 14px rgba(0,0,0,0.06);
    color: #1f2a2e;
    line-height: 1.55;
  }}

  @media (max-width: 640px) {{
    .lmcp-title {{ font-size: 17px; }}
  }}

  div.stLinkButton > a {{
    width: 100%;
    display: inline-flex;
    justify-content: center;
    padding: 12px 14px;
    border-radius: 14px;
    font-weight: 800;
    border: 1px solid rgba(0,0,0,0.08);
  }}
</style>
""",
    unsafe_allow_html=True,
)

# =============================
# HELPERS (Jou oorspronklike logika)
# =============================
U_TO_GR = {"U7": "Gr 1", "U8": "Gr 2", "U9": "Gr 3", "U10": "Gr 4", "U11": "Gr 5", "U12": "Gr 6", "U13": "Gr 7"}
GR_TO_U = {v: k for k, v in U_TO_GR.items()}
URL_RE = re.compile(r"(https?://[^\s\)\]\}<>\"']+)", re.IGNORECASE)

def safe_str(x) -> str: return "" if pd.isna(x) else str(x).strip()

def normalize_category(cat: str) -> str:
    c = safe_str(cat).lower()
    if "sport" in c: return "Sport"
    if "cultur" in c: return "Culture"
    if "academ" in c: return "Academics"
    return "Unknown"

def parse_under(value: str) -> str:
    v = safe_str(value)
    m = re.search(r"\bU\s*(\d{1,2})\b", v, flags=re.I)
    return f"U{int(m.group(1))}" if m else ""

def parse_grade(value: str) -> str:
    v = safe_str(value)
    m = re.search(r"\bGr\s*(\d)\b", v, flags=re.I)
    return f"Gr {int(m.group(1))}" if m else ""

def parse_date_smart(s: str) -> pd.Timestamp:
    raw = safe_str(s)
    if not raw: return pd.NaT
    dt = pd.to_datetime(raw, errors="coerce", dayfirst=False)
    if pd.isna(dt): dt = pd.to_datetime(raw, errors="coerce", dayfirst=True)
    return dt

def sa_long_date(dt: pd.Timestamp, raw_text: str) -> str:
    if pd.isna(dt): return safe_str(raw_text)
    return f"{dt.day} {dt.strftime('%B')} {dt.year}"

def split_info_text_and_links(info: str):
    raw = safe_str(info)
    if not raw: return "", []
    links = URL_RE.findall(raw)
    text = URL_RE.sub("", raw).strip(" -\n\t")
    return text, links

def afrikaans_title_and_subtitle(subject: str):
    s = safe_str(subject)
    low = s.lower()
    if "afrikaans" not in low: return "", s, False
    has_eat = "eat" in low
    title = "Afrikaans Eerste Addisionele Taal" if has_eat else "Afrikaans Hooftaal"
    remainder = re.sub(r"afrikaans|\(?\s*(EAT|HT)\s*\)?", "", s, flags=re.I)
    remainder = re.sub(r"[\-\(\)\[\]:]+", " ", remainder).strip()
    return title, remainder, True

# =============================
# SMART LOAD DATA (STABILITY)
# =============================
@st.cache_data(ttl=120)
def load_data_robust(url):
    try:
        # Gebruik 'n cache-buster om Google te dwing vir nuwe data
        r = requests.get(f"{url}&cb={int(time.time()/60)}", timeout=10)
        if r.status_code == 200 and "html" not in r.text.lower()[:100]:
            df_raw = pd.read_csv(io.StringIO(r.text))
            df_raw.columns = df_raw.columns.str.strip()
            return df_raw.fillna("")
        return None
    except:
        return None

# =============================
# MAIN APP EXECUTION
# =============================
try:
    st.image("LMCP_RGB (1).png", use_container_width=True)
except:
    pass

st.markdown('<div class="lmcp-divider"></div>', unsafe_allow_html=True)

df = load_data_robust(URL)

if df is None or df.empty:
    st.info("🔄 Connecting to the event hub... Please wait a few seconds.")
    if st.button("Manual Refresh"):
        st.cache_data.clear()
        st.rerun()
    st.stop()

# Prepare Data
COL_CAT, COL_SUBJ, COL_TEAM, COL_DATE, COL_VEN, COL_INFO, COL_LINK, COL_DURATION, COL_AGEGRADE = "Category", "Activity/Subject Name", "Team", "Date / Due Date", "Venue", "Information", "Programme / Document Link", "Display Duration", "Age Group (9,10) / Grade (1,2,3)"

df["_type"] = df[COL_CAT].apply(normalize_category)
df["_event_dt"] = df[COL_DATE].apply(parse_date_smart)
df["_under"] = df[COL_AGEGRADE].apply(parse_under)
df["_grade"] = df[COL_AGEGRADE].apply(parse_grade)
df = df.sort_values("_event_dt", ascending=True)

# Filters
st.markdown('<div class="lmcp-panel">', unsafe_allow_html=True)
sel_categories = st.multiselect("Category", ["Sport", "Culture", "Academics"], default=["Sport", "Culture", "Academics"])

colL, colR = st.columns(2)
with colL:
    sel_under = st.selectbox("Age Group", [""] + list(U_TO_GR.keys()))
with colR:
    sel_grade = st.selectbox("Grade", [""] + list(GR_TO_U.keys()))
st.markdown("</div>", unsafe_allow_html=True)

# Apply Logic
filtered = df[df["_type"].isin(sel_categories)].copy()
if sel_under:
    filtered = filtered[(filtered["_under"] == sel_under) | (filtered["_type"] == "Academics")]
if sel_grade:
    filtered = filtered[(filtered["_grade"] == sel_grade) | (filtered["_type"] != "Academics")]

# Render Cards
for _, row in filtered.iterrows():
    raw_subj = safe_str(row[COL_SUBJ])
    af_title, af_sub, is_af = afrikaans_title_and_subtitle(raw_subj)
    title = af_title if is_af else (safe_str(row[COL_TEAM]) if row[COL_TEAM] else raw_subj)
    subtitle = af_sub if is_af else (raw_subj if row[COL_TEAM] else "")
    
    info_text, info_links = split_info_text_and_links(row[COL_INFO])
    
    st.markdown(f"""
    <div class="lmcp-card">
        <div class="lmcp-title">{title}</div>
        {f'<div class="lmcp-subtitle">{subtitle}</div>' if subtitle else ''}
        <div class="lmcp-meta">📅 {sa_long_date(row["_event_dt"], row[COL_DATE])}<br>📍 {row[COL_VEN]}</div>
        {f'<div class="lmcp-info">{info_text}</div>' if info_text else ''}
    </div>
    """, unsafe_allow_html=True)
    
    if safe_str(row[COL_LINK]).startswith("http"):
        st.link_button("Dokument" if is_af else "Document", row[COL_LINK])
