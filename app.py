import streamlit as st
import pandas as pd

import re
import io
import requests
from requests.exceptions import RequestException, Timeout

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="LMCP Event Hub", layout="centered", initial_sidebar_state="collapsed")

# =============================
# STYLE (your original)
# =============================
st.markdown("""
<style>
.stApp { background-color: #f8f9fa; }

.nav-bar {
  background-color: #800000;
  color: white;
  padding: 20px;
  text-align: center;
  border-radius: 10px;
  margin-bottom: 20px;
}

.card {
  background: white;
  padding: 20px;
  border-radius: 12px;
  border-left: 10px solid #800000;
  margin-bottom: 15px;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

.tag {
  background: #800000;
  color: white;
  padding: 3px 10px;
  border-radius: 8px;
  font-size: 11px;
  font-weight: bold;
  display: inline-block;
}

.info {
  background: #f1f3f5;
  padding: 10px;
  border-radius: 8px;
  margin-top: 10px;
  border-left: 4px solid #008080;
  font-size: 14px;
}

/* Button inside card */
.docbtn {
  display: inline-block;
  margin-top: 12px;
  padding: 10px 14px;
  background: #008080;
  color: white !important;
  text-decoration: none;
  border-radius: 8px;
  font-weight: 700;
  font-size: 14px;
}
.docbtn:hover { filter: brightness(0.95); }

.smallbtn {
  display: inline-block;
  margin-top: 8px;
  margin-right: 8px;
  padding: 9px 12px;
  background: #800000;
  color: white !important;
  text-decoration: none;
  border-radius: 8px;
  font-weight: 700;
  font-size: 13px;
}
.smallbtn:hover { filter: brightness(0.95); }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="nav-bar"><h1>MIDSTREAM COLLEGE</h1><p>PRIMARY EVENT HUB</p></div>', unsafe_allow_html=True)

# =============================
# SHEET URL
# =============================
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

# =============================
# ANTI CRASH loader (timeout+cache)
# =============================
@st.cache_data(ttl=300, show_spinner=False)
def load_sheet_csv(url: str) -> pd.DataFrame:
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=(5, 20))
    r.raise_for_status()
    text = r.text or ""
    if "<html" in text.lower():
        raise ValueError("Google returned HTML instead of CSV.")
    df = pd.read_csv(io.StringIO(text)).fillna("")
    df.columns = df.columns.str.strip()
    return df

# =============================
# HELPERS
# =============================
URL_RE = re.compile(r"(https?://[^\s\)\]\}<>\"']+)", re.IGNORECASE)

def safe_str(x) -> str:
    return "" if pd.isna(x) else str(x).strip()

def format_subject(subject: str) -> str:
    """
    Replace EAT/HT in Afrikaans subject with full words.
    Also remove duplicates like: "EAT EAT".
    """
    s = safe_str(subject)

    # Make replacements
    # Afrikaans EAT / HT
    if re.search(r"\bEAT\b", s, flags=re.I) and "Afrikaans" in s:
        s = re.sub(r"\bAfrikaans\b", "Afrikaans", s, flags=re.I)
        s = re.sub(r"\bEAT\b", "", s, flags=re.I)
        s = re.sub(r"\s+", " ", s).strip()
        return "Afrikaans Eerste Addisionele Taal" + (f" - {s}" if s and s.lower() != "afrikaans" else "")

    if re.search(r"\bHT\b", s, flags=re.I) and "Afrikaans" in s:
        s = re.sub(r"\bAfrikaans\b", "Afrikaans", s, flags=re.I)
        s = re.sub(r"\bHT\b", "", s, flags=re.I)
        s = re.sub(r"\s+", " ", s).strip()
        return "Afrikaans Hooftaal" + (f" - {s}" if s and s.lower() != "afrikaans" else "")

    # If it is just EAT / HT alone
    if s.strip().upper() == "EAT":
        return "Afrikaans Eerste Addisionele Taal"
    if s.strip().upper() == "HT":
        return "Afrikaans Hooftaal"

    return s

def parse_date_smart(raw: str):
    """
    Your CSV date like 05/02/2026 means 5 Feb (month/day).
    """
    raw = safe_str(raw)
    if not raw:
        return pd.NaT

    if re.match(r"^\d{1,2}/\d{1,2}/\d{2,4}$", raw):
        dt = pd.to_datetime(raw, errors="coerce", dayfirst=False)
        if not pd.isna(dt):
            return dt

    return pd.to_datetime(raw, errors="coerce", dayfirst=True)

def format_date(raw: str) -> str:
    dt = parse_date_smart(raw)
    if pd.isna(dt):
        return safe_str(raw)
    return f"{dt.day} {dt.strftime('%B')} {dt.year}"

def split_info(info_text: str):
    """
    If Information contains link(s), convert them to buttons and keep remaining text.
    """
    raw = safe_str(info_text)
    if not raw:
        return "", []

    links = URL_RE.findall(raw)
    text = URL_RE.sub("", raw)
    text = re.sub(r"\s{2,}", " ", text).strip(" -\n\t")
    return text, links

# =============================
# LOAD DATA
# =============================
try:
    df = load_sheet_csv(URL)
except Timeout:
    st.error("Kon nie tans met Google Sheets koppel nie (timeout). Probeer later weer.")
    st.stop()
except RequestException:
    st.error("Kon nie tans met Google Sheets koppel nie (connection). Probeer later weer.")
    st.stop()
except Exception as e:
    st.error("Kon nie tans met Google Sheets koppel nie.")
    with st.expander("Technical details"):
        st.code(str(e))
    st.stop()

# =============================
# COLUMN NAMES (stable)
# =============================
COL_CAT   = "Category"
COL_SUBJ  = "Activity/Subject Name"
COL_TEAM  = "Team"
COL_DATE  = "Date / Due Date"
COL_VEN   = "Venue"
COL_INFO  = "Information"
COL_LINK  = "Programme / Document Link"
COL_GRADE = "Age Group (9,10) / Grade (1,2,3)"

# =============================
# FILTER
# =============================
cats = sorted([c for c in df[COL_CAT].astype(str).unique() if str(c).strip()])
sel_cat = st.multiselect("Kies Kategorie:", cats)

# =============================
# DISPLAY
# =============================
for _, row in df.iterrows():
    c_cat   = safe_str(row.get(COL_CAT, ""))
    c_subj  = safe_str(row.get(COL_SUBJ, ""))
    c_team  = safe_str(row.get(COL_TEAM, ""))
    c_date  = safe_str(row.get(COL_DATE, ""))
    c_ven   = safe_str(row.get(COL_VEN, ""))
    c_info  = safe_str(row.get(COL_INFO, ""))
    c_grade = safe_str(row.get(COL_GRADE, ""))
    c_link  = safe_str(row.get(COL_LINK, ""))

    if sel_cat and c_cat not in sel_cat:
        continue

    # Fix subject display
    subj_fixed = format_subject(c_subj)

    # Title rule (no duplicates)
    title = c_team if len(c_team) > 1 and c_team.lower() != c_subj.lower() else subj_fixed

    # Date format
    date_fixed = format_date(c_date)

    # Info split
    info_text, info_links = split_info(c_info)

    # Main doc button inside card
    main_btn = ""
    if c_link.startswith("http"):
        main_btn = f'<a class="docbtn" href="{c_link}" target="_blank" rel="noopener noreferrer">Document</a>'

    # Info link buttons inside card too
    info_btns = ""
    for i, lnk in enumerate(info_links, start=1):
        info_btns += f'<a class="smallbtn" href="{lnk}" target="_blank" rel="noopener noreferrer">Info {i}</a>'

    st.markdown(f"""
    <div class="card">
        <span class="tag">{c_cat}</span>

        <div style="color:#008080; font-weight:bold; margin-top:10px;">{subj_fixed}</div>

        <div style="font-size:1.2rem; font-weight:bold; margin-top:4px;">{title}</div>

        <div style="color:#555; font-size:14px; margin-top:8px;">
            {c_grade}<br>
            📅 {date_fixed}<br>
            📍 {c_ven}
        </div>

        {f'<div class="info">{info_text}</div>' if info_text else ''}

        {info_btns}
        {main_btn}
    </div>
    """, unsafe_allow_html=True)
