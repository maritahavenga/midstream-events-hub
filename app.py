# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import requests, io, re, pytz
from datetime import datetime, timedelta
from requests.exceptions import RequestException, Timeout

# =============================
# PAGE CONFIG
# =============================
st.set_page_config(page_title="LMCP Hub", page_icon="📌", layout="wide")

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"
LOGO_URL = "https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg"

TZ = pytz.timezone("Africa/Johannesburg")
now_dt = datetime.now(TZ)
today = now_dt.date()

VIEW_OPTIONS = ["Upcoming", "Next 7 Days", "Term Documents", "New Updates"]
NEW_UPDATES_HOURS_DEFAULT = 8
BADGE_ANIMATE_MINUTES = 10

# ============================================================
# QUERY PARAMS HELPERS (kept so URL updates with filters)
# ============================================================

def qp_get(name: str, default=""):
    try:
        v = st.query_params.get(name, default)
    except Exception:
        v = default

    if v is None:
        return default
    if isinstance(v, (list, tuple)):
        return v[0] if v else default
    return v

def qp_get_list(name: str):
    raw = qp_get(name, "")
    if not raw:
        return []
    return [x.strip() for x in raw.split(",") if x.strip()]

def qp_set_from_state(payload: dict):
    clean = {}
    for k, v in payload.items():
        if isinstance(v, list):
            if v:
                clean[k] = ",".join(v)
        else:
            if str(v).strip():
                clean[k] = str(v).strip()
    st.query_params.from_dict(clean)

# =============================
# SESSION DEFAULTS
# =============================
def ss_init(key, default):
    if key not in st.session_state:
        st.session_state[key] = default

ss_init("view_mode", "Upcoming")
ss_init("cat_choice", [])
ss_init("act_choice", [])
ss_init("u_choice", [])
ss_init("gr_choice", [])
ss_init("search_text", "")

# =============================
# INITIAL LOAD FROM QUERY PARAMS (ONCE)
# =============================
if "qp_loaded" not in st.session_state:
    st.session_state.qp_loaded = True

    view = qp_get("view", "")
    if view in VIEW_OPTIONS:
        st.session_state.view_mode = view

    cats = qp_get_list("cat")
    cat_norm_map = {"sport": "Sport", "culture": "Culture", "academics": "Academics", "academic": "Academics"}
    st.session_state.cat_choice = [cat_norm_map.get(c.lower(), c) for c in cats if c]

    st.session_state.act_choice = qp_get_list("act")
    st.session_state.u_choice = qp_get_list("u")
    st.session_state.gr_choice = qp_get_list("gr")
    st.session_state.search_text = qp_get("q", "")

# =============================
# STYLE
# =============================
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap');
html, body, [class*="css"] {font-family: 'Inter', sans-serif;}
:root{
  --maroon:#800000; --teal:#008080; --line:#e8edf5; --shadow:0 10px 30px rgba(0,0,0,.06);
}
.block-container{padding-top:1.35rem;}

.topBanner{
  margin-top:14px;
  border-radius:22px;
  padding:18px 18px 16px 18px;
  margin-bottom:14px;
  background:#008080;
  box-shadow:var(--shadow);
  color:#fff;
}
.topBannerInner{display:flex;flex-direction:column;gap:10px;align-items:center;text-align:center;}
.longLogo{
  width:min(900px, 100%);
  border-radius:16px;
  background:#fff;
  padding:10px 12px;
  border:2px solid rgba(255,255,255,0.35);
}
.longLogo img{width:100%;height:auto;display:block;}
.hubText{font-weight:900;font-size:1.65rem;letter-spacing:.3px;}

.card{
  border:1px solid var(--line);
  background:#fff;
  box-shadow:var(--shadow);
  border-radius:18px;
  padding:14px 14px 12px 14px;
  margin-bottom:14px;
  border-left:10px solid var(--maroon);
  position:relative;
}

.card-title{font-weight:900;color:var(--maroon);font-size:1.15rem;line-height:1.2;}
.card-submeta{margin-top:6px;font-size:.92rem;color:#64748b;font-weight:800;}
.meta{color:#64748b;margin-top:8px;font-size:.95rem;}

.noteBlock{
  margin-top:12px;padding:12px;border-radius:14px;
  background:rgba(0,128,128,0.08);
  border:1px solid rgba(0,128,128,0.25);
  color:#0f172a;font-size:.95rem;line-height:1.35;
}

.btnRow{display:flex;gap:10px;flex-wrap:wrap;margin-top:12px;}
.btn{
  display:inline-block;background:var(--teal);color:white !important;
  padding:9px 12px;border-radius:12px;font-weight:900;
  text-decoration:none;font-size:.90rem;
}
.btn:hover{opacity:.92;}

.ribbon{
  position:absolute; right:12px; bottom:12px;
  background:#FFD400;
  color:#B00000;
  font-weight:1000;
  font-size:.78rem;
  padding:6px 10px;
  border-radius:999px;
  border:1px solid rgba(176,0,0,0.25);
  box-shadow:0 8px 16px rgba(0,0,0,0.10);
  display:flex;align-items:center;gap:8px;
  z-index:5;
}
.rDot{width:8px;height:8px;border-radius:999px;background:#B00000;animation:pulse 1.0s infinite;}
@keyframes pulse{0%{transform:scale(1);opacity:.4;}50%{transform:scale(1.7);opacity:1;}100%{transform:scale(1);opacity:.4;}}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    f"""
<div class="topBanner">
  <div class="topBannerInner">
    <div class="longLogo"><img src="{LOGO_URL}"></div>
    <div class="hubText">Digital Hub</div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# =============================
# HELPERS
# =============================
URL_RE = re.compile(r"(https?://[^\s\)\]\}<>\"']+)", re.IGNORECASE)

def safe_txt(x) -> str:
    s = str(x or "")
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").strip()

def is_http(u: str) -> bool:
    s = str(u or "").strip().lower()
    return s.startswith("http://") or s.startswith("https://")

def first_url(v: str) -> str:
    s = str(v or "").replace("\n", " ").strip()
    m = re.search(r"https?://\S+", s)
    return m.group(0) if m else ""

def split_info_text_and_links(info: str):
    raw = str(info or "").strip()
    if not raw:
        return "", []
    links = URL_RE.findall(raw)
    text = URL_RE.sub("", raw)
    text = re.sub(r"\s{2,}", " ", text).strip(" -\n\t|")
    return text, links

def normalize_category(v: str) -> str:
    s = str(v or "").strip().lower()
    if "sport" in s: return "sport"
    if "culture" in s or "kultuur" in s: return "culture"
    if "academic" in s or "academics" in s or "akadem" in s: return "academics"
    return s

def normalize_activity(v: str) -> str:
    s = str(v or "").strip().lower()
    s = re.sub(r"\s+", " ", s)
    if s in ["ht", "afrikaans ht"] or "hooftaal" in s:
        return "Afrikaans Hooftaal"
    if s in ["eat", "afrikaans eat"] or "eerste addisionele" in s:
        return "Afrikaans Eerste Addisionele Taal"
    if "wiskunde" in s: return "Math"
    if "atletiek" in s or "athletics" in s: return "Athletics"
    if "swem" in s or "swimming" in s or "gala" in s: return "Swimming"
    if "tennis" in s: return "Tennis"
    if "rugby" in s: return "Rugby"
    if "hockey" in s: return "Hockey"
    if "netbal" in s or "netball" in s: return "Netball"
    if "koor" in s or "choir" in s: return "Choir"
    if "revue" in s: return "Revue"
    return s.title()

def is_afrikaans_subject(b_raw: str) -> bool:
    s = str(b_raw or "").strip().lower()
    return ("afrikaans" in s) or (s in ["ht", "eat"]) or ("hooftaal" in s) or ("eerste addisionele" in s)

def norm_gender_words(text: str) -> str:
    s = str(text or "").strip().replace("_", " ")
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"\bmeisies\b", "Girls", s, flags=re.I)
    s = re.sub(r"\bseuns\b", "Boys", s, flags=re.I)
    s = re.sub(r"\bgirls\b", "Girls", s, flags=re.I)
    s = re.sub(r"\bboys\b", "Boys", s, flags=re.I)
    s = re.sub(r"(Boys)\s*(Boys)\b", r"\1", s)
    s = re.sub(r"(Girls)\s*(Girls)\b", r"\1", s)
    return re.sub(r"\s+", " ", s).strip()

MONTHS = {
    "jan": "January","january": "January",
    "feb": "February","february": "February",
    "mar": "March","march": "March",
    "apr": "April","april": "April",
    "may": "May",
    "jun": "June","june": "June",
    "jul": "July","july": "July",
    "aug": "August","august": "August",
    "sep": "September","september": "September",
    "oct": "October","october": "October",
    "nov": "November","november": "November",
    "dec": "December","december": "December",
}

def parse_date_sa(s):
    if s is None: return None
    raw = str(s).strip()
    if raw == "" or raw.lower() in ["nan", "none"]: return None

    if re.fullmatch(r"\d+(\.\d+)?", raw):
        try:
            n = float(raw)
            if n > 30000:
                base = datetime(1899, 12, 30)
                return base + timedelta(days=int(n))
        except Exception:
            pass

    m = re.match(r"^\s*(\d{1,2})\s+([A-Za-z]+)\s*$", raw)
    if m:
        d = int(m.group(1))
        mon = m.group(2).lower()
        if mon in MONTHS:
            year = datetime.now(TZ).year
            try:
                return datetime.strptime(f"{d} {MONTHS[mon]} {year}", "%d %B %Y")
            except Exception:
                pass

    cleaned = raw.replace(".", "/").replace("-", "/")
    cleaned = re.sub(r"\s+", " ", cleaned)

    d1 = pd.to_datetime(cleaned, dayfirst=True, errors="coerce")
    if not pd.isnull(d1): return d1.to_pydatetime()

    d2 = pd.to_datetime(cleaned, dayfirst=False, errors="coerce")
    if not pd.isnull(d2): return d2.to_pydatetime()

    return None

def format_date_long_sa(s) -> str:
    dt = parse_date_sa(s)
    if not dt: return str(s or "").strip()
    return f"{dt.day} {dt.strftime('%B %Y')}"

VENUE_MAP = {
    "musiekkamer": "Music Room",
    "musiek kamer": "Music Room",
    "saal": "Hall",
    "ouditorium": "Auditorium",
    "veld": "Field",
    "bondev": "Bondev Field",
    "swembad": "Swimming Pool",
    "tennis bane": "Tennis Courts",
    "netbal bane": "Netball Courts",
    "cricket oval": "Cricket Oval",
}

def normalize_venue(v: str) -> str:
    s = str(v or "").strip().replace("_", " ")
    s = re.sub(r"\s+", " ", s)
    sl = s.lower()
    if "see programme" in sl or "see program" in sl or "sien program" in sl or "sien programme" in sl:
        return "SEE_PROGRAMME"
    for k, vv in VENUE_MAP.items():
        if k in sl:
            return vv
    return s

# =============================
# TIMESTAMP (robust: auto-detect column)
# =============================
def parse_sheet_timestamp(x):
    s = str(x or "").strip()
    if not s:
        return None
    dt = pd.to_datetime(s, dayfirst=True, errors="coerce")
    if pd.isnull(dt):
        return None
    py = dt.to_pydatetime()
    try:
        return TZ.localize(py) if py.tzinfo is None else py.astimezone(TZ)
    except Exception:
        return py

def pick_timestamp_column_smart(df_: pd.DataFrame) -> str:
    if df_.empty or len(df_.columns) == 0:
        return ""

    # Prefer obvious name variants
    for c in df_.columns:
        cl = str(c).strip().lower()
        if "time" in cl and ("stamp" in cl or "stemp" in cl):
            return c

    # Otherwise, parse success-rate test
    N = min(50, len(df_))
    best_col = df_.columns[0]
    best_score = -1.0

    # check first 6 columns only (fast)
    for c in df_.columns[:6]:
        vals = df_[c].astype(str).head(N).tolist()
        ok = 0
        for v in vals:
            if parse_sheet_timestamp(v):
                ok += 1
        score = ok / max(1, len(vals))
        if score > best_score:
            best_score = score
            best_col = c

    return best_col

# =============================
# AGE GROUP / GRADE PARSING
# =============================
def expand_group_range(raw: str, kind: str):
    s = str(raw or "").strip()
    if not s:
        return []
    s = s.replace("–", "-").replace("—", "-")
    s = re.sub(r"\s*(/|&|\+|and|en|to)\s*", ",", s, flags=re.I)

    if kind == "Gr" and re.search(r"\bgr\b", s, flags=re.I):
        nums = [int(n) for n in re.findall(r"\d+", s)]
        return [f"Gr {n}" for n in nums] if nums else []

    if kind == "U" and re.search(r"\bu\b", s, flags=re.I):
        nums = [int(n) for n in re.findall(r"\d+", s)]
        return [f"U{n}" for n in nums] if nums else []

    s_nospace = re.sub(r"\s+", "", s)
    nums = [int(n) for n in re.findall(r"\d+", s_nospace)]
    if not nums:
        return []

    if "-" in s_nospace and len(nums) >= 2:
        lo, hi = sorted([nums[0], nums[1]])
        seq = list(range(lo, hi + 1))
        return [f"U{x}" for x in seq] if kind == "U" else [f"Gr {x}" for x in seq]

    if "," in s_nospace:
        return [f"U{x}" for x in nums] if kind == "U" else [f"Gr {x}" for x in nums]

    if len(nums) == 1:
        return [f"U{nums[0]}"] if kind == "U" else [f"Gr {nums[0]}"]

    return [f"U{x}" for x in nums] if kind == "U" else [f"Gr {x}" for x in nums]

def extract_u_groups_from_text(text: str):
    t = str(text or "").strip()
    if not t:
        return []
    t = t.replace("–", "-").replace("—", "-")

    m = re.search(r"\bU?\d{1,2}\s*-\s*U?\d{1,2}\b", t, flags=re.I)
    if m:
        return expand_group_range(m.group(0), "U")

    m = re.search(r"\bU?\d{1,2}(?:\s*,\s*U?\d{1,2}){1,}\b", t, flags=re.I)
    if m:
        return expand_group_range(m.group(0), "U")

    m = re.search(r"\b\d{1,2}\s*-\s*\d{1,2}\b", t)
    if m:
        return expand_group_range(m.group(0), "U")

    m = re.search(r"\bU(\d{1,2})\b", t, flags=re.I)
    if m:
        return [f"U{int(m.group(1))}"]

    return []

def group_for_row(cat_norm: str, grade_raw: str, team_raw: str):
    if cat_norm == "sport":
        g = str(grade_raw or "").strip()
        m = expand_group_range(g, "U") if g else []
        if not m:
            m = extract_u_groups_from_text(team_raw)
        if len(m) >= 2:
            return f"{m[0]}-{m[-1]}", m
        return (m[0] if m else ""), m

    g = str(grade_raw or "").strip()
    if not g:
        return "", []
    m = expand_group_range(g, "Gr")
    if len(m) >= 2:
        return f"{m[0]}–{m[-1]}", m
    return (m[0] if m else ""), m

def strip_group_tokens(text: str) -> str:
    t = str(text or "")
    t = re.sub(r"\bU?\d{1,2}\s*[-–]\s*U?\d{1,2}\b", "", t, flags=re.I)
    t = re.sub(r"\bU?\d{1,2}(?:\s*,\s*U?\d{1,2}){1,}\b", "", t, flags=re.I)
    t = re.sub(r"\s{2,}", " ", t)
    return t.strip(" -–|,")

def fix_boys_girls_combo(s: str) -> str:
    t = str(s or "").strip().replace("&amp;", "&")
    t = re.sub(r"\s*&\s*", " & ", t)
    if re.search(r"\bBoys\s*&\s*Girls\b", t, flags=re.I):
        t = re.sub(r"\bBoys\s*&\s*Girls\b", "B Girls", t, flags=re.I)
    t = re.sub(r"\bBoys\s+and\s+Girls\b", "B Girls", t, flags=re.I)
    return re.sub(r"\s{2,}", " ", t).strip()

def tidy_team_text(s: str) -> str:
    t = str(s or "").strip()
    if not t:
        return ""
    t = t.replace("&amp;", "&")
    t = re.sub(r"\bU\s+(\d{1,2})\b", r"U\1", t, flags=re.I)
    t = re.sub(r"(U\d{1,2})(Girls|Boys)\b", r"\1 \2", t, flags=re.I)
    t = re.sub(r"([A-Za-z])(?=U\d)", r"\1 ", t)
    t = re.sub(r"\b(U\d{1,2})(Boys|Girls)\b", r"\1 \2", t, flags=re.I)
    t = fix_boys_girls_combo(t)
    t = re.sub(r"\s{2,}", " ", t).strip()
    return t

def build_title(cat_val: str, act_val: str, team_val: str, grade_val: str) -> str:
    cn = normalize_category(cat_val)
    act_txt = norm_gender_words(normalize_activity(act_val))
    team_clean = strip_group_tokens(team_val)
    team_clean = tidy_team_text(norm_gender_words(team_clean))
    return re.sub(r"\s{2,}", " ", f"{act_txt} {team_clean}".strip())

# =============================
# LOAD CSV (ANTI-CRASH)
# =============================
@st.cache_data(ttl=180, show_spinner=False)
def load_csv(url: str):
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, timeout=(6, 25), headers=headers, allow_redirects=True)
    r.raise_for_status()

    txt = r.text or ""
    ctype = (r.headers.get("Content-Type") or "").lower()
    if "<html" in txt.lower() and "text/csv" not in ctype and "application/csv" not in ctype:
        return pd.DataFrame(), txt

    df_ = pd.read_csv(io.StringIO(txt), dtype=str, engine="python", on_bad_lines="skip").fillna("")
    df_.columns = [str(c).strip() for c in df_.columns]
    return df_, txt

try:
    df, raw_txt = load_csv(CSV_URL)
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
    st.error("No data loaded from Google Sheets yet. Republish the sheet and refresh.")
    if st.button("Retry"):
        st.cache_data.clear()
        st.rerun()
    st.stop()

with st.sidebar:
    if st.button("🔄 Refresh data", key="btn_refresh"):
        st.cache_data.clear()
        st.rerun()

# =============================
# COLUMNS
# =============================
COL_CATEGORY  = "Category"
COL_ACTIVITY  = "Activity/Subject Name"
COL_TEAM      = "Team / Assessment"
COL_DATE      = "Date / Due Date"
COL_VENUE     = "Venue"
COL_PROGRAMME = "Programme / Document Link"
COL_TEAMS_LNK = "Team"
COL_CONFIRM   = "Confirm"
COL_INFO      = "Information"
COL_GRADE     = "Age Group (9,10) / Grade (1,2,3)"
COL_TERM      = "Display Duration"

def s(colname):
    return df[colname].astype(str) if colname in df.columns else pd.Series([""] * len(df), dtype=str)

cat_s     = s(COL_CATEGORY)
act_s     = s(COL_ACTIVITY)
team_s    = s(COL_TEAM)
date_s    = s(COL_DATE)
ven_s     = s(COL_VENUE)
prog_s    = s(COL_PROGRAMME)
teamlnk_s = s(COL_TEAMS_LNK)
conf_s    = s(COL_CONFIRM)
info_s    = s(COL_INFO)
grade_s   = s(COL_GRADE)
term_s    = s(COL_TERM)

TS_COL = pick_timestamp_column_smart(df)
ts_s = df[TS_COL].astype(str) if TS_COL in df.columns else pd.Series([""] * len(df), dtype=str)

# =============================
# VIEW
# =============================
st.radio(
    "View",
    VIEW_OPTIONS,
    index=VIEW_OPTIONS.index(st.session_state.get("view_mode", "Upcoming"))
    if st.session_state.get("view_mode", "Upcoming") in VIEW_OPTIONS else 0,
    horizontal=True,
    key="view_mode",
)

# =============================
# FILTERS
# =============================
st.sidebar.markdown("## Filters")

category_choice = st.sidebar.multiselect(
    "Category",
    ["Sport", "Culture", "Academics"],
    default=st.session_state.cat_choice,
    key="cat_choice",
)

st.sidebar.text_input(
    "Whole school search",
    value=st.session_state.search_text,
    placeholder="Type to filter...",
    key="search_text",
)

wanted = {c.lower() for c in category_choice} if category_choice else set()

def cat_ok(i: int) -> bool:
    if not wanted:
        return True
    cn = normalize_category(cat_s.iloc[i])
    return (
        ("sport" in wanted and cn == "sport")
        or ("culture" in wanted and cn == "culture")
        or ("academics" in wanted and cn == "academics")
    )

act_opts = sorted({
    normalize_activity(act_s.iloc[i])
    for i in range(len(df))
    if str(act_s.iloc[i]).strip() and cat_ok(i)
})

st.sidebar.multiselect(
    "Activity/Subject",
    act_opts,
    default=[a for a in st.session_state.act_choice if a in act_opts],
    key="act_choice",
)

selected_u = st.sidebar.multiselect(
    "Age Groups (Sport)",
    [f"U{i}" for i in range(7, 14)],
    default=st.session_state.u_choice,
    key="u_choice",
) if (not wanted or "sport" in wanted) else []

selected_gr = st.sidebar.multiselect(
    "Grades (Culture/Academics)",
    [f"Gr {i}" for i in range(1, 8)],
    default=st.session_state.gr_choice,
    key="gr_choice",
) if (not wanted or "culture" in wanted or "academics" in wanted) else []

# New Updates window slider (only visible in that view)
NEW_UPDATES_HOURS = NEW_UPDATES_HOURS_DEFAULT
if st.session_state.view_mode == "New Updates":
    NEW_UPDATES_HOURS = st.sidebar.slider("New Updates window (hours)", 1, 72, NEW_UPDATES_HOURS_DEFAULT)

# =============================
# MATCHING NORMALIZATION (fixes Gr 4 vs Gr4 etc.)
# =============================
def norm_token(x: str) -> str:
    return str(x or "").lower().replace(" ", "").strip()

selected_u_norm = {norm_token(x) for x in set(selected_u)}
selected_gr_norm = {norm_token(x) for x in set(selected_gr)}

# ✅ Auto-scope when Category is empty
force_sport = (not wanted) and bool(selected_u_norm) and not bool(selected_gr_norm)
force_grades = (not wanted) and bool(selected_gr_norm) and not bool(selected_u_norm)

# =============================
# WRITE STATE -> QUERY PARAMS (ONLY IF CHANGED)
# =============================
payload = {
    "view": st.session_state.view_mode,
    "cat": st.session_state.cat_choice,
    "act": st.session_state.act_choice,
    "u": st.session_state.u_choice,
    "gr": st.session_state.gr_choice,
    "q": st.session_state.search_text,
}
if st.session_state.get("_last_qp_payload") != payload:
    st.session_state["_last_qp_payload"] = payload
    qp_set_from_state(payload)

# =============================
# BUILD RESULTS
# =============================
res = []
for i in range(len(df)):
    cn = normalize_category(cat_s.iloc[i])
    act_norm = normalize_activity(act_s.iloc[i])

    # Auto-scope when no category is selected
    if force_sport and cn != "sport":
        continue
    if force_grades and cn == "sport":
        continue

    if wanted and not cat_ok(i):
        continue
    if st.session_state.act_choice and act_norm not in st.session_state.act_choice:
        continue

    # Stable "new" based on sheet timestamp
    created_dt = parse_sheet_timestamp(ts_s.iloc[i])
    is_recent = False
    if created_dt:
        try:
            is_recent = (now_dt - created_dt) <= timedelta(hours=NEW_UPDATES_HOURS)
        except Exception:
            is_recent = False

    # View mode: New Updates (based on timestamp)
    if st.session_state.view_mode == "New Updates":
        if not is_recent:
            continue

    term_val = str(term_s.iloc[i]).strip().lower()
    looks_like_term_doc = any(
        k in (act_norm.lower() + " " + str(team_s.iloc[i]).lower())
        for k in ["spelling", "speltoets", "spellys", "assessment schedule", "assessment", "toets", "toetse"]
    )
    term_flag = ("full term" in term_val) or ("term" in term_val) or (looks_like_term_doc and cn == "academics")

    d_raw = str(date_s.iloc[i]).strip()
    d_dt = parse_date_sa(d_raw)

    if d_dt and d_dt.date() < today:
        continue

    if st.session_state.view_mode == "Next 7 Days":
        if not d_dt:
            continue
        if d_dt.date() > (today + timedelta(days=7)):
            continue

    if st.session_state.view_mode == "Term Documents":
        if not term_flag:
            continue

    grp_disp, grp_matches = group_for_row(cn, grade_s.iloc[i], team_s.iloc[i])

    # Sport: overlap match (normalized tokens)
    if cn == "sport" and selected_u_norm:
        if not grp_matches:
            continue
        grp_norm = {norm_token(x) for x in grp_matches}
        if not (selected_u_norm & grp_norm):
            continue

    # Culture/Academics: overlap match (normalized tokens)
    if cn in ["culture", "academics"] and selected_gr_norm:
        if not grp_matches:
            continue
        grp_norm = {norm_token(x) for x in grp_matches}
        if not (selected_gr_norm & grp_norm):
            continue

    title = build_title(cat_s.iloc[i], act_s.iloc[i], team_s.iloc[i], grade_s.iloc[i])

    if st.session_state.search_text:
        needle = st.session_state.search_text.lower().replace(" ", "")
        hay = title.lower().replace(" ", "")
        if needle not in hay:
            continue

    sort_dt = d_dt if d_dt else datetime(2099, 1, 1)
    grade_raw_for_sort = str(grade_s.iloc[i] or "").strip()

    res.append({
        "i": i,
        "dt": sort_dt,
        "title": title.lower(),
        "term": term_flag,
        "new": is_recent,
        "created_dt": created_dt,
        "grade": grade_raw_for_sort,
    })

term_items = sorted([x for x in res if x["term"]], key=lambda x: (x["title"], x["grade"]))
other_items = sorted([x for x in res if not x["term"]], key=lambda x: (x["dt"], x["title"], x["grade"]))
res_sorted = term_items + other_items

# =============================
# DISPLAY
# =============================
st.markdown("## 📅 Events")
pin = "&#128205;"

if not res_sorted:
    st.info("No items match your filters.")
else:
    for item in res_sorted:
        i = item["i"]
        cn = normalize_category(cat_s.iloc[i])
        afr = is_afrikaans_subject(act_s.iloc[i])

        title = build_title(cat_s.iloc[i], act_s.iloc[i], team_s.iloc[i], grade_s.iloc[i])

        d_raw = str(date_s.iloc[i]).strip()
        date_line = format_date_long_sa(d_raw) if d_raw else ""

        _grp_disp, grp_matches = group_for_row(cn, grade_s.iloc[i], team_s.iloc[i])

        ven_norm = normalize_venue(str(ven_s.iloc[i]).strip())

        prog_link = first_url(prog_s.iloc[i])
        teams_link = first_url(teamlnk_s.iloc[i])
        confirm_link = first_url(conf_s.iloc[i])

        info_raw = str(info_s.iloc[i]).strip().replace("_", " ")
        info_text, info_links = split_info_text_and_links(info_raw)

        buttons = []
        notes_parts = []

        if cn == "academics":
            b_docs = "Dokumente" if afr else "Documents"
            b_info = "Inligting" if afr else "Information"
            if prog_link and is_http(prog_link):
                buttons.append((b_docs, prog_link))
            for idx, lk in enumerate(info_links, start=1):
                if is_http(lk):
                    buttons.append((b_info if idx == 1 else f"{b_info} {idx}", lk))
        else:
            if prog_link and is_http(prog_link):
                buttons.append(("Programme", prog_link))
            if teams_link and is_http(teams_link):
                buttons.append(("Teams", teams_link))
            for idx, lk in enumerate(info_links, start=1):
                if is_http(lk):
                    buttons.append(("Information" if idx == 1 else f"Information {idx}", lk))
            if confirm_link and is_http(confirm_link) and ("forms.gle" in confirm_link.lower() or "docs.google.com/forms" in confirm_link.lower()):
                buttons.append(("Confirm", confirm_link))

        venue_line = ""
        if ven_norm == "SEE_PROGRAMME":
            notes_parts.append("<b>Venue:</b><br>See programme")
        elif ven_norm:
            q = ven_norm
            if "midstream" in ven_norm.lower():
                q = f"{ven_norm} Midstream College"
            map_url = f"https://www.google.com/maps/search/?api=1&query={q.replace(' ', '+')}"
            venue_line = (
                f"<div class='meta'>{pin} "
                f"<a href='{map_url}' target='_blank' style='color:#008080;font-weight:900;text-decoration:none;'>"
                f"{safe_txt(ven_norm).upper()}</a></div>"
            )

        if info_text:
            notes_parts.append(f"<b>Note:</b><br>{safe_txt(info_text)}")

        notes_block = f"<div class='noteBlock'>{'<br><br>'.join(notes_parts)}</div>" if notes_parts else ""

        btn_html = ""
        if buttons:
            btn_html = "<div class='btnRow'>" + "".join(
                [f"<a class='btn' href='{u}' target='_blank'>{safe_txt(lbl)}</a>" for lbl, u in buttons[:4]]
            ) + "</div>"

        ribbon = ""
        if item["new"]:
            created_dt = item.get("created_dt")
            dot = "<span class='rDot'></span>"
            if created_dt:
                try:
                    if (now_dt - created_dt) > timedelta(minutes=BADGE_ANIMATE_MINUTES):
                        dot = "<span style='width:8px;height:8px;border-radius:999px;background:#B00000;display:inline-block;opacity:.9;'></span>"
                except Exception:
                    pass
            ribbon = f"<div class='ribbon'>{dot}NEW UPDATE</div>"

        # Clear “why is this showing” lines (no duplicate U/Gr)
        sport_age_line = ""
        grade_line = ""
        if cn == "sport" and grp_matches:
            sport_age_line = f"<div class='meta'><b>Ages:</b> {safe_txt(grp_matches[0])}{'–' + safe_txt(grp_matches[-1]) if len(grp_matches) >= 2 else ''}</div>"
        if cn in ["culture", "academics"] and grp_matches:
            grade_line = f"<div class='meta'><b>Grades:</b> {safe_txt(grp_matches[0])}{'–' + safe_txt(grp_matches[-1]) if len(grp_matches) >= 2 else ''}</div>"

        st.markdown(
            f"""
<div class="card">
  {ribbon}
  <div class="card-title">{safe_txt(title)}</div>
  {f"<div class='meta'>📅 <b>{safe_txt(date_line)}</b></div>" if date_line else ""}
  {sport_age_line}
  {grade_line}
  {venue_line}
  {notes_block}
  {btn_html}
</div>
""",
            unsafe_allow_html=True,
        )

st.markdown(
    "<br><center style='font-size:0.85rem;color:#94a3b8;'>LAERSKOOL MIDSTREAM COLLEGE PRIMARY Digital Hub 2026</center>",
    unsafe_allow_html=True,
)
