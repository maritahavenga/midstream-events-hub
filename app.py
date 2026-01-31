import re
import streamlit as st
import pandas as pd

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="LMCP Event Hub", layout="wide")

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

# =============================
# STYLING (modern, less “robot”)
# =============================
st.markdown("""
<style>
    .stApp { background: #f6f7fb; }
    .topbar {
        background: linear-gradient(90deg, #800000, #a00000);
        color: white;
        padding: 18px 22px;
        border-radius: 16px;
        margin-bottom: 14px;
        box-shadow: 0 10px 18px rgba(0,0,0,0.10);
    }
    .topbar h1 { margin: 0; font-size: 22px; letter-spacing: 0.5px; }
    .topbar p { margin: 2px 0 0; opacity: 0.95; }

    .panel {
        background: white;
        border-radius: 16px;
        padding: 14px 16px;
        box-shadow: 0 6px 16px rgba(0,0,0,0.08);
        margin-bottom: 12px;
        border: 1px solid rgba(0,0,0,0.04);
    }
    .pill {
        display: inline-block;
        padding: 6px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 600;
        background: rgba(128,0,0,0.08);
        color: #800000;
        margin-right: 8px;
    }
    .card {
        background: white;
        border-radius: 18px;
        padding: 16px 16px 14px;
        border: 1px solid rgba(0,0,0,0.05);
        box-shadow: 0 10px 18px rgba(0,0,0,0.08);
        margin-bottom: 12px;
    }
    .title { font-size: 18px; font-weight: 800; margin: 0; }
    .sub { font-size: 13px; color: #177; font-weight: 700; margin-top: 6px; }
    .meta { color: #555; font-size: 14px; margin-top: 8px; line-height: 1.4; }
    .info {
        background: #f1f3f6;
        padding: 10px 12px;
        border-radius: 12px;
        margin-top: 10px;
        border-left: 4px solid #177;
        font-size: 14px;
    }
    .smallnote { font-size: 12px; color: #777; margin-top: 8px; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="topbar">
  <h1>MIDSTREAM COLLEGE</h1>
  <p>Primary Event Hub</p>
</div>
""", unsafe_allow_html=True)

# =============================
# HELPERS
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

def safe_str(x) -> str:
    return "" if pd.isna(x) else str(x).strip()

def normalize_category(cat: str) -> str:
    c = safe_str(cat).lower()
    if "sport" in c:
        return "Sport"
    if "cultur" in c or "culture" in c:
        return "Culture"
    if "academ" in c:
        return "Academics"
    # fallback: guess academics if not explicitly sport/culture
    return "Academics"

def normalize_afrikaans_subject(text: str) -> str:
    t = safe_str(text)

    # Afrikaans EAT -> Afrikaans Eerste Addisionele Taal
    if re.search(r"\bafrikaans\b", t, flags=re.I) and re.search(r"\beat\b", t, flags=re.I):
        # keep other text but ensure the Afrikaans part is correct
        t = re.sub(r"Afrikaans\s*EAT", "Afrikaans Eerste Addisionele Taal", t, flags=re.I)

    # Afrikaans HT -> Afrikaans Hooftaal (as per your required spelling)
    if re.search(r"\bafrikaans\b", t, flags=re.I) and re.search(r"\bht\b", t, flags=re.I):
        t = re.sub(r"Afrikaans\s*HT", "Afrikaans Hooftaal", t, flags=re.I)

    return t

def is_afrikaans_activity(text: str) -> bool:
    t = safe_str(text)
    return ("Afrikaans" in t) and (re.search(r"\b(EAT|HT)\b", t, flags=re.I) is not None)

def parse_under(value: str) -> str:
    """Convert age cell into Uxx when possible."""
    v = safe_str(value)
    if not v:
        return ""
    m = re.search(r"\bU\s*(\d{1,2})\b", v, flags=re.I)
    if m:
        return f"U{int(m.group(1))}"
    # if numeric age (7..13)
    m2 = re.search(r"\b(\d{1,2})\b", v)
    if m2:
        age = int(m2.group(1))
        if 7 <= age <= 13:
            return f"U{age}"
    return ""

def parse_grade(value: str) -> str:
    """Convert age/grade cell into Gr X when possible."""
    v = safe_str(value)
    if not v:
        return ""
    m = re.search(r"\bGr\s*(\d)\b", v, flags=re.I)
    if m:
        return f"Gr {int(m.group(1))}"
    # sometimes only number given: could be age
    m2 = re.search(r"\b(\d{1,2})\b", v)
    if m2:
        n = int(m2.group(1))
        # if it's an age (7..13), map to grade
        if 7 <= n <= 13:
            return U_TO_GR.get(f"U{n}", "")
        # if it's already grade 1..7
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

def expired(row, today):
    dt = row["_event_dt"]
    dur = row["_dur_days"]
    if pd.isna(dt) or dur is None:
        return False  # show if cannot calculate
    expiry_date = dt.normalize() + pd.Timedelta(days=dur)
    return today > expiry_date

# =============================
# LOAD DATA
# =============================
try:
    df = pd.read_csv(URL)
    df.columns = df.columns.str.strip()
    df = df.fillna("")

    # Expected columns based on your CSV:
    COL_CAT      = "Category"
    COL_SUBJ     = "Activity/Subject Name"
    COL_TEAM     = "Team"
    COL_DATE     = "Date / Due Date"
    COL_VEN      = "Venue"
    COL_INFO     = "Information"
    COL_LINK     = "Programme / Document Link"
    COL_DURATION = "Display Duration"
    COL_AGEGRADE = "Age Group (9,10) / Grade (1,2,3)"

    if df.empty:
        st.info("Waiting for data from the sheet…")
        st.stop()

    # Prepare normalized fields
    df["_type"] = df[COL_CAT].apply(normalize_category)
    df["_subject"] = df[COL_SUBJ].apply(normalize_afrikaans_subject)

    # Parse date for sorting
    df["_event_dt"] = pd.to_datetime(df[COL_DATE], errors="coerce", dayfirst=True)

    # Display Duration expiry
    df["_dur_days"] = df[COL_DURATION].apply(safe_int)

    today = pd.Timestamp.now(tz="Africa/Johannesburg").normalize().tz_localize(None)
    df = df[~df.apply(lambda r: expired(r, today), axis=1)].copy()

    # Under + Grade derived from the same column
    df["_under"] = df[COL_AGEGRADE].apply(parse_under)
    df["_grade"] = df[COL_AGEGRADE].apply(parse_grade)

    # Sort by date (nearest first; unknown dates last)
    df["_sort_dt"] = df["_event_dt"].fillna(pd.Timestamp.max)
    df = df.sort_values("_sort_dt", ascending=True)

except Exception as e:
    st.error("Could not load data from Google Sheets.")
    st.code(str(e))
    st.stop()

# =============================
# NAV BARS (stateful, so U10 stays when you add Academics)
# =============================
if "sel_categories" not in st.session_state:
    st.session_state.sel_categories = ["Sport"]  # default, you can change
if "sel_under" not in st.session_state:
    st.session_state.sel_under = ""
if "sel_grade" not in st.session_state:
    st.session_state.sel_grade = ""

with st.container():
    st.markdown('<div class="panel">', unsafe_allow_html=True)

    # 1) Category bar
    colA, colB, colC = st.columns([1.2, 2.2, 1.2])
    with colA:
        st.markdown("<span class='pill'>1</span> Category", unsafe_allow_html=True)
    with colB:
        cats = ["Sport", "Culture", "Academics"]
        st.session_state.sel_categories = st.multiselect(
            " ",
            options=cats,
            default=st.session_state.sel_categories,
            label_visibility="collapsed",
        )
        if not st.session_state.sel_categories:
            st.session_state.sel_categories = ["Sport"]

    # 2) Activity bar: show only activities from selected categories
    with colC:
        st.markdown("<span class='pill'>2</span> Activity", unsafe_allow_html=True)

    # Build activity options filtered by selected categories
    df_cat = df[df["_type"].isin(st.session_state.sel_categories)].copy()
    activities = sorted([a for a in df_cat["_subject"].unique() if str(a).strip()])
    sel_acts = st.multiselect(
        " ",
        options=activities,
        default=[],
        label_visibility="collapsed",
        placeholder="All activities",
    )

    # 3) Age Group bar (Under for Sport/Culture, Grade for Academics)
    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1.2, 2.2, 1.2])
    with col1:
        st.markdown("<span class='pill'>3</span> Age Group", unsafe_allow_html=True)

    want_under = any(c in st.session_state.sel_categories for c in ["Sport", "Culture"])
    want_grade = "Academics" in st.session_state.sel_categories

    # Under selector (only if Sport or Culture selected)
    with col2:
        if want_under:
            under_options = [""] + list(U_TO_GR.keys())
            u = st.selectbox(
                " ",
                options=under_options,
                index=under_options.index(st.session_state.sel_under) if st.session_state.sel_under in under_options else 0,
                label_visibility="collapsed",
                help="For Sport & Culture",
            )
            st.session_state.sel_under = u

            # Keep grade synced when you add Academics later
            if u and not st.session_state.sel_grade:
                st.session_state.sel_grade = U_TO_GR.get(u, "")

        else:
            st.session_state.sel_under = ""

    # Grade selector (only if Academics selected)
    with col3:
        if want_grade:
            grade_options = [""] + list(GR_TO_U.keys())
            g = st.selectbox(
                " ",
                options=grade_options,
                index=grade_options.index(st.session_state.sel_grade) if st.session_state.sel_grade in grade_options else 0,
                label_visibility="collapsed",
                help="For Academics",
            )
            st.session_state.sel_grade = g

            # Keep under synced if needed
            if g and not st.session_state.sel_under and want_under:
                st.session_state.sel_under = GR_TO_U.get(g, "")

        else:
            st.session_state.sel_grade = ""

    st.markdown("</div>", unsafe_allow_html=True)

# =============================
# FILTER LOGIC (U stays, and Academics uses matching grade)
# =============================
filtered = df[df["_type"].isin(st.session_state.sel_categories)].copy()

# Activity filter
if sel_acts:
    filtered = filtered[filtered["_subject"].isin(sel_acts)]

# Age filters:
# - If Sport/Culture selected and U chosen: apply U filter to Sport/Culture rows
# - If Academics selected and Grade chosen (or implied from U): apply grade filter to Academics rows
u = st.session_state.sel_under
g = st.session_state.sel_grade

if u and want_under:
    sport_cult_mask = filtered["_type"].isin(["Sport", "Culture"])
    filtered.loc[sport_cult_mask, "_keep_sc"] = filtered.loc[sport_cult_mask, "_under"].eq(u)
    # rows not sport/culture keep for now (academics handled below)
    filtered.loc[~sport_cult_mask, "_keep_sc"] = True
    filtered = filtered[filtered["_keep_sc"]].drop(columns=["_keep_sc"])

# Determine which grade we should use for academics:
# If grade not chosen but U chosen, infer grade from U
grade_for_acad = g
if (not grade_for_acad) and u:
    grade_for_acad = U_TO_GR.get(u, "")

if grade_for_acad and want_grade:
    acad_mask = filtered["_type"].eq("Academics")
    filtered.loc[acad_mask, "_keep_ac"] = filtered.loc[acad_mask, "_grade"].eq(grade_for_acad)
    filtered.loc[~acad_mask, "_keep_ac"] = True
    filtered = filtered[filtered["_keep_ac"]].drop(columns=["_keep_ac"])

# =============================
# RENDER CARDS
# =============================
if filtered.empty:
    st.info("No items match your filters.")
    st.stop()

for _, row in filtered.iterrows():
    category = row["_type"]
    subject  = safe_str(row["_subject"])
    team     = safe_str(row["Team"])
    date_s   = safe_str(row["Date / Due Date"])
    venue    = safe_str(row["Venue"])
    info     = safe_str(row["Information"])
    link     = safe_str(row["Programme / Document Link"])

    # single title only (avoid duplicates)
    title = team if team else subject

    # Button language rule
    btn_text = "Dokument" if is_afrikaans_activity(subject) else "Document"

    # Build small “context line” in English
    # For sport/culture show Under; for academics show Grade
    under = safe_str(row["_under"])
    grade = safe_str(row["_grade"])
    context_bits = []
    if category in ["Sport", "Culture"] and under:
        context_bits.append(under)
    if category == "Academics" and grade:
        context_bits.append(grade)
    context = " • ".join(context_bits)

    st.markdown(f"""
    <div class="card">
        <p class="title">{title}</p>
        <div class="sub">{subject}</div>
        <div class="meta">
            {"<div>" + context + "</div>" if context else ""}
            <div>📅 {date_s}</div>
            <div>📍 {venue}</div>
        </div>
        {f'<div class="info">{info}</div>' if info else ''}
    </div>
    """, unsafe_allow_html=True)

    if link.startswith("http"):
        st.link_button(btn_text, link)
