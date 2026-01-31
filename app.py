import re
import io
import requests
import pandas as pd
import streamlit as st
from requests.exceptions import RequestException, Timeout

# =============================
# BASIESE OPSET
# =============================
st.set_page_config(page_title="LMCP Event Hub", layout="centered")

# =============================
# STYL (Maroon + Teal, maar selfde feel)
# =============================
st.markdown(f"""
    <style>
    .stApp {{ background-color: #f8f9fa; font-family: Arial, sans-serif; }}
    .nav-bar {{
        background: linear-gradient(90deg, #6b0019, #0f5b66);
        color: white; padding: 18px; text-align: center;
        border-radius: 12px; margin-bottom: 18px;
        border: 3px solid rgba(255,255,255,0.25);
    }}
    .card {{
        background: white;
        padding: 18px;
        border-radius: 14px;
        border-left: 10px solid #6b0019;
        margin-bottom: 14px;
        box-shadow: 0 6px 14px rgba(0,0,0,0.08);
    }}
    .tag {{
        background: #0f5b66;
        color: white;
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 11px;
        font-weight: bold;
        display: inline-block;
    }}
    .info {{
        background: #e8f3f5;
        padding: 12px;
        border-radius: 10px;
        margin-top: 10px;
        border-left: 6px solid #6b0019;
        font-size: 14px;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.75);
    }}
    .meta {{
        color:#555;
        font-size: 14px;
        line-height: 1.6;
        margin-top: 8px;
    }}
    </style>
""", unsafe_allow_html=True)

# =============================
# BANNER (jou file naam)
# =============================
try:
    st.image("LMCP_RGB (1).png", use_container_width=True)
except Exception:
    pass

st.markdown('<div class="nav-bar"><h2 style="margin:0;">MIDSTREAM COLLEGE</h2><p style="margin:4px 0 0;">Primary Event Hub</p></div>', unsafe_allow_html=True)

# =============================
# GOOGLE SHEETS CSV URL
# =============================
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

# =============================
# SMART CACHING + TIMEOUT LOADER
# =============================
@st.cache_data(ttl=300, show_spinner=False)  # 5 minute cache
def load_sheet_csv(url: str) -> pd.DataFrame:
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=(5, 20))  # connect 5s, read 20s
    r.raise_for_status()

    text = r.text or ""
    # as Google per ongeluk HTML terug gee
    if "<html" in text.lower():
        raise ValueError("Google returned HTML instead of CSV. Check publish/share settings.")

    df = pd.read_csv(io.StringIO(text))
    df.columns = df.columns.str.strip()
    return df.fillna("")

# =============================
# HELPERS
# =============================
URL_RE = re.compile(r"(https?://[^\s\)\]\}<>\"']+)", re.IGNORECASE)

def safe_str(x) -> str:
    return "" if pd.isna(x) else str(x).strip()

def strip_urls(text: str) -> str:
    """Keer dat http links in headings/titles ‘pop’."""
    t = safe_str(text)
    t = URL_RE.sub("", t)
    t = re.sub(r"\s{2,}", " ", t).strip()
    return t

def normalize_category(cat: str) -> str:
    c = safe_str(cat).strip().lower()
    if "sport" in c:
        return "Sport"
    if "culture" in c:
        return "Culture"
    if "academ" in c:
        return "Academics"
    return safe_str(cat) or "Other"

def parse_date_smart(s: str):
    """
    Jou sheet se slash-dates is month/day (2/11/2026 = 11 February 2026).
    """
    raw = safe_str(s)
    if not raw:
        return pd.NaT

    if re.match(r"^\d{1,2}/\d{1,2}/\d{2,4}$", raw):
        dt = pd.to_datetime(raw, errors="coerce", dayfirst=False)  # month/day
        if not pd.isna(dt):
            return dt
        return pd.to_datetime(raw, errors="coerce", dayfirst=True)

    dt = pd.to_datetime(raw, errors="coerce", dayfirst=True)
    return dt

def sa_long_date(dt: pd.Timestamp, raw_text: str) -> str:
    if pd.isna(dt):
        return safe_str(raw_text)
    return f"{dt.day} {dt.strftime('%B')} {dt.year}"

def safe_int(x):
    try:
        s = str(x).strip()
        if s == "":
            return None
        return int(float(s))
    except:
        return None

def is_expired(row, today):
    dt = row["_event_dt"]
    dur = row["_dur_days"]
    if pd.isna(dt) or dur is None or dur <= 0:
        return False
    expiry_date = dt.normalize() + pd.Timedelta(days=dur)
    return today > expiry_date

def split_info_text_and_links(info: str):
    raw = safe_str(info)
    if not raw:
        return "", []
    links = URL_RE.findall(raw)
    text = URL_RE.sub("", raw)
    text = re.sub(r"\s{2,}", " ", text).strip(" -\n\t")
    return text, links

def afrikaans_title_and_subtitle(subject: str):
    """
    - EAT/HT mag nooit wys nie (ook nie (EAT) brackets)
    - Title word vol-uit geskryf
    - Subtitle = oorblywende activity text (bv 'Gr 5 spelling')
    """
    s = safe_str(subject)
    low = s.lower()
    if "afrikaans" not in low:
        return "", s, False

    has_eat = re.search(r"\beat\b", low) is not None
    has_ht  = re.search(r"\bht\b", low) is not None

    if has_eat:
        title = "Afrikaans Eerste Addisionele Taal"
        remainder = re.sub(r"afrikaans", "", s, flags=re.I)
        remainder = re.sub(r"\(?\s*EAT\s*\)?", "", remainder, flags=re.I)
    elif has_ht:
        title = "Afrikaans Hooftaal"
        remainder = re.sub(r"afrikaans", "", s, flags=re.I)
        remainder = re.sub(r"\(?\s*HT\s*\)?", "", remainder, flags=re.I)
    else:
        return "", s, False

    remainder = re.sub(r"[\-\(\)\[\]:]+", " ", remainder)
    remainder = re.sub(r"\s+", " ", remainder).strip(" -")
    return title, remainder, True

def doc_button_text(subject: str) -> str:
    _, _, is_af = afrikaans_title_and_subtitle(subject)
    return "Dokument" if is_af else "Document"

# =============================
# LOAD DATA (met netjiese errors)
# =============================
try:
    df = load_sheet_csv(URL)
except Timeout:
    st.warning("⏳ Google Sheets is taking too long. Please try again.")
    if st.button("Retry"):
        st.cache_data.clear()
        st.rerun()
    st.stop()
except RequestException:
    st.warning("⚠️ Could not connect to Google Sheets right now. Please try again shortly.")
    if st.button("Retry"):
        st.cache_data.clear()
        st.rerun()
    st.stop()
except Exception as e:
    st.warning("⚠️ Something went wrong while loading the sheet.")
    with st.expander("Technical details"):
        st.code(str(e))
    if st.button("Retry"):
        st.cache_data.clear()
        st.rerun()
    st.stop()

if df.empty:
    st.info("Waiting for data…")
    st.stop()

# Optional refresh
if st.button("🔄 Refresh data"):
    st.cache_data.clear()
    st.rerun()

# =============================
# COLUMN NAMES (jou sheet)
# =============================
COL_CAT      = "Category"
COL_SUBJ     = "Activity/Subject Name"
COL_TEAM     = "Team"
COL_DATE     = "Date / Due Date"
COL_VEN      = "Venue"
COL_INFO     = "Information"
COL_LINK     = "Programme / Document Link"
COL_DURATION = "Display Duration"
COL_GRADE    = "Age Group (9,10) / Grade (1,2,3)"

# =============================
# PREPARE DATA
# =============================
df["_type"] = df[COL_CAT].apply(normalize_category)
df["_event_dt"] = df[COL_DATE].apply(parse_date_smart)
df["_dur_days"] = df[COL_DURATION].apply(safe_int)

today = pd.Timestamp.now(tz="Africa/Johannesburg").normalize().tz_localize(None)
df = df[~df.apply(lambda r: is_expired(r, today), axis=1)].copy()

df["_sort_dt"] = df["_event_dt"].fillna(pd.Timestamp.max)
df = df.sort_values("_sort_dt", ascending=True)

# =============================
# FILTERS (soos jy wou)
# =============================
cats = ["Sport", "Culture", "Academics"]
sel_cat = st.multiselect("Category", cats, default=cats)

# Activity pull net uit geselekteerde Category
df_cat = df[df["_type"].isin(sel_cat)].copy()
act_options = sorted([safe_str(a) for a in df_cat[COL_SUBJ].unique() if safe_str(a)])
sel_act = st.selectbox("Activity", ["All"] + act_options, index=0)

filtered = df[df["_type"].isin(sel_cat)].copy()
if sel_act != "All":
    filtered = filtered[filtered[COL_SUBJ].eq(sel_act)]

st.caption(f"Showing {len(filtered)} item(s).")

# =============================
# DISPLAY (jou ou card look)
# =============================
for _, row in filtered.iterrows():
    cat   = safe_str(row["_type"])
    subj_raw = safe_str(row[COL_SUBJ])
    team_raw = safe_str(row[COL_TEAM])
    date_raw = safe_str(row[COL_DATE])
    ven   = safe_str(row[COL_VEN])
    info_raw = safe_str(row[COL_INFO])
    link_main = safe_str(row[COL_LINK])

    dt = row["_event_dt"]
    date_text = sa_long_date(dt, date_raw)

    # Afrikaans rule
    af_title, af_sub, is_af = afrikaans_title_and_subtitle(subj_raw)

    if is_af:
        title = af_title
        subtitle = af_sub
    else:
        title = team_raw if team_raw else subj_raw
        subtitle = subj_raw if team_raw else ""

    # stop URL “popping” in titles/subtitles
    title = strip_urls(title)
    subtitle = strip_urls(subtitle)

    # Information: text + links
    info_text, info_links = split_info_text_and_links(info_raw)

    st.markdown(f"""
        <div class="card">
            <span class="tag">{cat}</span>
            <div style="margin-top:10px; font-weight:800; font-size:1.15rem;">{title}</div>
            {f'<div style="color:#0f5b66; font-weight:700; margin-top:6px;">{subtitle}</div>' if subtitle else ''}
            <div class="meta">
                📅 {date_text}<br>
                📍 {ven}
            </div>
            {f'<div class="info">{info_text}</div>' if info_text else ''}
        </div>
    """, unsafe_allow_html=True)

    # Buttons (nie “full screen” forced nie—default Streamlit)
    col1, col2 = st.columns([4, 1])
    with col2:
        # Links inside Information
        for i, lnk in enumerate(info_links, start=1):
            st.link_button(f"Info {i}", lnk)

        # Main document link
        if link_main.startswith("http"):
            st.link_button(doc_button_text(subj_raw), link_main)
