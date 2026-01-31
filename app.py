import re
import streamlit as st
import pandas as pd

# =============================
# PAGE CONFIG
# =============================
st.set_page_config(page_title="LMCP Event Hub", layout="wide")

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

# =============================
# BRAND COLORS (Maroon + Teal)
# =============================
MAROON = "#6b0019"
TEAL   = "#0f5b66"
BG     = "#f6f7fb"

# =============================
# STYLING
# =============================
st.markdown(f"""
<style>
    .stApp {{ background: {BG}; }}

    .topbar {{
        background: linear-gradient(90deg, {MAROON}, {TEAL});
        color: white;
        padding: 18px 22px;
        border-radius: 18px;
        margin-bottom: 14px;
        border: 3px solid rgba(255,255,255,0.35); /* banner border */
        box-shadow: 0 10px 18px rgba(0,0,0,0.10);
    }}
    .topbar h1 {{ margin: 0; font-size: 22px; letter-spacing: 0.4px; }}
    .topbar p {{ margin: 2px 0 0; opacity: 0.95; }}

    .panel {{
        background: white;
        border-radius: 18px;
        padding: 14px 16px;
        box-shadow: 0 6px 16px rgba(0,0,0,0.08);
        margin-bottom: 12px;
        border: 1px solid rgba(0,0,0,0.04);
    }}

    .label {{
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 0.2px;
        color: #2c2c2c;
        margin-bottom: 6px;
        display: block;
    }}

    .cardbox {{
        background: white;
        border-radius: 20px;
        padding: 14px 14px;
        border: 1px solid rgba(0,0,0,0.06);
        box-shadow: 0 10px 18px rgba(0,0,0,0.08);
        margin-bottom: 12px;
    }}
    .title {{
        font-size: 18px;
        font-weight: 900;
        margin: 0;
    }}
    .subtitle {{
        font-size: 14px;
        font-weight: 800;
        color: {TEAL};
        margin-top: 6px;
    }}
    .meta {{
        color: #555;
        font-size: 14px;
        margin-top: 10px;
        line-height: 1.6;
    }}
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="topbar">
  <h1>MIDSTREAM COLLEGE</h1>
  <p>Primary Event Hub</p>
</div>
""", unsafe_allow_html=True)

# =============================
# MAPPINGS (U -> Grade)
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

def sa_long_date(dt: pd.Timestamp, raw_text: str) -> str:
    """Return '11 February 2026'. If dt invalid, return raw."""
    if pd.isna(dt):
        return raw_text.strip()
    month = dt.strftime("%B")
    return f"{dt.day} {month} {dt.year}"

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

def is_expired(row, today):
    """Expire only if duration > 0 and date is valid."""
    dt = row["_event_dt"]
    dur = row["_dur_days"]
    if pd.isna(dt) or dur is None or dur <= 0:
        return False
    expiry_date = dt.normalize() + pd.Timedelta(days=dur)
    return today > expiry_date

# ---- Afrikaans formatting rules ----
def classify_afrikaans(subject: str):
    """
    Returns (main_title, second_line_activity, is_afrikaans_row)
    - main_title: Afrikaans Eerste Addisionele Taal / Afrikaans Hooftaal
    - second line: rest of the activity text (no duplication)
    """
    s = safe_str(subject)
    low = s.lower()

    if "afrikaans" not in low:
        return "", s, False

    # Detect EAT/HT even if written with spaces/dashes/brackets
    eat = re.search(r"\beat\b", low) is not None
    ht  = re.search(r"\bht\b", low) is not None

    if eat:
        main = "Afrikaans Eerste Addisionele Taal"
        # remove "afrikaans" + any eat tokens from the remainder
        remainder = re.sub(r"afrikaans", "", s, flags=re.I)
        remainder = re.sub(r"\beat\b", "", remainder, flags=re.I)
        remainder = re.sub(r"[\-\(\)\[\]:]+", " ", remainder)
        remainder = re.sub(r"\s+", " ", remainder).strip(" -")
        return main, (remainder if remainder else "Activity"), True

    if ht:
        main = "Afrikaans Hooftaal"
        remainder = re.sub(r"afrikaans", "", s, flags=re.I)
        remainder = re.sub(r"\bht\b", "", remainder, flags=re.I)
        remainder = re.sub(r"[\-\(\)\[\]:]+", " ", remainder)
        remainder = re.sub(r"\s+", " ", remainder).strip(" -")
        return main, (remainder if remainder else "Activity"), True

    # Afrikaans but no HT/EAT token – keep as normal
    return "", s, False

def button_text_for_row(subject: str) -> str:
    # If Afrikaans row (EAT/HT) -> Afrikaans button
    main, _, is_af = classify_afrikaans(subject)
    return "Dokument" if is_af else "Document"

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

# Normalize fields
df["_type"] = df[COL_CAT].apply(normalize_category)

# Parse date for sorting + expiry + formatting
df["_event_dt"] = pd.to_datetime(df[COL_DATE], errors="coerce", dayfirst=True)
df["_dur_days"] = df[COL_DURATION].apply(safe_int)

today = pd.Timestamp.now(tz="Africa/Johannesburg").normalize().tz_localize(None)
df = df[~df.apply(lambda r: is_expired(r, today), axis=1)].copy()

# Under / grade
df["_under"] = df[COL_AGEGRADE].apply(parse_under)
df["_grade"] = df[COL_AGEGRADE].apply(parse_grade)

# Sort by date (nearest first; unknown last)
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
st.markdown('<div class="panel">', unsafe_allow_html=True)

# Category
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

# Activity (changes per category)
st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)
st.markdown('<span class="label">Activity</span>', unsafe_allow_html=True)

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
st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)
st.markdown('<span class="label">Age Group</span>', unsafe_allow_html=True)

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
        # keep grade in sync when adding academics later
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
        # keep under in sync if sport/culture also selected
        if st.session_state.sel_grade and not st.session_state.sel_under and want_under:
            st.session_state.sel_under = GR_TO_U.get(st.session_state.sel_grade, "")
    else:
        st.session_state.sel_grade = ""

st.markdown('</div>', unsafe_allow_html=True)

# =============================
# APPLY FILTERS
# =============================
filtered = df[df["_type"].isin(st.session_state.sel_categories)].copy()

# Activity filter
if sel_acts:
    filtered = filtered[filtered[COL_SUBJ].isin(sel_acts)]

# Under filter for sport/culture rows
u = st.session_state.sel_under
if u and want_under:
    mask_sc = filtered["_type"].isin(["Sport", "Culture"])
    filtered = filtered[~mask_sc | (filtered["_under"].eq(u) | filtered["_under"].eq(""))].copy()

# Grade filter for academics rows (grade or inferred from under)
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
# RENDER CARDS
# =============================
for _, row in filtered.iterrows():
    raw_subject = safe_str(row[COL_SUBJ])
    team        = safe_str(row[COL_TEAM])
    venue       = safe_str(row[COL_VEN])
    info        = safe_str(row[COL_INFO])
    link        = safe_str(row[COL_LINK])

    # SA long date
    dt = row["_event_dt"]
    date_text = sa_long_date(dt, safe_str(row[COL_DATE]))

    # Afrikaans title/second-line rule
    af_title, second_line, is_af = classify_afrikaans(raw_subject)

    # Title rule (no duplication)
    if is_af:
        title = af_title
        subtitle = second_line  # required: second line must be activity
    else:
        # normal: title uses team if present, else subject; subtitle is subject if title came from team
        title = team if team else raw_subject
        subtitle = raw_subject if team else ""

    btn_text = button_text_for_row(raw_subject)

    st.markdown('<div class="cardbox">', unsafe_allow_html=True)

    st.markdown(f'<div class="title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="subtitle">{subtitle}</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="meta">
        📅 {date_text}<br>
        📍 {venue}
    </div>
    """, unsafe_allow_html=True)

    if info:
        st.info(info)

    if link.startswith("http"):
        st.link_button(btn_text, link)

    st.markdown('</div>', unsafe_allow_html=True)
