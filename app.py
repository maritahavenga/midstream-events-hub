# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import requests, io, re, pytz
from datetime import datetime, timedelta
from requests.exceptions import RequestException, Timeout
import streamlit.components.v1 as components

# =============================
# PAGE CONFIG
# =============================
st.set_page_config(page_title="LMCP Hub", page_icon="📌", layout="wide")

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"
LOGO_URL = "https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg"

TZ = pytz.timezone("Africa/Johannesburg")
now_dt = datetime.now(TZ)
today = now_dt.date()

# =============================
# PERSIST FILTERS (localStorage restore)
# - If URL has params: save them
# - If URL has none: restore last saved params
# =============================
PERSIST_KEY = "lmcp_hub_last_qs"
components.html(
    f"""
    <script>
    (function() {{
      const KEY = "{PERSIST_KEY}";
      const qs = window.location.search ? window.location.search.substring(1) : "";
      if (qs && qs.length > 0) {{
        localStorage.setItem(KEY, qs);
      }} else {{
        const saved = localStorage.getItem(KEY);
        if (saved && saved.length > 0) {{
          const newUrl = window.location.pathname + "?" + saved + window.location.hash;
          window.location.replace(newUrl);
        }}
      }}
    }})();
    </script>
    """,
    height=0,
)

# =============================
# MAPPING RULES (Gr 4 = U10)
# =============================
GRADE_TO_U = {
    "Gr 1": "U7", "Gr 2": "U8", "Gr 3": "U9", "Gr 4": "U10",
    "Gr 5": "U11", "Gr 6": "U12", "Gr 7": "U13"
}

# =============================
# QUERY PARAM HELPERS
# =============================
def _qp_get_list(key: str):
    v = st.query_params.get(key)
    if v is None:
        return []
    if isinstance(v, list):
        out = []
        for item in v:
            out += [x.strip() for x in str(item).split(",") if x.strip()]
        return out
    return [x.strip() for x in str(v).split(",") if x.strip()]

def _qp_set_all():
    """Sync current session state to the URL."""
    st.query_params["view"] = st.session_state.get("view_mode_radio", "Upcoming")
    st.query_params["cat"]  = ",".join(st.session_state.get("cat_ms", []))
    st.query_params["u"]    = ",".join(st.session_state.get("u_ms", []))
    st.query_params["gr"]   = ",".join(st.session_state.get("gr_ms", []))
    st.query_params["q"]    = st.session_state.get("search_q", "")

# =============================
# CALLBACKS (GEHEUE + MAPPING)
# =============================
def on_filter_change():
    # 1) As Sport-only, maak grades skoon sodat "hidden grades" nie nog filter nie.
    selected_cat = st.session_state.get("cat_ms", [])
    is_sport_only_now = (len(selected_cat) == 1 and selected_cat[0] == "Sport")
    if is_sport_only_now:
        st.session_state["gr_ms"] = []

    # 2) Grade -> U mapping (as jy grades kies, voeg relevante U's by)
    selected_grades = st.session_state.get("gr_ms", [])
    current_u = list(st.session_state.get("u_ms", []))

    changed = False
    for g in selected_grades:
        u_val = GRADE_TO_U.get(g)
        if u_val and u_val not in current_u:
            current_u.append(u_val)
            changed = True

    if changed:
        st.session_state["u_ms"] = current_u

    # 3) Skryf alles terug na URL
    _qp_set_all()

# =============================
# STYLE (CSS)
# =============================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap');
html, body, [class*="css"] {font-family: 'Inter', sans-serif;}
:root{ --maroon:#800000; --teal:#008080; --line:#e8edf5; --shadow:0 10px 30px rgba(0,0,0,.06); }
.topBanner{ margin-top:14px; border-radius:22px; padding:18px; margin-bottom:22px; background:#008080; color:#fff; text-align:center;}
.longLogo{ width:min(900px, 100%); border-radius:16px; background:#fff; padding:10px; margin:0 auto; border:2px solid rgba(255,255,255,0.35); }
.longLogo img{width:100%; display:block;}
.card{ border:1px solid var(--line); background:#fff; box-shadow:var(--shadow); border-radius:18px; padding:14px; margin-bottom:14px; border-left:10px solid var(--maroon); position:relative; }
.card-title{font-weight:900; color:var(--maroon); font-size:1.15rem;}
.noteBlock{ margin-top:12px; padding:12px; border-radius:14px; background:rgba(0,128,128,0.08); border:1px solid rgba(0,128,128,0.25); font-size:.95rem; }
.btnRow{display:flex; gap:10px; flex-wrap:wrap; margin-top:12px;}
.btn{ display:inline-block; background:var(--teal); color:white !important; padding:9px 12px; border-radius:12px; font-weight:900; text-decoration:none; font-size:.90rem; }
.meta{color:#64748b; font-size:.95rem; margin-top:4px;}
.ribbon{ position:absolute; bottom:12px; right:12px; background:#FFD400; color:#B00000; font-weight:1000; font-size:.75rem; padding:6px 10px; border-radius:999px; display:flex; align-items:center; gap:8px; }
.rDot{width:8px; height:8px; border-radius:999px; background:#B00000; animation:pulse 1s infinite;}
@keyframes pulse{0%{transform:scale(1);opacity:.4;}50%{transform:scale(1.7);opacity:1;}100%{transform:scale(1);opacity:.4;}}
</style>
""", unsafe_allow_html=True)

st.markdown(
    f'<div class="topBanner"><div class="longLogo"><img src="{LOGO_URL}"></div>'
    f'<div style="font-weight:900; font-size:1.65rem; margin-top:10px;">Digital Hub</div></div>',
    unsafe_allow_html=True
)

# =============================
# DATA HELPERS
# =============================
def safe_txt(x):
    return str(x or "").strip()

def normalize_category(v):
    s = str(v).strip().lower()
    if "sport" in s:
        return "sport"
    if "culture" in s or "kultuur" in s:
        return "culture"
    if "academic" in s or "akadem" in s:
        return "academics"
    return s

def parse_date_sa(s):
    try:
        cleaned = str(s).strip()
        if not cleaned:
            return None
        cleaned = cleaned.replace(".", "/").replace("-", "/")
        return pd.to_datetime(cleaned, dayfirst=True, errors="coerce").to_pydatetime()
    except:
        return None

@st.cache_data(ttl=180, show_spinner=False)
def load_csv(url: str) -> pd.DataFrame:
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        df_ = pd.read_csv(io.StringIO(r.text), dtype=str).fillna("")
        return df_
    except (Timeout, RequestException):
        return pd.DataFrame()

df = load_csv(CSV_URL)
if df.empty:
    st.error("Kon nie data laai nie. Verfris asb. (Data bron is moontlik tydelik af.)")
    st.stop()

# =============================
# INITIALIZE SESSION STATE FROM URL
# =============================
if "cat_ms" not in st.session_state:
    st.session_state.cat_ms = _qp_get_list("cat")

if "u_ms" not in st.session_state:
    st.session_state.u_ms = _qp_get_list("u")

if "gr_ms" not in st.session_state:
    st.session_state.gr_ms = _qp_get_list("gr")

if "search_q" not in st.session_state:
    st.session_state.search_q = st.query_params.get("q", "")

if "view_mode_radio" not in st.session_state:
    st.session_state.view_mode_radio = st.query_params.get("view", "Upcoming")

# =============================
# SIDEBAR FILTERS
# =============================
st.sidebar.markdown("## Filters")

category_choice = st.sidebar.multiselect(
    "Category",
    ["Sport", "Culture", "Academics"],
    key="cat_ms",
    on_change=on_filter_change
)

search = st.sidebar.text_input(
    "Search",
    key="search_q",
    on_change=on_filter_change
)

# Sport-only logic
is_sport_only = (len(st.session_state.get("cat_ms", [])) == 1 and st.session_state.get("cat_ms", [])[0] == "Sport")

selected_u = st.sidebar.multiselect(
    "Age Groups (Sport)",
    [f"U{i}" for i in range(7, 14)],
    key="u_ms",
    on_change=on_filter_change
)

# Show Grades only when NOT sport-only
if not is_sport_only:
    selected_gr = st.sidebar.multiselect(
        "Grades (Culture / Academics)",
        [f"Gr {i}" for i in range(1, 8)],
        key="gr_ms",
        on_change=on_filter_change
    )
else:
    selected_gr = st.session_state.get("gr_ms", [])

# Reset (also clears localStorage so base URL starts fresh)
if st.sidebar.button("🧹 Reset All"):
    for k in ["cat_ms", "u_ms", "gr_ms"]:
        st.session_state[k] = []
    st.session_state["search_q"] = ""
    st.session_state["view_mode_radio"] = "Upcoming"

    st.query_params.clear()

    components.html(
        f"""
        <script>
          localStorage.removeItem("{PERSIST_KEY}");
        </script>
        """,
        height=0
    )
    st.rerun()

# =============================
# VIEW MODE
# =============================
view_mode = st.radio(
    "View",
    ["Upcoming", "Next 7 Days", "Term Documents"],
    horizontal=True,
    key="view_mode_radio",
    on_change=on_filter_change
)

# =============================
# FILTER LOGIC & DISPLAY
# =============================
# Precompute normalized selected categories
selected_cats_norm = [normalize_category(c) for c in st.session_state.get("cat_ms", [])]
search_q = str(st.session_state.get("search_q", "")).strip().lower()

selected_u = st.session_state.get("u_ms", [])
selected_gr = st.session_state.get("gr_ms", [])

# date window for next 7 days
end_7 = today + timedelta(days=7)

res = []
for _, row in df.iterrows():
    cat_norm = normalize_category(row.get("Category", ""))

    # Category filter
    if selected_cats_norm and cat_norm not in selected_cats_norm:
        continue

    # Search filter (search across a few useful columns)
    if search_q:
        hay = " ".join([
            str(row.get("Activity/Subject Name", "")),
            str(row.get("Team / Assessment", "")),
            str(row.get("Venue", "")),
            str(row.get("Information", "")),
            str(row.get("Age Group (9,10) / Grade (1,2,3)", "")),
            str(row.get("Category", "")),
        ]).lower()
        if search_q not in hay:
            continue

    # Grade/Age filter
    row_grade = str(row.get("Age Group (9,10) / Grade (1,2,3)", ""))
    row_grade_u = row_grade.upper()

    match_found = False
    if not selected_u and not selected_gr:
        match_found = True
    if any(u.upper() in row_grade_u for u in selected_u):
        match_found = True
    if any(g.upper() in row_grade_u for g in selected_gr):
        match_found = True

    if not match_found:
        continue

    # Date parsing
    d_dt = parse_date_sa(row.get("Date / Due Date", ""))

    # View mode behavior
    if view_mode == "Upcoming":
        # if a date exists, must be >= today; if no date, keep (docs)
        if d_dt and d_dt.date() < today:
            continue

    elif view_mode == "Next 7 Days":
        # must have a date in next 7 days
        if not d_dt:
            continue
        if not (today <= d_dt.date() <= end_7):
            continue

    elif view_mode == "Term Documents":
        # show items that are "docs" (no date) OR anything that mentions "term"
        info_txt = (str(row.get("Information", "")) + " " + str(row.get("Activity/Subject Name", ""))).lower()
        if d_dt:
            # hide dated events in term-doc view unless it clearly says term document
            if "term" not in info_txt and "dokument" not in info_txt:
                continue

    res.append(row)

# =============================
# RENDER
# =============================
st.markdown("## 📅 Events")

if not res:
    st.info("Geen items gevind nie. Verander jou filters in die sidebar.")
else:
    for r in res:
        title = r.get("Activity/Subject Name", "")
        team = r.get("Team / Assessment", "")
        date_str = r.get("Date / Due Date", "")
        venue = r.get("Venue", "")
        info = r.get("Information", "")

        # Badge logic: $ in Information = NEW UPDATE
        badge = ""
        if "$" in str(info):
            badge = '<div class="ribbon"><span class="rDot"></span>NEW UPDATE</div>'

        st.markdown(f"""
        <div class="card">
            {badge}
            <div class="card-title">{safe_txt(title)} - {safe_txt(team)}</div>
            <div class="meta">📅 {safe_txt(date_str)}</div>
            <div class="meta">📍 {safe_txt(venue).upper()}</div>
            {f'<div class="noteBlock">{safe_txt(info).replace("$","")}</div>' if info else ""}
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br><center style='color:grey;'>LMCP Digital Hub 2026</center>", unsafe_allow_html=True)
