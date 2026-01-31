import re
import streamlit as st
import pandas as pd

# =============================
# PAGE CONFIG
# =============================
st.set_page_config(page_title="LMCP Event Hub", layout="wide")

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

# =============================
# STYLING (Modern)
# =============================
st.markdown("""
<style>
    .stApp { background: #f6f7fb; }
    .topbar {
        background: linear-gradient(90deg, #800000, #a00000);
        color: white;
        padding: 18px 22px;
        border-radius: 18px;
        margin-bottom: 14px;
        box-shadow: 0 10px 18px rgba(0,0,0,0.10);
    }
    .topbar h1 { margin: 0; font-size: 22px; letter-spacing: 0.4px; }
    .topbar p { margin: 2px 0 0; opacity: 0.95; }

    .panel {
        background: white;
        border-radius: 18px;
        padding: 14px 16px;
        box-shadow: 0 6px 16px rgba(0,0,0,0.08);
        margin-bottom: 12px;
        border: 1px solid rgba(0,0,0,0.04);
    }
    .label {
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 0.2px;
        color: #2c2c2c;
        margin-bottom: 6px;
        display: block;
    }
    .cardbox {
        background: white;
        border-radius: 20px;
        padding: 14px 14px;
        border: 1px solid rgba(0,0,0,0.06);
        box-shadow: 0 10px 18px rgba(0,0,0,0.08);
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="topbar">
  <h1>MIDSTREAM COLLEGE</h1>
  <p>Primary Event Hub</p>
</div>
""", unsafe_allow_html=True)

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
    c = safe_str(cat).strip().lower()

    # strict matching
    if re.search(r"\bsport(s)?\b", c):
        return "Sport"
    if re.search(r"\bcultur(e|al)?\b", c):
        return "Culture"
    if re.search(r"\bacadem(ic|ics)?\b", c):
        return "Academics"

    return "Unknown"

def normalize_afrikaans_subject(text: str) -> str:
    t = safe_str(text)
    low = t.lower()

    # Only do replacements when the subject includes "afrikaans"
    if "afrikaans" in low:
        # Any EAT variation -> full phrase
        if re.search(r"\beat\b", low):
            # Replace standalone EAT token or Afrikaans ... EAT variations
            t = re.sub(r"\bEAT\b", "Eerste Addisionele Taal", t, flags=re.I)
            # If it says "Afrikaans Eerste Addisionele Taal" without spacing, ensure good format:
            t = re.sub(r"Afrikaans\s*Eerste\s*Addisionele\s*Taal", "Afrikaans Eerste Addisionele Taal", t, flags=re.I)

        # Any HT variation -> full phrase (spelling as requested)
        if re.search(r"\bht\b", low):
            t = re.sub(r"\bHT\b", "Hooftaal", t, flags=re.I)
            t = re.sub(r"Afrikaans\s*Hooftaal", "Afrikaans Hooftaal", t, flags=re.I)

    return t

def is_afrikaans_activity(text: str) -> bool:
    t = safe_str(text)
    if "Afrikaans" not in t:
        return False
    return (
        "Eerste Addisionele Taal" in t
        or "Hooftaal" in t
        or re.search(r"\b(EAT|HT)\b", t, flags=re.I) is not None
    )

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

# Safer expiry: only expire if duration > 0 AND date is valid
def is_expired(row, today):
    dt = row["_event_dt"]
    dur = row["_dur_days"]
    if pd.isna(dt) or dur is None or dur <= 0:
        return False
    expiry_date = dt.normalize() + pd.Timedelta(days=dur)
    return today > expiry_date

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

df["_type"] = df[COL_CAT].apply(normalize_category)
df["_subject"] = df[COL_SUBJ].apply(normalize_afrikaans_subject)

df["_event_dt"] = pd.to_datetime(df[COL_DATE], errors="coerce", dayfirst=True)
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
st.markdown('<div class="panel">', unsafe_allow_html=True)

# 1) Category (explicit key fixes the “Sport still shows academics” issue)
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

# 2) Activity (filtered by chosen categories)
st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)
st.markdown('<span class="label">Activity</span>', unsafe_allow_html=True)
df_cat = df[df["_type"].isin(st.session_state.sel_categories)].copy()
activity_options = sorted([a for a in df_cat["_subject"].unique() if str(a).strip()])
sel_acts = st.multiselect(
    "Activity",
    options=activity_options,
    default=[],
    key="activity_select",
    label_visibility="collapsed",
    placeholder="All activities",
)
st.caption("Tip: Clear Activity to show all.")

# 3) Age Group
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

st.markdown('</div>', unsafe_allow_html=True)

# =============================
# APPLY FILTERS
# =============================
filtered = df[df["_type"].isin(st.session_state.sel_categories)].copy()

# Activity filter
if sel_acts:
    filtered = filtered[filtered["_subject"].isin(sel_acts)]

# Under filter for sport/culture only (keep blanks so you don't lose rows)
u = st.session_state.sel_under
if u and want_under:
    mask_sc = filtered["_type"].isin(["Sport", "Culture"])
    filtered = filtered[~mask_sc | (filtered["_under"].eq(u) | filtered["_under"].eq(""))].copy()

# Grade filter for academics (grade selected OR inferred from under; keep blanks)
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
# RENDER
# =============================
for _, row in filtered.iterrows():
    category = safe_str(row["_type"])
    subject  = safe_str(row["_subject"])
    team     = safe_str(row[COL_TEAM])
    date_s   = safe_str(row[COL_DATE])
    venue    = safe_str(row[COL_VEN])
    info     = safe_str(row[COL_INFO])
    link     = safe_str(row[COL_LINK])

    title = team if team else subject
    btn_text = "Dokument" if is_afrikaans_activity(subject) else "Document"

    st.markdown('<div class="cardbox">', unsafe_allow_html=True)

    st.markdown(f"### {title}")
    st.markdown(f"**{subject}**")
    st.write(f"📅 {date_s}")
    st.write(f"📍 {venue}")

    if info:
        st.info(info)

    if link.startswith("http"):
        st.link_button(btn_text, link)

    st.markdown('</div>', unsafe_allow_html=True)
