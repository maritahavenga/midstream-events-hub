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

# ✅ Upcoming sheet you display (published CSV)
UPCOMING_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

# (Optional) If you have a separate published CSV for timestamps/updates, set it here, else leave None
TIMESTAMP_CSV_URL = None

TZ = pytz.timezone("Africa/Johannesburg")

# =============================
# HELPERS
# =============================
URL_RE = re.compile(r'(https?://[^\s\)\]\}>,]+)')

def cl(v):
    """clean cell"""
    s = "" if v is None else str(v)
    s = s.replace(".0", "")
    s = s.replace("nan", "")
    return s.strip()

def extract_urls(text: str):
    if text is None:
        return []
    s = str(text).strip()
    if not s or s.lower() == "nan":
        return []
    urls = URL_RE.findall(s)
    # keep order, remove duplicates
    seen = set()
    out = []
    for u in urls:
        if u not in seen:
            out.append(u)
            seen.add(u)
    return out

def label_links(base_label: str, urls: list[str]):
    labeled = []
    for i, u in enumerate(urls, start=1):
        lbl = base_label if i == 1 else f"{base_label} {i}"
        labeled.append((lbl, u))
    return labeled

def assessment_doc_labels(urls: list[str]):
    """
    HARD RULE:
      Document   = English
      Document 2 = Afrikaans
    """
    labeled = []
    if len(urls) >= 1:
        labeled.append(("Document", urls[0], "English"))
    if len(urls) >= 2:
        labeled.append(("Document 2", urls[1], "Afrikaans"))
    # if more than 2 accidentally:
    for i in range(3, len(urls) + 1):
        labeled.append((f"Document {i}", urls[i-1], ""))
    return labeled

def safe_read_csv(url: str) -> pd.DataFrame:
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        return pd.read_csv(io.StringIO(r.text))
    except (RequestException, Timeout, ValueError):
        return pd.DataFrame()

def parse_date_any(v):
    """
    Tries to parse dd/mm/yyyy or yyyy-mm-dd or mixed.
    Returns pd.Timestamp or NaT.
    """
    s = cl(v)
    if not s:
        return pd.NaT
    # common: "02/02/2026 13:43:09" or "02/02/2026"
    # use dayfirst True because SA data
    try:
        return pd.to_datetime(s, dayfirst=True, errors="coerce")
    except Exception:
        return pd.NaT

def normalize_activity_for_filter(name: str) -> str:
    """
    Filter label only: remove grade part like 'Mathematics Gr 4' -> 'Mathematics'
    """
    s = cl(name)
    if not s:
        return ""
    # remove "Gr ..." tails
    s = re.sub(r"\bGr\s*\d+\b", "", s, flags=re.IGNORECASE).strip()
    s = re.sub(r"\s{2,}", " ", s).strip()
    return s

def is_assessment_schedule_row(row: pd.Series) -> bool:
    a = cl(row.get("Activity/Subject Name", "")).lower()
    c = cl(row.get("Category", "")).lower()
    return (a == "assessment schedule") or (c == "assessment schedule")

def sort_df(df: pd.DataFrame) -> pd.DataFrame:
    # Ensure date_sort exists
    if "date_sort" not in df.columns:
        # try best-guess columns
        for cand in ["Date / Due Date", "Date", "Due Date"]:
            if cand in df.columns:
                df["date_sort"] = df[cand].apply(parse_date_any)
                break
        if "date_sort" not in df.columns:
            df["date_sort"] = pd.NaT

    df["date_sort"] = pd.to_datetime(df["date_sort"], errors="coerce")
    # Sort by date then alphabetical
    sort_cols = []
    if "date_sort" in df.columns: sort_cols.append("date_sort")
    if "Activity/Subject Name" in df.columns: sort_cols.append("Activity/Subject Name")
    if "Team / Assessment" in df.columns: sort_cols.append("Team / Assessment")
    if "Venue" in df.columns: sort_cols.append("Venue")
    return df.sort_values(sort_cols, ascending=True, na_position="last").reset_index(drop=True)

def grade_key(g):
    """
    For sorting grades like 'Gr 4A2' or 'Grade 4' -> numeric then alpha.
    """
    s = cl(g)
    m = re.search(r"(\d+)", s)
    num = int(m.group(1)) if m else 999
    return (num, s.lower())

# =============================
# SESSION STATE DEFAULTS
# =============================
DEFAULT_FILTERS = {
    "view_mode": "Upcoming",  # Upcoming | Filters
    "cat": [],
    "act": [],
    "ag": [],
    "gr": [],
    "search": "",
}

for k, v in DEFAULT_FILTERS.items():
    if k not in st.session_state:
        st.session_state[k] = v

if "saved_filters" not in st.session_state:
    st.session_state.saved_filters = DEFAULT_FILTERS.copy()

# =============================
# LOAD DATA
# =============================
df = safe_read_csv(UPCOMING_CSV_URL)

# Normalize expected columns if your sheet varies
# (Your sheet headings in the past: Timestamp, Email address, Category, Activity/Subject Name,
# Team / Assessment, Date / Due Date, Venue, Programme / Document Link, Team, Confirm, Information,
# Age Group (9,10) / Grade (1,2,3), Display Duration)
for col in df.columns:
    # remove weird BOMs/spaces
    df.rename(columns={col: col.strip()}, inplace=True)

# Create helper columns
if not df.empty:
    # Activity label for filter only
    if "Activity/Subject Name" in df.columns:
        df["activity_filter_label"] = df["Activity/Subject Name"].apply(normalize_activity_for_filter)
    else:
        df["activity_filter_label"] = ""

    # Date sort
    if "Date / Due Date" in df.columns:
        df["date_sort"] = df["Date / Due Date"].apply(parse_date_any)
    elif "Date" in df.columns:
        df["date_sort"] = df["Date"].apply(parse_date_any)
    else:
        df["date_sort"] = pd.NaT

    # Age/Grade column (keep as is)
    if "Age Group (9,10) / Grade (1,2,3)" in df.columns:
        df["age_grade"] = df["Age Group (9,10) / Grade (1,2,3)"].apply(cl)
    elif "Age/Grade" in df.columns:
        df["age_grade"] = df["Age/Grade"].apply(cl)
    else:
        df["age_grade"] = ""

    # Sort globally (TERM DATES NOT PINNED)
    df = sort_df(df)

# =============================
# FILTER OPTION LISTS
# =============================
def unique_sorted(series):
    vals = [cl(x) for x in series.dropna().unique()] if series is not None else []
    vals = [v for v in vals if v]
    return sorted(list(dict.fromkeys(vals)), key=lambda x: x.lower())

CAT_OPTIONS = unique_sorted(df["Category"]) if (not df.empty and "Category" in df.columns) else []
ACT_OPTIONS = unique_sorted(df["activity_filter_label"]) if (not df.empty and "activity_filter_label" in df.columns) else []
AG_OPTIONS = unique_sorted(df["age_grade"]) if (not df.empty and "age_grade" in df.columns) else []

# Build Grade options separately if you store grade/class somewhere (optional)
GRADE_COL = None
for cand in ["Grade", "Class", "Gr", "Grade/Class", "Grade / Class"]:
    if cand in df.columns:
        GRADE_COL = cand
        break
GR_OPTIONS = unique_sorted(df[GRADE_COL]) if (GRADE_COL and not df.empty) else []

# =============================
# SAVE / APPLY FILTERS
# =============================
def save_current_filters():
    st.session_state.saved_filters = {
        "view_mode": "Upcoming",
        "cat": list(st.session_state.cat),
        "act": list(st.session_state.act),
        "ag": list(st.session_state.ag),
        "gr": list(st.session_state.gr),
        "search": st.session_state.search,
    }

def apply_saved_filters():
    sf = st.session_state.get("saved_filters", DEFAULT_FILTERS)
    st.session_state.cat = list(sf.get("cat", []))
    st.session_state.act = list(sf.get("act", []))
    st.session_state.ag = list(sf.get("ag", []))
    st.session_state.gr = list(sf.get("gr", []))
    st.session_state.search = sf.get("search", "")

def clear_filters():
    st.session_state.cat = []
    st.session_state.act = []
    st.session_state.ag = []
    st.session_state.gr = []
    st.session_state.search = ""

def go_to_filters():
    st.session_state.view_mode = "Filters"

def go_to_events():
    st.session_state.view_mode = "Upcoming"

# =============================
# TOP NAV
# =============================
left, mid, right = st.columns([1, 2, 1])
with left:
    if st.button("⬅ Filters", use_container_width=True):
        go_to_filters()
with mid:
    st.markdown("<h2 style='text-align:center; margin:0;'>LMCP Hub</h2>", unsafe_allow_html=True)
with right:
    if st.button("📅 Events", use_container_width=True):
        go_to_events()

st.markdown("---")

# =============================
# FILTER SCREEN
# =============================
def render_filters_screen():
    st.subheader("Filters")

    # ✅ Add Save Filter + Go to Events at TOP
    topA, topB, topC = st.columns([1, 1, 1])
    with topA:
        if st.button("💾 Save filters & go to Events (Top)", use_container_width=True):
            save_current_filters()
            go_to_events()
            st.rerun()
    with topB:
        if st.button("✅ Apply saved filters", use_container_width=True):
            apply_saved_filters()
            st.rerun()
    with topC:
        if st.button("🧹 Clear filters", use_container_width=True):
            clear_filters()
            st.rerun()

    st.markdown("")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.session_state.cat = st.multiselect("Category", CAT_OPTIONS, default=st.session_state.cat)
    with c2:
        st.session_state.act = st.multiselect("Activity / Subject", ACT_OPTIONS, default=st.session_state.act)
    with c3:
        st.session_state.ag = st.multiselect("Age group / Grade", AG_OPTIONS, default=st.session_state.ag)
    with c4:
        if GR_OPTIONS:
            st.session_state.gr = st.multiselect("Class / Grade", GR_OPTIONS, default=st.session_state.gr)
        else:
            st.session_state.gr = st.session_state.gr  # keep

    st.session_state.search = st.text_input("Search (title / venue / info)", value=st.session_state.search)

    st.markdown("---")

    # ✅ Add Save Filter + Go to Events at BOTTOM
    botA, botB, botC = st.columns([1, 1, 1])
    with botA:
        if st.button("💾 Save filters & go to Events (Bottom)", use_container_width=True):
            save_current_filters()
            go_to_events()
            st.rerun()
    with botB:
        if st.button("✅ Apply saved filters (Bottom)", use_container_width=True):
            apply_saved_filters()
            st.rerun()
    with botC:
        if st.button("🧹 Clear filters (Bottom)", use_container_width=True):
            clear_filters()
            st.rerun()

# =============================
# UPCOMING / EVENTS SCREEN
# =============================
def apply_filters(df_in: pd.DataFrame) -> pd.DataFrame:
    if df_in.empty:
        return df_in

    d = df_in.copy()

    # Category
    if st.session_state.cat:
        d = d[d["Category"].astype(str).isin(st.session_state.cat)] if "Category" in d.columns else d

    # Activity label filter (Mathematics grade text removed in label)
    if st.session_state.act:
        d = d[d["activity_filter_label"].astype(str).isin(st.session_state.act)] if "activity_filter_label" in d.columns else d

    # Age/Grade field
    if st.session_state.ag:
        d = d[d["age_grade"].astype(str).isin(st.session_state.ag)] if "age_grade" in d.columns else d

    # Optional class/grade column
    if st.session_state.gr and GRADE_COL and GRADE_COL in d.columns:
        d = d[d[GRADE_COL].astype(str).isin(st.session_state.gr)]

    # Search
    q = cl(st.session_state.search).lower()
    if q:
        hay_cols = [c for c in ["Activity/Subject Name", "Venue", "Information", "Programme / Document Link", "Team / Assessment"] if c in d.columns]
        if hay_cols:
            mask = False
            for c in hay_cols:
                mask = mask | d[c].astype(str).str.lower().str.contains(q, na=False)
            d = d[mask]

    # Final sort: date then alphabetical
    d = sort_df(d)
    return d

def render_event_card(row: pd.Series):
    title = cl(row.get("Activity/Subject Name", ""))
    cat = cl(row.get("Category", ""))
    venue = cl(row.get("Venue", ""))
    team_assess = cl(row.get("Team / Assessment", ""))
    age_grade = cl(row.get("age_grade", ""))

    dt = row.get("date_sort", pd.NaT)
    date_str = ""
    if pd.notna(dt):
        try:
            date_str = dt.strftime("%d %b %Y %H:%M").replace(" 00:00", "")
        except Exception:
            date_str = str(dt)

    st.markdown(
        f"""
        <div style="border:1px solid #e6e6e6; border-radius:14px; padding:14px; margin-bottom:12px;">
          <div style="font-size:18px; font-weight:700;">{title}</div>
          <div style="margin-top:4px; opacity:0.85;">
            <b>{cat}</b>{" • " + date_str if date_str else ""}{" • " + venue if venue else ""}
          </div>
          <div style="margin-top:6px; opacity:0.85;">
            {team_assess if team_assess else ""}<br/>
            {age_grade if age_grade else ""}
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # LINKS RULES
    # - Programme / Document Link can contain 2 links -> Programme, Programme 2
    # - Information can contain 2 links -> Information, Information 2
    # - If Assessment Schedule -> Document (English), Document 2 (Afrikaans) from Programme / Document Link
    prog_field = row.get("Programme / Document Link", "")
    info_field = row.get("Information", "")

    if is_assessment_schedule_row(row):
        doc_urls = extract_urls(prog_field)
        docs = assessment_doc_labels(doc_urls)
        for doc_label, url, lang in docs:
            if lang:
                st.markdown(f"- [{doc_label}]({url}) <span style='opacity:0.75'>({lang})</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"- [{doc_label}]({url})")
    else:
        programme_urls = extract_urls(prog_field)
        programme_links = label_links("Programme", programme_urls)
        for lbl, url in programme_links:
            st.markdown(f"- [{lbl}]({url})")

    # Always label Information links as Information / Information 2 (rule)
    info_urls = extract_urls(info_field)
    info_links = label_links("Information", info_urls)
    for lbl, url in info_links:
        st.markdown(f"- [{lbl}]({url})")

def render_upcoming_screen():
    # top quick actions
    a, b, c = st.columns([1, 1, 1])
    with a:
        if st.button("⚙️ Filters", use_container_width=True):
            go_to_filters()
            st.rerun()
    with b:
        if st.button("💾 Save current filters", use_container_width=True):
            save_current_filters()
            st.success("Saved.")
    with c:
        if st.button("🧹 Clear filters", use_container_width=True):
            clear_filters()
            st.rerun()

    # Apply current filters to df
    d = apply_filters(df)

    # ✅ Term Dates are NOT pinned. They stay inside the normal list and sorting.
    if d.empty:
        st.info("No events match the current filters.")
        return

    # Render cards
    for _, r in d.iterrows():
        render_event_card(r)

# =============================
# ROUTER
# =============================
if st.session_state.view_mode == "Filters":
    render_filters_screen()
else:
    render_upcoming_screen()
