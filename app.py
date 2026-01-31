import re
import streamlit as st
import pandas as pd
from datetime import datetime

# =============================
# PAGE CONFIG
# =============================
st.set_page_config(page_title="LMCP Event Hub", layout="wide")

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

# =============================
# BRAND COLORS
# =============================
MAROON = "#6b0019"
TEAL = "#0f5b66"
BG = "#f6f7fb"
TEAL_SHADE = "#e8f3f5"

# =============================
# CSS (minimal, smooth)
# =============================
st.markdown(
    f"""
<style>
  .stApp {{ background: {BG}; }}

  /* Soft card */
  .lmcp-card {{
    background: white;
    border-radius: 18px;
    padding: 16px;
    border: 1px solid rgba(0,0,0,0.06);
    box-shadow: 0 10px 18px rgba(0,0,0,0.06);
    margin-bottom: 14px;
  }}

  /* Filter panel */
  .lmcp-panel {{
    background: white;
    border-radius: 18px;
    padding: 14px 16px;
    border: 1px solid rgba(0,0,0,0.06);
    box-shadow: 0 8px 16px rgba(0,0,0,0.05);
    margin-bottom: 14px;
  }}

  /* Info block: 3D-ish */
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

  .lmcp-title {{
    font-size: 18px;
    font-weight: 900;
    margin: 0;
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
</style>
""",
    unsafe_allow_html=True,
)

# =============================
# HEADER with BANNER IMAGE
# =============================
# A smooth header feel: banner + subtle divider
try:
    st.image("LMCP_RGB (1).png", use_container_width=True)
except Exception:
    # If the file isn't in the repo, app still works.
    pass

st.markdown(
    f"""
<div style="
  height: 10px;
  background: linear-gradient(90deg, {MAROON}, {TEAL});
  border-radius: 999px;
  margin: 8px 0 18px 0;
  border: 2px solid rgba(0,0,0,0.06);
"></div>
""",
    unsafe_allow_html=True,
)

# =============================
# MAPPINGS
# =============================
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

# =============================
# HELPERS
# =============================
def safe_str(x) -> str:
    return "" if pd.isna(x) else str(x).strip()

def normalize_category(cat: str) -> str:
    c = safe_str(cat).lower()
    if re.search(r"\bsport(s)?\b", c):
        return "Sport"
    if re.search(r"\bcultur(e|al)?\b", c):
        return "Culture"
    if re.search(r"\bacadem(ic|ics)?\b", c):
        return "Academics"
    return "Unknown"

def parse_under(value: str) -> str:
    v = safe_str(value)
    if not v:
        return ""
    m = re.search(r"\bU\s*(\d{1,2})\b", v, flags=re.I)
    if m:
        return f"U{int(m.group(1))}"
    # numeric 7..13
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

def is_expired(row, today):
    """Expire only if duration > 0 and date is valid."""
    dt = row["_event_dt"]
    dur = row["_dur_days"]
    if pd.isna(dt) or dur is None or dur <= 0:
        return False
    expiry_date = dt.normalize() + pd.Timedelta(days=dur)
    return today > expiry_date

def sa_long_date(dt: pd.Timestamp, raw_text: str) -> str:
    if pd.isna(dt):
        return raw_text.strip()
    return f"{dt.day} {dt.strftime('%B')} {dt.year}"

# --- Afrikaans Title + Subtitle rules ---
def afrikaans_title_and_subtitle(subject: str):
    """
    If subject contains Afrikaans + HT/EAT:
      title = Afrikaans Hooftaal OR Afrikaans Eerste Addisionele Taal
      subtitle = what remains in the subject text (e.g. 'Gr 5 spelling')
    Never returns the word 'Activity'.
    """
    s = safe_str(subject)
    low = s.lower()

    if "afrikaans" not in low:
        return "", s, False

    has_eat = re.search(r"\beat\b", low) is not None
    has_ht = re.search(r"\bht\b", low) is not None

    if has_eat:
        title = "Afrikaans Eerste Addisionele Taal"
        remainder = re.sub(r"afrikaans", "", s, flags=re.I)
        remainder = re.sub(r"\beat\b", "", remainder, flags=re.I)
    elif has_ht:
        title = "Afrikaans Hooftaal"
        remainder = re.sub(r"afrikaans", "", s, flags=re.I)
        remainder = re.sub(r"\bht\b", "", remainder, flags=re.I)
    else:
        return "", s, False

    remainder = re.sub(r"[\-\(\)\[\]:]+", " ", remainder)
    remainder = re.sub(r"\s+", " ", remainder).strip(" -")

    # If nothing remains, just hide subtitle (do NOT show 'Activity')
    return title, remainder, True

def button_text(subject: str) -> str:
    title, _, is_af = afrikaans_title_and_subtitle(subject)
    return "Dokument" if is_af else "Document"

# --- Information parsing: extract links + clean text ---
URL_RE = re.compile(r"(https?://[^\s\)\]\}<>\"']+)", re.IGNORECASE)

def split_info_text_and_links(info: str):
    """
    Returns (text, links[])
    - If info has both text and links, both are returned.
    - Removes URLs from the text.
    """
    raw = safe_str(info)
    if not raw:
        return "", []

    links = URL_RE.findall(raw)
    # remove urls from text
    text = URL_RE.sub("", raw)
    # clean stray punctuation and whitespace
    text = re.sub(r"\s{2,}", " ", text).strip(" -\n\t")
    return text, links

# =============================
# LOAD DATA
# =============================
try:
    df = pd.read_csv(URL)
    df.columns = df.columns.str.strip()
    df = df.fillna("")
except Exception as e:
    st.error("Could not load data from Google Sheets.")
    st.code(str(e))
    st.stop()

if df.empty:
    st.info("Waiting for data from the sheet…")
    st.stop()

# Columns from your CSV
COL_CAT      = "Category"
COL_SUBJ     = "Activity/Subject Name"
COL_TEAM     = "Team"
COL_DATE     = "Date / Due Date"
COL_VEN      = "Venue"
COL_INFO     = "Information"
COL_LINK     = "Programme / Document Link"
COL_DURATION = "Display Duration"
COL_AGEGRADE = "Age Group (9,10) / Grade (1,2,3)"

# Prepare fields
df["_type"] = df[COL_CAT].apply(normalize_category)
df["_event_dt"] = pd.to_datetime(df[COL_DATE], errors="coerce", dayfirst=True)
df["_dur_days"] = df[COL_DURATION].apply(safe_int)

today = pd.Timestamp.now(tz="Africa/Johannesburg").normalize().tz_localize(None)
df = df[~df.apply(lambda r: is_expired(r, today), axis=1)].copy()

df["_under"] = df[COL_AGEGRADE].apply(parse_under)
df["_grade"] = df[COL_AGEGRADE].apply(parse_grade)

df["_sort_dt"] = df["_event_dt"].fillna(pd.Timestamp.max)
df = df.sort_values("_sort_dt", ascending=True)

# =============================
# SESSION STATE (keep Under when adding Academics)
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

st.markdown('<span class="label">Category</span>', unsafe_allow_html=True)
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

# Activity depends on Category
st.markdown('<span class="label" style="margin-top:10px;">Activity</span>', unsafe_allow_html=True)
df_cat = df[df["_type"].isin(st.session_state.sel_categories)].copy()
activity_options = sorted([safe_str(a) for a in df_cat[COL_SUBJ].unique() if safe_str(a)])
sel_acts = st.multiselect(
    "Activity",
    options=activity_options,
    default=[],
    key="activity_select",
    label_visibility="collapsed",
    placeholder="All activities",
)

# Age Group
st.markdown('<span class="label" style="margin-top:10px;">Age Group</span>', unsafe_allow_html=True)
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
        if st.session_state.sel_grade and not st.session_state.sel_under and want_under:
            st.session_state.sel_under = GR_TO_U.get(st.session_state.sel_grade, "")
    else:
        st.session_state.sel_grade = ""

st.markdown("</div>", unsafe_allow_html=True)

# =============================
# APPLY FILTERS
# =============================
filtered = df[df["_type"].isin(st.session_state.sel_categories)].copy()

if sel_acts:
    filtered = filtered[filtered[COL_SUBJ].isin(sel_acts)]

u = st.session_state.sel_under
if u and want_under:
    mask_sc = filtered["_type"].isin(["Sport", "Culture"])
    # keep blanks so we don't lose lots of rows
    filtered = filtered[~mask_sc | (filtered["_under"].eq(u) | filtered["_under"].eq(""))].copy()

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
# RENDER CARDS (smooth Streamlit feel)
# =============================
for _, row in filtered.iterrows():
    raw_subject = safe_str(row[COL_SUBJ])
    team = safe_str(row[COL_TEAM])
    venue = safe_str(row[COL_VEN])
    info_raw = safe_str(row[COL_INFO])
    link_main = safe_str(row[COL_LINK])

    # Date
    dt = row["_event_dt"]
    date_text = sa_long_date(dt, safe_str(row[COL_DATE]))

    # Afrikaans title/subtitle logic
    af_title, af_sub, is_af = afrikaans_title_and_subtitle(raw_subject)

    # Normal title/subtitle (avoid duplication)
    if is_af:
        title = af_title
        subtitle = af_sub  # can be empty -> we simply don't show it
    else:
        title = team if team else raw_subject
        subtitle = raw_subject if team else ""

    # Information: split text + links
    info_text, info_links = split_info_text_and_links(info_raw)

    # Button text rule
    btn_text_main = button_text(raw_subject)

    # Card container
    st.markdown('<div class="lmcp-card">', unsafe_allow_html=True)

    st.markdown(f"<div class='lmcp-title'>{title}</div>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(f"<div class='lmcp-subtitle'>{subtitle}</div>", unsafe_allow_html=True)

    st.markdown(
        f"<div class='lmcp-meta'>📅 {date_text}<br>📍 {venue}</div>",
        unsafe_allow_html=True
    )

    # Information display:
    # - text block if text exists
    if info_text:
        st.markdown(f"<div class='lmcp-info'>{info_text}</div>", unsafe_allow_html=True)

    # - buttons for links found in Information
    for idx, u_link in enumerate(info_links, start=1):
        st.link_button(f"More info {idx}", u_link)

    # - main document link (Programme / Document Link)
    if link_main.startswith("http"):
        st.link_button(btn_text_main, link_main)

    st.markdown("</div>", unsafe_allow_html=True)
