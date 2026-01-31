import re
import io
import requests
import pandas as pd
import streamlit as st
from requests.exceptions import RequestException, Timeout

# =============================
# PAGE CONFIG (mobile friendly)
# =============================
st.set_page_config(page_title="LMCP Event Hub", layout="centered")

# =============================
# GOOGLE SHEETS CSV
# =============================
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

# =============================
# BRAND COLORS
# =============================
MAROON = "#6b0019"
TEAL = "#0f5b66"
BG = "#f6f7fb"
TEAL_SHADE = "#e8f3f5"

# =============================
# CSS (smooth, mobile, not "HTML-y")
# =============================
st.markdown(
    f"""
<style>
  .stApp {{
    background: {BG};
    font-family: "Segoe UI Variable", "Segoe UI", system-ui, -apple-system, "SF Pro Display",
                 Roboto, "Helvetica Neue", Arial, sans-serif;
  }}

  section.main > div {{
    max-width: 880px;
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

  /* Info block: maroon side + teal shade */
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
    section.main > div {{
      padding-left: 0.75rem;
      padding-right: 0.75rem;
    }}
    .lmcp-card {{
      padding: 14px;
    }}
    .lmcp-title {{
      font-size: 17px;
    }}
  }}
</style>
""",
    unsafe_allow_html=True,
)

# =============================
# HEADER BANNER (file must exist in repo)
# =============================
try:
    st.image("LMCP_RGB (1).png", use_container_width=True)
except Exception:
    # App still works even if banner missing
    pass
st.markdown('<div class="lmcp-divider"></div>', unsafe_allow_html=True)

# =============================
# SMART CACHE + TIMEOUT CSV LOADER
# =============================
@st.cache_data(ttl=300, show_spinner=False)  # 5 min cache
def load_sheet_csv(url: str) -> pd.DataFrame:
    headers = {"User-Agent": "Mozilla/5.0"}
    # timeout = (connect, read)
    r = requests.get(url, headers=headers, timeout=(5, 20))
    r.raise_for_status()

    # Sometimes Google returns HTML error page instead of CSV
    content_type = (r.headers.get("Content-Type") or "").lower()
    text = r.text or ""

    if "text/html" in content_type and "csv" not in content_type:
        raise ValueError("Google returned HTML instead of CSV.")
    if "<html" in text.lower():
        raise ValueError("Google returned an HTML page instead of CSV.")

    df = pd.read_csv(io.StringIO(text))
    df.columns = df.columns.str.strip()
    return df.fillna("")

# =============================
# HELPERS
# =============================
URL_RE = re.compile(r"(https?://[^\s\)\]\}<>\"']+)", re.IGNORECASE)

U_TO_GR = {
    "U7": "Gr 1",
    "U8": "Gr 2",
    "U9": "Gr 3",
    "U10": "Gr 4",
    "U11": "Gr 5",
    "U12": "Gr 6",
    "U13": "Gr 7",
}
GR_TO_U = {v: k for k, v in U_TO_GR.items()}

def safe_str(x) -> str:
    return "" if pd.isna(x) else str(x).strip()

def normalize_category(cat: str) -> str:
    """
    STRICT:
    if Category contains 'sport' -> Sport
    if contains 'culture' -> Culture
    if contains 'academ' -> Academics
    else Unknown
    """
    c = safe_str(cat).strip().lower()
    if "sport" in c:
        return "Sport"
    if "culture" in c:
        return "Culture"
    if "academ" in c:
        return "Academics"
    return "Unknown"

def parse_under(value: str) -> str:
    v = safe_str(value)
    if not v:
        return ""
    m = re.search(r"\bU\s*(\d{1,2})\b", v, flags=re.I)
    if m:
        return f"U{int(m.group(1))}"
    m2 = re.search(r"\b(\d{1,2})\b", v)
    if m2:
        age = int(m2.group(1))
        if 7 <= age <= 13:
            return f"U{age}"
    return ""

def parse_grade(value: str) -> str:
    v = safe_str(value)
    if not v:
        return ""
    m = re.search(r"\bGr\s*(\d)\b", v, flags=re.I)
    if m:
        return f"Gr {int(m.group(1))}"
    m2 = re.search(r"\b(\d{1,2})\b", v)
    if m2:
        n = int(m2.group(1))
        if 7 <= n <= 13:
            return U_TO_GR.get(f"U{n}", "")
        if 1 <= n <= 7:
            return f"Gr {n}"
    return ""

def safe_int(x):
    try:
        s = str(x).strip()
        if s == "":
            return None
        return int(float(s))
    except:
        return None

def parse_date_smart(s: str):
    """
    Your slash dates behave like month/day (e.g. 2/11/2026 = 11 February 2026)
    So try dayfirst=False first for slash pattern.
    """
    raw = safe_str(s)
    if not raw:
        return pd.NaT

    if re.match(r"^\d{1,2}/\d{1,2}/\d{2,4}$", raw):
        dt = pd.to_datetime(raw, errors="coerce", dayfirst=False)
        if not pd.isna(dt):
            return dt
        return pd.to_datetime(raw, errors="coerce", dayfirst=True)

    dt = pd.to_datetime(raw, errors="coerce")
    if not pd.isna(dt):
        return dt
    return pd.to_datetime(raw, errors="coerce", dayfirst=True)

def sa_long_date(dt: pd.Timestamp, raw_text: str) -> str:
    if pd.isna(dt):
        return safe_str(raw_text)
    return f"{dt.day} {dt.strftime('%B')} {dt.year}"

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
    Remove any EAT/HT token (also (EAT)/(HT)) and NEVER show EAT/HT anywhere.
    Title becomes full phrase.
    Subtitle becomes remaining activity text (can be blank).
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
# LOAD DATA WITH ERROR HANDLING
# =============================
st.caption("Loading events…")

try:
    df = load_sheet_csv(URL)

except Timeout:
    st.warning("⏳ The Google Sheet took too long to respond. Please try again.")
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
    st.info("No data found yet.")
    st.stop()

# Optional manual refresh
with st.container():
    colA, colB = st.columns([1, 1])
    with colB:
        if st.button("🔄 Refresh data"):
            st.cache_data.clear()
            st.rerun()

# =============================
# EXPECTED COLUMNS
# =============================
COL_CAT      = "Category"
COL_SUBJ     = "Activity/Subject Name"
COL_TEAM     = "Team"
COL_DATE     = "Date / Due Date"
COL_VEN      = "Venue"
COL_INFO     = "Information"
COL_LINK     = "Programme / Document Link"
COL_DURATION = "Display Duration"
COL_AGEGRADE = "Age Group (9,10) / Grade (1,2,3)"

# =============================
# DERIVED FIELDS
# =============================
df["_type"] = df[COL_CAT].apply(normalize_category)
df["_event_dt"] = df[COL_DATE].apply(parse_date_smart)
df["_dur_days"] = df[COL_DURATION].apply(safe_int)

today = pd.Timestamp.now(tz="Africa/Johannesburg").normalize().tz_localize(None)
df = df[~df.apply(lambda r: is_expired(r, today), axis=1)].copy()

df["_under"] = df[COL_AGEGRADE].apply(parse_under)
df["_grade"] = df[COL_AGEGRADE].apply(parse_grade)

df["_sort_dt"] = df["_event_dt"].fillna(pd.Timestamp.max)
df = df.sort_values("_sort_dt", ascending=True)

# =============================
# SESSION STATE
# =============================
if "sel_categories" not in st.session_state:
    st.session_state.sel_categories = ["Sport", "Culture", "Academics"]
if "sel_under" not in st.session_state:
    st.session_state.sel_under = ""
if "sel_grade" not in st.session_state:
    st.session_state.sel_grade = ""

# =============================
# FILTER PANEL
# =============================
st.markdown('<div class="lmcp-panel">', unsafe_allow_html=True)

st.markdown("**Category**")
all_cats = ["Sport", "Culture", "Academics"]
st.session_state.sel_categories = st.multiselect(
    "Category",
    options=all_cats,
    default=st.session_state.sel_categories,
    key="category_select",
    label_visibility="collapsed",
)
if not st.session_state.sel_categories:
    st.session_state.sel_categories = ["Sport", "Culture", "Academics"]

# Activity pulls ONLY from selected category(s)
df_cat = df[df["_type"].isin(st.session_state.sel_categories)].copy()
activity_options = sorted([safe_str(a) for a in df_cat[COL_SUBJ].unique() if safe_str(a)])

st.markdown("**Activity**")
sel_act = st.selectbox(
    "Activity",
    options=["All"] + activity_options,
    index=0,
    key="activity_select_one",
    label_visibility="collapsed",
)

st.markdown("**Age Group**")
want_under = any(c in st.session_state.sel_categories for c in ["Sport", "Culture"])
want_grade = "Academics" in st.session_state.sel_categories

colL, colR = st.columns(2)
with colL:
    if want_under:
        under_options = [""] + list(U_TO_GR.keys())
        st.session_state.sel_under = st.selectbox(
            "Under",
            options=under_options,
            index=under_options.index(st.session_state.sel_under) if st.session_state.sel_under in under_options else 0,
            key="under_select",
            label_visibility="collapsed",
        )
        # Keep grade in sync when adding Academics
        if st.session_state.sel_under and not st.session_state.sel_grade:
            st.session_state.sel_grade = U_TO_GR.get(st.session_state.sel_under, "")
    else:
        st.session_state.sel_under = ""

with colR:
    if want_grade:
        grade_options = [""] + list(GR_TO_U.keys())
        st.session_state.sel_grade = st.selectbox(
            "Grade",
            options=grade_options,
            index=grade_options.index(st.session_state.sel_grade) if st.session_state.sel_grade in grade_options else 0,
            key="grade_select",
            label_visibility="collapsed",
        )
        # Keep under in sync if Sport/Culture also selected
        if st.session_state.sel_grade and not st.session_state.sel_under and want_under:
            st.session_state.sel_under = GR_TO_U.get(st.session_state.sel_grade, "")
    else:
        st.session_state.sel_grade = ""

st.markdown("</div>", unsafe_allow_html=True)

# =============================
# APPLY FILTERS
# =============================
filtered = df[df["_type"].isin(st.session_state.sel_categories)].copy()

# Activity filter
if sel_act != "All":
    filtered = filtered[filtered[COL_SUBJ].eq(sel_act)]

# Under filter only for Sport/Culture
u = st.session_state.sel_under
if u and want_under:
    mask_sc = filtered["_type"].isin(["Sport", "Culture"])
    # keep blanks so sport rows without under won't disappear
    filtered = filtered[~mask_sc | (filtered["_under"].eq(u) | filtered["_under"].eq(""))].copy()

# Grade filter for Academics (selected OR inferred from Under)
grade_for_acad = st.session_state.sel_grade
if (not grade_for_acad) and u:
    grade_for_acad = U_TO_GR.get(u, "")

if grade_for_acad and want_grade:
    mask_ac = filtered["_type"].eq("Academics")
    filtered = filtered[~mask_ac | (filtered["_grade"].eq(grade_for_acad) | filtered["_grade"].eq(""))].copy()

st.caption(f"Showing {len(filtered)} item(s).")
if filtered.empty:
    st.info("No items match your filters. Try clearing Activity or Age Group.")
    st.stop()

# =============================
# RENDER CARDS (buttons not full screen)
# =============================
for _, row in filtered.iterrows():
    raw_subject = safe_str(row[COL_SUBJ])
    team = safe_str(row[COL_TEAM])
    venue = safe_str(row[COL_VEN])
    info_raw = safe_str(row[COL_INFO])
    link_main = safe_str(row[COL_LINK])

    # SA long date with smart parsing
    dt = row["_event_dt"]
    date_text = sa_long_date(dt, safe_str(row[COL_DATE]))

    # Afrikaans formatting
    af_title, af_sub, is_af = afrikaans_title_and_subtitle(raw_subject)

    if is_af:
        title = af_title
        subtitle = af_sub  # do not show word "Activity"
    else:
        title = team if team else raw_subject
        subtitle = raw_subject if team else ""

    # Information -> text + links
    info_text, info_links = split_info_text_and_links(info_raw)

    st.markdown('<div class="lmcp-card">', unsafe_allow_html=True)

    st.markdown(f"<div class='lmcp-title'>{title}</div>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(f"<div class='lmcp-subtitle'>{subtitle}</div>", unsafe_allow_html=True)

    st.markdown(
        f"<div class='lmcp-meta'>📅 {date_text}<br>📍 {venue}</div>",
        unsafe_allow_html=True
    )

    # Text info block
    if info_text:
        st.markdown(f"<div class='lmcp-info'>{info_text}</div>", unsafe_allow_html=True)

    # Buttons in a small right column
    content_col, buttons_col = st.columns([4, 1])
    with buttons_col:
        # Information links as buttons
        for idx, u_link in enumerate(info_links, start=1):
            st.link_button(f"Info {idx}", u_link)

        # Main document link button
        if link_main.startswith("http"):
            st.link_button(doc_button_text(raw_subject), link_main)

    st.markdown("</div>", unsafe_allow_html=True)
