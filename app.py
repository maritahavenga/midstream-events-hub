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

UPCOMING_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"
SUBMISSIONS_CSV_URL = "https://docs.google.com/spreadsheets/d/1jB78iGRp3pmwib7k_MfdwzMC402QY9MPtHKC3TAAlPQ/export?format=csv&gid=1864466191"

LOGO_URL = "https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg"
FACILITIES_MAP_URL = "https://drive.google.com/file/d/1PR-o4unbkpy7wq0Rg3nUf3wP1gHn_662/view?usp=sharing"

TZ = pytz.timezone("Africa/Johannesburg")
now_dt = datetime.now(TZ)
today = now_dt.date()

# ✅ Added "Test Breakdown" as a RADIO option (view)
VIEW_OPTIONS = ["All", "Next 7 Days", "Term Documents", "Assessment Schedule", "Test Breakdown", "New Updates"]
NEW_UPDATES_DEFAULT_HOURS = 72
BADGE_ANIMATE_MINUTES = 10

# =============================
# QUICK SELECT (clean dropdown)
# =============================
QUICK_GRADE_PLACEHOLDER = "Select a grade…"
QUICK_GRADE_CLEAR = "Clear selection"
QUICK_GRADE_OPTIONS = [QUICK_GRADE_PLACEHOLDER, "Gr 1-3", "Gr 4", "Gr 5", "Gr 6", "Gr 7", QUICK_GRADE_CLEAR]

GRADE_TO_U_MAP = {
    "Gr 1-3": ["U7", "U8", "U9"],
    "Gr 4": ["U10"],
    "Gr 5": ["U11"],
    "Gr 6": ["U12"],
    "Gr 7": ["U13"],
}

# =============================
# QUERY PARAMS HELPERS
# =============================
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

ss_init("screen_mode", "Events")  # Events | Filter
ss_init("view_mode", "All")
ss_init("cat_choice", [])
ss_init("act_choice", [])
ss_init("u_choice", [])
ss_init("gr_choice", [])
ss_init("search_text", "")

ss_init("quick_grade_ui", QUICK_GRADE_PLACEHOLDER)
ss_init("_qg_applied", QUICK_GRADE_PLACEHOLDER)
ss_init("_pending_qg_reset", False)
ss_init("_request_rerun", False)
ss_init("_request_qp_sync", False)

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

    qg = qp_get("qg", QUICK_GRADE_PLACEHOLDER)
    if qg in QUICK_GRADE_OPTIONS:
        st.session_state.quick_grade_ui = qg
        st.session_state._qg_applied = QUICK_GRADE_PLACEHOLDER

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
div[data-testid="stSidebar"] label,
div[data-testid="stSidebar"] p,
div[data-testid="stSidebar"] span{
  white-space:normal !important;
  word-break:break-word !important;
}
button[data-testid="collapsedControl"],
button[data-testid="stSidebarCollapseButton"]{
  transform: scale(1.18);
  transform-origin: left center;
  font-weight: 900 !important;
}
button[data-testid="collapsedControl"] svg,
button[data-testid="stSidebarCollapseButton"] svg{
  width: 26px !important;
  height: 26px !important;
}
button[data-testid="collapsedControl"]::after,
button[data-testid="stSidebarCollapseButton"]::after{
  content:"  Filter here";
  font-weight: 1000;
  font-size: 1.05rem;
  color: var(--teal);
  margin-left: 8px;
}
div[data-testid="stBaseButton-primary"] > button{
  background: var(--teal) !important;
  border: 1px solid rgba(0,0,0,0.08) !important;
  font-weight: 1000 !important;
  padding: 0.8rem 1rem !important;
  border-radius: 14px !important;
}
div[data-testid="stBaseButton-primary"] > button:hover{opacity:.92;}
div[data-testid="stBaseButton-secondary"] > button{
  font-weight: 900 !important;
  padding: 0.8rem 1rem !important;
  border-radius: 14px !important;
}
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
.smallTopHelp{font-size:.85rem;color:#e6fffb;margin-top:-6px;}
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
    <div class="smallTopHelp">Use Quick Select for Grade + Age group, or tap FILTER for advanced filters.</div>
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

def extract_urls(v: str):
    raw = str(v or "").strip()
    if not raw:
        return []
    urls = [u.strip() for u in URL_RE.findall(raw) if u.strip()]
    seen, out = set(), []
    for u in urls:
        if u not in seen:
            out.append(u)
            seen.add(u)
    return out

def urls_signature_part(v: str) -> str:
    links = extract_urls(v)
    return "|".join(links[:2])

def split_info_text_and_links(info: str):
    raw = str(info or "").strip()
    if not raw:
        return "", []
    links = URL_RE.findall(raw)
    text = URL_RE.sub("", raw)
    text = re.sub(r"\s{2,}", " ", text).strip(" -\n\t|")
    return text, links

def norm_token(x: str) -> str:
    return str(x or "").lower().replace(" ", "").strip()

def normalize_category(v: str) -> str:
    s = str(v or "").strip().lower()
    if "sport" in s: return "sport"
    if "culture" in s or "kultuur" in s: return "culture"
    if "academic" in s or "academics" in s or "akadem" in s: return "academics"
    return s

def is_afrikaans_subject(b_raw: str) -> bool:
    s = str(b_raw or "").strip().lower()
    return ("afrikaans" in s) or (s in ["ht", "eat"]) or ("hooftaal" in s) or ("eerste addisionele" in s)

def is_assessment_schedule(activity_raw: str, team_raw: str) -> bool:
    s = (str(activity_raw or "") + " " + str(team_raw or "")).strip().lower()
    return "assessment schedule" in s

def norm_gender_words(text: str) -> str:
    s = str(text or "").strip().replace("_", " ")
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"\bmeisies\b", "Girls", s, flags=re.I)
    s = re.sub(r"\bseuns\b", "Boys", s, flags=re.I)
    s = re.sub(r"\bgirls\b", "Girls", s, flags=re.I)
    s = re.sub(r"\bboys\b", "Boys", s, flags=re.I)
    return re.sub(r"\s+", " ", s).strip()

def is_math_activity(activity_raw: str) -> bool:
    s = re.sub(r"\s+", " ", str(activity_raw or "").strip().lower())
    return ("wiskunde" in s) or ("mathematics" in s) or ("maths" in s) or (s == "math") or ("math " in s)

# ✅ Test Breakdown detector
def is_test_breakdown_row(activity_raw: str, team_raw: str, info_raw_full: str) -> bool:
    a = str(activity_raw or "").lower()
    t = str(team_raw or "").lower()
    inf = str(info_raw_full or "").lower()
    return ("test breakdown" in a) or ("test breakdown" in t) or ("test breakdown" in inf)

# ✅ remove "Test Breakdown" from subject display/filter
def strip_test_breakdown_label(s: str) -> str:
    raw = str(s or "").strip()
    if not raw:
        return ""
    out = re.sub(r"\btest\s*breakdown\b", "", raw, flags=re.I)
    out = re.sub(r"\s{2,}", " ", out).strip(" -–|:")
    return out.strip()

# =============================
# ACTIVITY: display vs filter
# =============================
def display_activity(cat_norm: str, activity_raw: str) -> str:
    s = str(activity_raw or "").strip()
    if cat_norm == "sport":
        return s

    sl = re.sub(r"\s+", " ", s.lower().strip())
    if sl in ["ht", "afrikaans ht"] or "hooftaal" in sl:
        return "Afrikaans Hooftaal"
    if sl in ["eat", "afrikaans eat"] or "eerste addisionele" in sl:
        return "Afrikaans Eerste Addisionele Taal"

    if is_math_activity(sl):
        return "Mathematics"

    s = strip_test_breakdown_label(s)
    return s.title() if s else ""

def sport_base_activity(activity_raw: str) -> str:
    s = re.sub(r"\s+", " ", str(activity_raw or "").strip().lower())
    if "swim" in s or "swem" in s or "gala" in s: return "Swimming"
    if "athlet" in s or "atletiek" in s: return "Athletics"
    if "mountain bike" in s or "mtb" in s or "biking" in s or "cycling" in s or "fiets" in s: return "Mountain Biking"
    if "rugby" in s: return "Rugby"
    if "hockey" in s: return "Hockey"
    if "netball" in s or "netbal" in s: return "Netball"
    if "tennis" in s: return "Tennis"
    if "cricket" in s: return "Cricket"
    if "soccer" in s or "football" in s or "sokker" in s: return "Soccer"
    return str(activity_raw or "").strip().split(" ")[0].title() if str(activity_raw or "").strip() else ""

def activity_filter_key(cat_norm: str, activity_raw: str) -> str:
    if cat_norm == "sport":
        return sport_base_activity(activity_raw)
    return display_activity(cat_norm, activity_raw)

# =============================
# DATE PARSING
# =============================
def parse_date_sa(s):
    raw = str(s or "").strip()
    if not raw or raw.lower() in ["nan", "none"]:
        return None
    cleaned = re.sub(r"\s+", " ", raw.replace(".", "/").replace("-", "/"))
    d1 = pd.to_datetime(cleaned, dayfirst=True, errors="coerce")
    if not pd.isnull(d1): return d1.to_pydatetime()
    d2 = pd.to_datetime(cleaned, dayfirst=False, errors="coerce")
    if not pd.isnull(d2): return d2.to_pydatetime()
    return None

def format_date_long_sa(s) -> str:
    dt = parse_date_sa(s)
    if not dt: return str(s or "").strip()
    return f"{dt.day} {dt.strftime('%B %Y')}"

def parse_form_timestamp(x):
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

# =============================
# VENUE
# =============================
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
    s = re.sub(r"\s+", " ", str(v or "").strip().replace("_", " "))
    sl = s.lower()
    if "see programme" in sl or "see program" in sl or "sien program" in sl or "sien programme" in sl:
        return "SEE_PROGRAMME"
    for k, vv in VENUE_MAP.items():
        if k in sl:
            return vv
    return s

CAMPUS_VENUE_LABELS = {
    "music room", "hall", "auditorium", "field", "bondev field", "swimming pool",
    "tennis courts", "netball courts", "cricket oval"
}
CAMPUS_VENUE_KEYWORDS = [
    "midstream", "midstream college", "lmcp", "primary", "college",
    "auditorium", "hall", "music room", "field", "bondev",
    "pool", "swimming", "tennis", "netball", "cricket", "oval",
    "court", "courts"
]

def is_midstream_campus_venue(ven_norm: str) -> bool:
    v = str(ven_norm or "").strip().lower()
    if not v:
        return False
    if v in CAMPUS_VENUE_LABELS:
        return True
    return any(k in v for k in CAMPUS_VENUE_KEYWORDS)

# =============================
# AGE GROUP / GRADE PARSING
# =============================
def expand_group_range(raw: str, kind: str):
    s = str(raw or "").strip()
    if not s:
        return []
    s = s.replace("–", "-").replace("—", "-")
    s = re.sub(r"\s*(/|&|\+|and|en|to)\s*", ",", s, flags=re.I)

    s_nospace = re.sub(r"\s+", "", s)
    nums = [int(n) for n in re.findall(r"\d+", s_nospace)]
    if not nums:
        return []

    if "-" in s_nospace and len(nums) >= 2:
        lo, hi = sorted([nums[0], nums[1]])
        seq = list(range(lo, hi + 1))
        return [f"U{x}" for x in seq] if kind == "U" else [f"Gr {x}" for x in seq]

    return [f"U{x}" for x in nums] if kind == "U" else [f"Gr {x}" for x in nums]

def extract_u_groups_from_text(text: str):
    t = str(text or "").strip().replace("–", "-").replace("—", "-")
    if not t:
        return []
    m = re.search(r"\bU?\d{1,2}\s*-\s*U?\d{1,2}\b", t, flags=re.I)
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
    t = re.sub(r"\bU\d{1,2}\b", "", t, flags=re.I)

    t = re.sub(r"\bGr\.?\s*\d{1,2}\s*[-–]\s*Gr\.?\s*\d{1,2}\b", "", t, flags=re.I)
    t = re.sub(r"\bGr\.?\s*\d{1,2}(?:\s*,\s*Gr\.?\s*\d{1,2}){1,}\b", "", t, flags=re.I)
    t = re.sub(r"\bGr\.?\s*\d{1,2}\b", "", t, flags=re.I)

    return re.sub(r"\s{2,}", " ", t).strip(" -–|,")

def tidy_team_text(s: str) -> str:
    t = str(s or "").strip().replace("&amp;", "&")
    if not t:
        return ""
    t = re.sub(r"\bU\s+(\d{1,2})\b", r"U\1", t, flags=re.I)
    t = re.sub(r"(U\d{1,2})(Girls|Boys)\b", r"\1 \2", t, flags=re.I)
    return re.sub(r"\s{2,}", " ", t).strip()

def build_title(cat_norm: str, act_val: str, team_val: str, grade_val: str) -> str:
    act_txt = norm_gender_words(display_activity(cat_norm, act_val))
    team_clean = tidy_team_text(norm_gender_words(strip_group_tokens(team_val)))

    if cat_norm == "sport":
        grp_disp, _ = group_for_row("sport", grade_val, team_val)
        if sport_base_activity(act_val) == "Tennis":
            base = re.sub(r"\s{2,}", " ", f"{act_txt} {team_clean}".strip())
            return f"{base} ({grp_disp})".strip() if grp_disp else base
        if not team_clean:
            return f"{act_txt} ({grp_disp})".strip() if grp_disp else act_txt
        return re.sub(r"\s{2,}", " ", f"{act_txt} {team_clean}".strip())

    base = re.sub(r"\s{2,}", " ", f"{act_txt} {team_clean}".strip())
    if cat_norm == "academics":
        g_disp, g_list = group_for_row("academics", grade_val, team_val)
        if g_list:
            if len(g_list) >= 2:
                g_disp = f"{g_list[0]}–{g_list[-1]}"
            else:
                g_disp = g_list[0]
        if g_disp:
            return f"{base} ({g_disp})".strip()
    return base

# =============================
# LOAD CSV
# =============================
@st.cache_data(ttl=180, show_spinner=False)
def load_csv(url: str):
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, timeout=(6, 25), headers=headers, allow_redirects=True)
    r.raise_for_status()
    txt = r.text or ""
    df_ = pd.read_csv(io.StringIO(txt), dtype=str, engine="python", on_bad_lines="skip").fillna("")
    df_.columns = [str(c).strip() for c in df_.columns]
    return df_

def safe_load(url: str):
    try:
        return load_csv(url)
    except Timeout:
        st.warning("⏳ A Google Sheet took too long to respond.")
        return pd.DataFrame()
    except RequestException:
        st.warning("⚠️ Could not connect to Google Sheets right now.")
        return pd.DataFrame()
    except Exception as e:
        st.warning("⚠️ Something went wrong while loading a sheet.")
        with st.expander("Technical details"):
            st.code(str(e))
        return pd.DataFrame()

df = safe_load(UPCOMING_CSV_URL)
if df.empty:
    st.error("No data loaded from the Upcoming sheet.")
    st.stop()

sub_df = safe_load(SUBMISSIONS_CSV_URL)
if sub_df.empty:
    st.warning("Responses sheet could not be read as CSV. Check sharing: Anyone with link = Viewer.")

with st.sidebar:
    if st.button("🔄 Refresh data", key="btn_refresh"):
        st.cache_data.clear()
        st.rerun()
    st.caption("Use the **FILTER** button at the top to set filters.")

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

# =============================
# Matching Upcoming <-> Responses for New Updates (+ Contact email)
# =============================
def row_signature(category, activity, team_assessment, due_date, venue, programme_link):
    parts = [
        normalize_category(category),
        norm_token(activity),
        norm_token(team_assessment),
        norm_token(due_date),
        norm_token(venue),
        norm_token(urls_signature_part(programme_link)),
    ]
    return hashlib.sha256("||".join(parts).encode("utf-8")).hexdigest()

sig_to_created = {}
sig_to_email = {}

if not sub_df.empty and "Timestamp" in sub_df.columns:
    ts_col = "Timestamp"

    def sub_col(name):
        return sub_df[name].astype(str) if name in sub_df.columns else pd.Series([""] * len(sub_df), dtype=str)

    sub_ts    = sub_df[ts_col].astype(str)
    sub_cat   = sub_col(COL_CATEGORY)
    sub_act   = sub_col(COL_ACTIVITY)
    sub_team  = sub_col(COL_TEAM)
    sub_date  = sub_col(COL_DATE)
    sub_ven   = sub_col(COL_VENUE)
    sub_prog  = sub_col(COL_PROGRAMME)
    sub_email = sub_col("Email address")

    for j in range(len(sub_df)):
        created_dt = parse_form_timestamp(sub_ts.iloc[j])
        if not created_dt:
            continue
        sig = row_signature(
            sub_cat.iloc[j], sub_act.iloc[j], sub_team.iloc[j],
            sub_date.iloc[j], sub_ven.iloc[j], sub_prog.iloc[j]
        )
        prev = sig_to_created.get(sig)
        if (prev is None) or (created_dt > prev):
            sig_to_created[sig] = created_dt
            sig_to_email[sig] = str(sub_email.iloc[j] or "").strip()

# =============================
# TOP BAR (Quick Select + Filter)
# =============================
if st.session_state.get("_pending_qg_reset", False):
    st.session_state.quick_grade_ui = QUICK_GRADE_PLACEHOLDER
    st.session_state._qg_applied = QUICK_GRADE_PLACEHOLDER
    st.session_state._pending_qg_reset = False

top_left, top_mid, top_right = st.columns([2.2, 1.0, 1.2])

with top_left:
    if st.session_state.screen_mode == "Events":
        st.selectbox(
            "Quick select",
            QUICK_GRADE_OPTIONS,
            index=QUICK_GRADE_OPTIONS.index(st.session_state.quick_grade_ui)
            if st.session_state.quick_grade_ui in QUICK_GRADE_OPTIONS else 0,
            key="quick_grade_ui",
            label_visibility="collapsed",
        )

with top_mid:
    if st.session_state.screen_mode == "Events":
        qg = st.session_state.quick_grade_ui
        if qg in QUICK_GRADE_OPTIONS and qg != st.session_state._qg_applied:
            if qg == QUICK_GRADE_CLEAR:
                st.session_state._pending_qg_reset = True
                st.session_state._qg_applied = QUICK_GRADE_CLEAR
                st.session_state._request_qp_sync = True
                st.session_state._request_rerun = True
            elif qg == QUICK_GRADE_PLACEHOLDER:
                st.session_state._qg_applied = qg
            else:
                if qg == "Gr 1-3":
                    st.session_state.gr_choice = ["Gr 1", "Gr 2", "Gr 3"]
                else:
                    st.session_state.gr_choice = [qg]
                st.session_state.u_choice = GRADE_TO_U_MAP.get(qg, [])
                st.session_state._qg_applied = qg
                st.session_state._request_qp_sync = True
                st.session_state._request_rerun = True

with top_right:
    if st.session_state.screen_mode == "Events":
        if st.button("🔎 FILTER", key="go_filter_top", type="primary", use_container_width=True):
            st.session_state.screen_mode = "Filter"
            st.rerun()
    else:
        if st.button("⬅ Back to Events", key="back_events_top", type="secondary", use_container_width=True):
            st.session_state.screen_mode = "Events"
            st.rerun()

# =============================
# VIEW RADIO
# =============================
st.radio(
    "Show",
    VIEW_OPTIONS,
    index=VIEW_OPTIONS.index(st.session_state.get("view_mode", "All"))
    if st.session_state.get("view_mode", "All") in VIEW_OPTIONS else 0,
    horizontal=True,
    key="view_mode",
)

# =============================
# FILTERS
# =============================
wanted = set()
selected_u_norm = set()
selected_gr_norm = set()
force_sport = False
force_grades = False
new_hours = NEW_UPDATES_DEFAULT_HOURS

TARGET_GRADES_MATH = {"gr4", "gr5", "gr6", "gr7"}

def selected_grade_tokens_to_labels(sel_norm: set):
    out = []
    for t in sorted(sel_norm):
        m = re.match(r"gr(\d+)", t)
        if m:
            out.append(f"Gr {int(m.group(1))}")
    return out

def clear_all_filters():
    st.session_state.cat_choice = []
    st.session_state.act_choice = []
    st.session_state.u_choice = []
    st.session_state.gr_choice = []
    st.session_state.search_text = ""
    st.session_state.quick_grade_ui = QUICK_GRADE_PLACEHOLDER
    st.session_state._qg_applied = QUICK_GRADE_PLACEHOLDER
    st.query_params.from_dict({})
    st.session_state.screen_mode = "Events"
    st.rerun()

def save_and_back():
    payload_now = {
        "view": st.session_state.view_mode,
        "cat": st.session_state.cat_choice,
        "act": st.session_state.act_choice,
        "u": st.session_state.u_choice,
        "gr": st.session_state.gr_choice,
        "q": st.session_state.search_text,
        "qg": st.session_state.quick_grade_ui,
    }
    qp_set_from_state(payload_now)
    st.session_state._request_qp_sync = False
    st.session_state.screen_mode = "Events"
    st.rerun()

def render_filters_main():
    global wanted, selected_u_norm, selected_gr_norm, force_sport, force_grades, new_hours

    st.markdown("## 🔎 Filters")

    a1, a2, a3 = st.columns([1, 1, 1])
    with a1:
        if st.button("✅ Save filters & Back to Events", key="save_back_top", type="primary", use_container_width=True):
            save_and_back()
    with a2:
        if st.button("🧹 Clear all filters", key="clear_all_top", type="secondary", use_container_width=True):
            clear_all_filters()
    with a3:
        if st.button("⬅ Back (no changes)", key="back_no_save_top", type="secondary", use_container_width=True):
            st.session_state.screen_mode = "Events"
            st.rerun()

    st.markdown("---")

    st.multiselect(
        "Category",
        ["Sport", "Culture", "Academics"],
        default=st.session_state.cat_choice,
        key="cat_choice",
    )

    st.text_input(
        "Whole school search",
        value=st.session_state.search_text,
        placeholder="Type to filter...",
        key="search_text",
    )

    wanted = {c.lower() for c in st.session_state.cat_choice} if st.session_state.cat_choice else set()

    def cat_ok_local(i: int) -> bool:
        if not wanted:
            return True
        cn = normalize_category(cat_s.iloc[i])
        return (
            ("sport" in wanted and cn == "sport")
            or ("culture" in wanted and cn == "culture")
            or ("academics" in wanted and cn == "academics")
        )

    act_opts = sorted({
        activity_filter_key(normalize_category(cat_s.iloc[i]), act_s.iloc[i])
        for i in range(len(df))
        if str(act_s.iloc[i]).strip() and cat_ok_local(i)
    })

    if (not wanted) or ("academics" in wanted) or ("culture" in wanted):
        act_opts = sorted(set(act_opts) | {"Mathematics", "Test Breakdown"})

    st.multiselect(
        "Activity/Subject",
        act_opts,
        default=[a for a in st.session_state.act_choice if a in act_opts],
        key="act_choice",
    )

    selected_u = st.multiselect(
        "Age Groups (Sport)",
        [f"U{i}" for i in range(7, 14)],
        default=st.session_state.u_choice,
        key="u_choice",
    ) if (not wanted or "sport" in wanted) else []

    grade_options = [f"Gr {i}" for i in range(1, 8)]
    selected_gr = st.multiselect(
        "Grades (Culture/Academics)",
        grade_options,
        default=[g for g in st.session_state.gr_choice if g in grade_options],
        key="gr_choice",
    ) if (not wanted or "culture" in wanted or "academics" in wanted) else []

    selected_u_norm = {norm_token(x) for x in set(selected_u)}
    selected_gr_norm = {norm_token(x) for x in set(selected_gr)}

    force_sport  = (not wanted) and bool(selected_u_norm) and not bool(selected_gr_norm)
    force_grades = (not wanted) and bool(selected_gr_norm) and not bool(selected_u_norm)

    if st.session_state.view_mode == "New Updates":
        new_hours = st.slider("New Updates window (hours)", 1, 336, NEW_UPDATES_DEFAULT_HOURS)
    else:
        new_hours = NEW_UPDATES_DEFAULT_HOURS

    st.markdown("---")

    b1, b2, b3 = st.columns([1, 1, 1])
    with b1:
        if st.button("✅ Save filters & Back to Events", key="save_back_bottom", type="primary", use_container_width=True):
            save_and_back()
    with b2:
        if st.button("🧹 Clear all filters", key="clear_all_bottom", type="secondary", use_container_width=True):
            clear_all_filters()
    with b3:
        if st.button("⬅ Back (no changes)", key="back_no_save_bottom", type="secondary", use_container_width=True):
            st.session_state.screen_mode = "Events"
            st.rerun()

if st.session_state.screen_mode == "Filter":
    render_filters_main()

if st.session_state.screen_mode == "Events":
    wanted = {c.lower() for c in st.session_state.cat_choice} if st.session_state.cat_choice else set()
    selected_u_norm = {norm_token(x) for x in set(st.session_state.u_choice)}
    grade_options = [f"Gr {i}" for i in range(1, 8)]
    selected_gr_norm = {norm_token(x) for x in set([g for g in st.session_state.gr_choice if g in grade_options])}

    force_sport  = (not wanted) and bool(selected_u_norm) and not bool(selected_gr_norm)
    force_grades = (not wanted) and bool(selected_gr_norm) and not bool(selected_u_norm)
    new_hours = NEW_UPDATES_DEFAULT_HOURS

# =============================
# SAFE URL SYNC + RERUN
# =============================
payload = {
    "view": st.session_state.view_mode,
    "cat": st.session_state.cat_choice,
    "act": st.session_state.act_choice,
    "u": st.session_state.u_choice,
    "gr": st.session_state.gr_choice,
    "q": st.session_state.search_text,
    "qg": st.session_state.quick_grade_ui,
}
if st.session_state.get("_last_qp_payload") != payload:
    st.session_state["_last_qp_payload"] = payload
    qp_set_from_state(payload)

if st.session_state.get("_request_qp_sync"):
    st.session_state._request_qp_sync = False

if st.session_state.get("_request_rerun"):
    st.session_state._request_rerun = False
    st.rerun()

# =============================
# BUILD RESULTS (Events screen)
# =============================
window_start = now_dt - timedelta(hours=new_hours)

if st.session_state.screen_mode == "Events":
    if st.session_state.view_mode == "New Updates" and not sig_to_created:
        st.warning("New Updates needs the Responses sheet accessible as CSV (Anyone with link = Viewer).")
        st.stop()

def cat_ok(i: int) -> bool:
    if not wanted:
        return True
    cn = normalize_category(cat_s.iloc[i])
    return (
        ("sport" in wanted and cn == "sport")
        or ("culture" in wanted and cn == "culture")
        or ("academics" in wanted and cn == "academics")
    )

# =============================
# EVENTS SCREEN OUTPUT
# =============================
if st.session_state.screen_mode == "Events":
    res = []
    for i in range(len(df)):
        cn = normalize_category(cat_s.iloc[i])

        if force_sport and cn != "sport":
            continue
        if force_grades and cn == "sport":
            continue

        if wanted and not cat_ok(i):
            continue

        info_raw_full = str(info_s.iloc[i]).strip().replace("_", " ")
        row_is_tb = is_test_breakdown_row(act_s.iloc[i], team_s.iloc[i], info_raw_full)

        # View mode: Test Breakdown
        if st.session_state.view_mode == "Test Breakdown" and not row_is_tb:
            continue

        row_act_key = activity_filter_key(cn, act_s.iloc[i])

        # Activity multiselect UNION logic (subjects OR Test Breakdown)
        if st.session_state.act_choice:
            has_tb_pick = ("Test Breakdown" in st.session_state.act_choice)
            subject_match = (row_act_key in st.session_state.act_choice)
            tb_match = (has_tb_pick and row_is_tb)
            if not (subject_match or tb_match):
                continue

        d_raw = str(date_s.iloc[i]).strip()
        d_dt = parse_date_sa(d_raw)

        if d_dt and d_dt.date() < today:
            continue

        if st.session_state.view_mode == "Next 7 Days":
            if not d_dt:
                continue
            if d_dt.date() > (today + timedelta(days=7)):
                continue

        act_disp_for_term = display_activity(cn, act_s.iloc[i])
        term_val = str(term_s.iloc[i]).strip().lower()
        looks_like_term_doc = any(
            k in (act_disp_for_term.lower() + " " + str(team_s.iloc[i]).lower() + " " + info_raw_full.lower())
            for k in ["spelling", "speltoets", "spellys", "assessment schedule", "assessment", "toets", "toetse", "test breakdown"]
        )
        term_flag = ("full term" in term_val) or ("term" in term_val) or (looks_like_term_doc and cn == "academics")

        if st.session_state.view_mode == "Term Documents" and not term_flag:
            continue

        if st.session_state.view_mode == "Assessment Schedule" and not is_assessment_schedule(act_s.iloc[i], team_s.iloc[i]):
            continue

        _, grp_matches = group_for_row(cn, grade_s.iloc[i], team_s.iloc[i])

        math_row = (cn in ["culture", "academics"]) and is_math_activity(act_s.iloc[i])
        selected_has_target_grades = bool(selected_gr_norm & TARGET_GRADES_MATH)

        if cn == "sport" and selected_u_norm:
            if not grp_matches:
                continue
            grp_norm = {norm_token(x) for x in grp_matches}
            if not (selected_u_norm & grp_norm):
                continue

        if cn in ["culture", "academics"] and selected_gr_norm:
            if grp_matches:
                grp_norm = {norm_token(x) for x in grp_matches}
                if not (selected_gr_norm & grp_norm):
                    if not (math_row and selected_has_target_grades):
                        continue
            else:
                if not (math_row and selected_has_target_grades):
                    continue

        sig = row_signature(cat_s.iloc[i], act_s.iloc[i], team_s.iloc[i], date_s.iloc[i], ven_s.iloc[i], prog_s.iloc[i])
        created_dt = sig_to_created.get(sig)
        is_recent = bool(created_dt and (window_start <= created_dt <= now_dt))

        if st.session_state.view_mode == "New Updates" and not is_recent:
            continue

        title = build_title(cn, act_s.iloc[i], team_s.iloc[i], grade_s.iloc[i])

        if st.session_state.search_text:
            needle = st.session_state.search_text.lower().replace(" ", "")
            hay = title.lower().replace(" ", "")
            if needle not in hay:
                continue

        sort_dt = d_dt if d_dt else datetime(2099, 1, 1)
        res.append({"i": i, "dt": sort_dt, "title": title.lower(), "new": is_recent, "created_dt": created_dt})

    res_sorted = sorted(res, key=lambda x: (x["dt"], x["title"]))

    st.markdown("## 📅 Events")
    pin = "&#128205;"

    if not res_sorted:
        st.warning("No items match your filters. Try FILTER → Clear all filters.")
    else:
        for item in res_sorted:
            i = item["i"]
            cn = normalize_category(cat_s.iloc[i])
            afr = is_afrikaans_subject(act_s.iloc[i])

            title = build_title(cn, act_s.iloc[i], team_s.iloc[i], grade_s.iloc[i])
            d_raw = str(date_s.iloc[i]).strip()
            date_line = format_date_long_sa(d_raw) if d_raw else ""

            _, grp_matches = group_for_row(cn, grade_s.iloc[i], team_s.iloc[i])

            ven_norm = normalize_venue(str(ven_s.iloc[i]).strip())

            prog_links = extract_urls(prog_s.iloc[i])
            team_links = extract_urls(teamlnk_s.iloc[i])
            confirm_links = extract_urls(conf_s.iloc[i])

            info_raw_full = str(info_s.iloc[i]).strip().replace("_", " ")
            info_text, info_links = split_info_text_and_links(info_raw_full)

            row_is_tb = is_test_breakdown_row(act_s.iloc[i], team_s.iloc[i], info_raw_full)
            assess = is_assessment_schedule(act_s.iloc[i], team_s.iloc[i])

            buttons = []
            notes_parts = []

            # ✅ Contact person: show ONLY "Contact person" as the clickable mailto link
            sig = row_signature(cat_s.iloc[i], act_s.iloc[i], team_s.iloc[i], date_s.iloc[i], ven_s.iloc[i], prog_s.iloc[i])
            contact_email = (sig_to_email.get(sig, "") or "").strip()
            contact_line = ""
            if contact_email and "@" in contact_email:
                contact_line = (
                    "<div class='meta'>"
                    f"<a href='mailto:{safe_txt(contact_email)}' style='color:#008080;font-weight:900;text-decoration:none;'>"
                    "Contact person</a></div>"
                )

            # ---------------- BUTTONS ----------------
            if cn == "academics":
                # ✅ Test Breakdown: ONLY show English + Afrikaans (from Information, fallback Programme)
                if row_is_tb:
                    src_links = info_links if len(info_links) >= 1 else prog_links
                    if len(src_links) >= 1 and is_http(src_links[0]):
                        buttons.append(("English", src_links[0]))
                    if len(src_links) >= 2 and is_http(src_links[1]):
                        buttons.append(("Afrikaans", src_links[1]))
                    # no other buttons for TB rows

                else:
                    # Assessment Schedule: Programme links -> English/Afrikaans
                    if assess and len(prog_links) >= 1:
                        if is_http(prog_links[0]):
                            buttons.append(("English", prog_links[0]))
                        if len(prog_links) >= 2 and is_http(prog_links[1]):
                            buttons.append(("Afrikaans", prog_links[1]))
                    else:
                        base_docs = "Dokumente" if afr else "Documents"
                        for idx, lk in enumerate(prog_links, start=1):
                            if is_http(lk):
                                buttons.append((base_docs if idx == 1 else f"{base_docs} {idx}", lk))

                    base_info = "Inligting" if afr else "Information"
                    for idx, lk in enumerate(info_links, start=1):
                        if is_http(lk):
                            buttons.append((base_info if idx == 1 else f"{base_info} {idx}", lk))

            else:
                for idx, lk in enumerate(prog_links, start=1):
                    if is_http(lk):
                        buttons.append(("Programme" if idx == 1 else f"Programme {idx}", lk))

                for idx, lk in enumerate(team_links, start=1):
                    if is_http(lk):
                        buttons.append(("Team" if idx == 1 else f"Team {idx}", lk))

                # If TB appears outside academics, enforce English/Afrikaans only
                if row_is_tb:
                    src_links = info_links if len(info_links) >= 1 else prog_links
                    if len(src_links) >= 1 and is_http(src_links[0]):
                        buttons.append(("English", src_links[0]))
                    if len(src_links) >= 2 and is_http(src_links[1]):
                        buttons.append(("Afrikaans", src_links[1]))
                else:
                    for idx, lk in enumerate(info_links, start=1):
                        if is_http(lk):
                            buttons.append(("Information" if idx == 1 else f"Information {idx}", lk))

                for idx, lk in enumerate(confirm_links, start=1):
                    if is_http(lk) and ("forms.gle" in lk.lower() or "docs.google.com/forms" in lk.lower()):
                        buttons.append(("Confirm" if idx == 1 else f"Confirm {idx}", lk))

            # Venue line (campus -> facilities map)
            venue_line = ""
            if ven_norm == "SEE_PROGRAMME":
                notes_parts.append("<b>Venue:</b><br>See programme")
            elif ven_norm:
                venue_href = FACILITIES_MAP_URL if is_midstream_campus_venue(ven_norm) else \
                    f"https://www.google.com/maps/search/?api=1&query={ven_norm.replace(' ', '+')}"
                venue_line = (
                    f"<div class='meta'>{pin} "
                    f"<a href='{venue_href}' target='_blank' style='color:#008080;font-weight:900;text-decoration:none;'>"
                    f"{safe_txt(ven_norm).upper()}</a></div>"
                )

            # Notes text only (links removed already)
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
                if created_dt and (now_dt - created_dt) > timedelta(minutes=BADGE_ANIMATE_MINUTES):
                    dot = "<span style='width:8px;height:8px;border-radius:999px;background:#B00000;display:inline-block;opacity:.9;'></span>"
                ribbon = f"<div class='ribbon'>{dot}NEW UPDATE</div>"

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
  {contact_line}
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
