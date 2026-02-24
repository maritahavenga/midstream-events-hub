# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import requests, io, re, pytz, hashlib
import html
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

# ✅ pending actions (run at top, NOT inside callbacks)
ss_init("_pending_clear_all", False)
ss_init("_pending_save_filters", False)

# =============================
# INITIAL LOAD FROM QUERY PARAMS (ONLY ON FIRST LOAD)
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
# APPLY PENDING ACTIONS (MUST BE BEFORE WIDGETS RENDER)
# =============================
if st.session_state.get("_pending_clear_all", False):
    st.session_state["_pending_clear_all"] = False

    st.session_state["cat_choice"] = []
    st.session_state["act_choice"] = []
    st.session_state["u_choice"] = []
    st.session_state["gr_choice"] = []
    st.session_state["search_text"] = ""
    st.session_state["quick_grade_ui"] = QUICK_GRADE_PLACEHOLDER
    st.session_state["_qg_applied"] = QUICK_GRADE_PLACEHOLDER

    st.query_params.from_dict({})
    st.session_state["screen_mode"] = "Events"

if st.session_state.get("_pending_save_filters", False):
    st.session_state["_pending_save_filters"] = False

    payload_now = {
        "view": st.session_state.get("view_mode", "All"),
        "cat": st.session_state.get("cat_choice", []),
        "act": st.session_state.get("act_choice", []),
        "u": st.session_state.get("u_choice", []),
        "gr": st.session_state.get("gr_choice", []),
        "q": st.session_state.get("search_text", ""),
        "qg": st.session_state.get("quick_grade_ui", QUICK_GRADE_PLACEHOLDER),
    }
    qp_set_from_state(payload_now)
    st.session_state["screen_mode"] = "Events"

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
  white-space:normal;
}
.btnRow{display:flex;gap:10px;flex-wrap:wrap;margin-top:12px;}
.btn{
  display:inline-block;background:var(--teal);color:white !important;
  padding:9px 12px;border-radius:12px;font-weight:900;
  text-decoration:none;font-size:.90rem;
}
.btn:hover{opacity:.92;}
/* ✅ NEW badge: small + compact */
.ribbon{
  position:absolute; right:12px; top:12px;
  background:#111827;
  color:#ffffff;
  font-weight:1000;
  font-size:.70rem;
  padding:4px 8px;
  border-radius:999px;
  border:1px solid rgba(255,255,255,0.18);
  display:flex;align-items:center;gap:6px;
  box-shadow:0 8px 16px rgba(0,0,0,0.10);
  z-index:5;
}
.rDot{width:7px;height:7px;border-radius:999px;background:#22c55e;animation:pulse 1.0s infinite;}
@keyframes pulse{0%{transform:scale(1);opacity:.35;}50%{transform:scale(1.55);opacity:1;}100%{transform:scale(1);opacity:.35;}}
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
URL_RE = re.compile(r"(https?://[^\s<>\"]+)", re.IGNORECASE)

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
    raw_unescaped = html.unescape(raw)
    found = [u.strip() for u in URL_RE.findall(raw_unescaped) if u.strip()]

    def clean(u: str) -> str:
        u = u.strip()
        u = u.rstrip(".,;:!?) ]}>\"'”’")
        if u.endswith(")") and u.count("(") < u.count(")"):
            u = u[:-1]
        return u.strip()

    seen, out = set(), []
    for u in found:
        u2 = clean(u)
        if u2 and u2 not in seen:
            out.append(u2)
            seen.add(u2)
    return out

def urls_signature_part(v: str) -> str:
    links = extract_urls(v)
    return "|".join(links[:2])

def split_info_text_and_links(info: str):
    raw = str(info or "")
    if not raw.strip():
        return "", []
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    raw_unescaped = html.unescape(raw)
    links = extract_urls(raw_unescaped)

    text_unescaped = raw_unescaped
    for u in links:
        text_unescaped = re.sub(re.escape(u), "", text_unescaped)

    lines = []
    for line in text_unescaped.split("\n"):
        ln = line.replace("\t", " ")
        ln = re.sub(r"[ ]{2,}", " ", ln).strip(" -|")
        if ln.strip():
            lines.append(ln)

    return "\n".join(lines).strip(), links

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

def is_test_breakdown_row(activity_raw: str, team_raw: str, info_raw_full: str) -> bool:
    a = str(activity_raw or "").lower()
    t = str(team_raw or "").lower()
    inf = str(info_raw_full or "").lower()
    return ("test breakdown" in a) or ("test breakdown" in t) or ("test breakdown" in inf)

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
# DATE PARSING (supports 27-28/02/2026 and 27–28/02/2026)
# =============================
def parse_date_sa_single(s: str):
    raw = str(s or "").strip()
    if not raw or raw.lower() in ["nan", "none"]:
        return None
    cleaned = re.sub(r"\s+", " ", raw.replace(".", "/")).strip()
    dt = pd.to_datetime(cleaned, dayfirst=True, errors="coerce")
    if not pd.isnull(dt):
        return dt.to_pydatetime()
    dt2 = pd.to_datetime(cleaned, dayfirst=False, errors="coerce")
    if not pd.isnull(dt2):
        return dt2.to_pydatetime()
    return None

def parse_date_range_sa(s: str):
    raw = str(s or "").strip()
    if not raw or raw.lower() in ["nan", "none"]:
        return (None, None)

    txt = raw.replace("—", "–")
    txt = re.sub(r"\s+", " ", txt).strip()

    m = re.search(r"(\d{1,2})\s*[-–—]\s*(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{4})", txt)
    if m:
        d1 = int(m.group(1)); d2 = int(m.group(2))
        mm = int(m.group(3)); yy = int(m.group(4))
        lo, hi = sorted([d1, d2])
        try:
            return (datetime(yy, mm, lo), datetime(yy, mm, hi))
        except Exception:
            pass

    m2 = re.search(
        r"(\d{1,2}[\/\.\-]\d{1,2}[\/\.\-]\d{2,4})\s*(?:\s-\s|–|—|\bto\b|\buntil\b|\btill\b|\btot\b)\s*(\d{1,2}[\/\.\-]\d{1,2}[\/\.\-]\d{2,4})",
        txt,
        flags=re.I
    )
    if m2:
        a = parse_date_sa_single(m2.group(1))
        b = parse_date_sa_single(m2.group(2))
        if a and b:
            if b < a:
                a, b = b, a
            return (a, b)

    m3 = re.search(r"(\d{1,2}[\/\.\-]\d{1,2}[\/\.\-]\d{2,4})", txt)
    if m3:
        one = parse_date_sa_single(m3.group(1))
        return (one, one) if one else (None, None)

    one = parse_date_sa_single(txt)
    return (one, one) if one else (None, None)

def format_date_long_sa(s) -> str:
    start_dt, end_dt = parse_date_range_sa(s)
    if not start_dt:
        return str(s or "").strip()

    if end_dt and end_dt.date() != start_dt.date():
        if start_dt.year == end_dt.year and start_dt.month == end_dt.month:
            return f"{start_dt.day}–{end_dt.day} {start_dt.strftime('%B %Y')}"
        return f"{start_dt.day} {start_dt.strftime('%B %Y')} – {end_dt.day} {end_dt.strftime('%B %Y')}"

    return f"{start_dt.day} {start_dt.strftime('%B %Y')}"

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
# VENUE (Bondev/Meerkat + Indoor/Outdoor Pool + Hub + Facility map rule)
# =============================
VENUE_MAP = {
    "musiekkamer": "Music Room",
    "musiek kamer": "Music Room",
    "saal": "Hall",
    "ouditorium": "Auditorium",
    "veld": "Field",
    "swembad": "Swimming Pool",
    "tennis bane": "Tennis Courts",
    "netbal bane": "Netball Courts",
    "cricket oval": "Cricket Oval",
    "bondev field": "Bondev Field",
    "bondevveld": "Bondev Field",
    "meerkat field": "Meerkat Field",
    "meerkatveld": "Meerkat Field",
    "indoor pool": "Indoor Pool",
    "binne swembad": "Indoor Pool",
    "outdoor pool": "Outdoor Pool",
    "buite swembad": "Outdoor Pool",
    "the hub": "The Hub",
    "lmcp hub": "The Hub",
}

def normalize_venue(v: str) -> str:
    s = re.sub(r"\s+", " ", str(v or "").strip().replace("_", " "))
    sl = s.lower()

    if "see programme" in sl or "see program" in sl or "sien program" in sl or "sien programme" in sl:
        return "SEE_PROGRAMME"

    if "hub" in sl:
        return "The Hub"

    if "astro" in sl:
        if "bondev" in sl:
            return "Bondev Astro"
        if "meerkat" in sl:
            return "Meerkat Astro"
        return "Astro"

    if "bondev field" in sl or "bondevveld" in sl:
        return "Bondev Field"
    if "meerkat field" in sl or "meerkatveld" in sl:
        return "Meerkat Field"

    if "indoor pool" in sl or "binne swembad" in sl:
        return "Indoor Pool"
    if "outdoor pool" in sl or "buite swembad" in sl:
        return "Outdoor Pool"

    for k, vv in VENUE_MAP.items():
        if k in sl:
            return vv

    return s

CAMPUS_VENUE_KEYWORDS = [
    "midstream", "midstream college", "lmcp", "primary", "college",
    "auditorium", "hall", "music room", "field", "bondev", "meerkat",
    "pool", "swimming", "indoor", "outdoor",
    "tennis", "netball", "cricket", "oval",
    "hub", "astro",
]

def is_midstream_campus_venue(ven_norm: str) -> bool:
    v = str(ven_norm or "").strip().lower()
    if not v:
        return False
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
            g_disp = f"{g_list[0]}–{g_list[-1]}" if len(g_list) >= 2 else g_list[0]
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
# COLUMN RESOLVER (fixes header mismatches = dates blank)
# =============================
def pick_col(df_: pd.DataFrame, candidates):
    cols = list(df_.columns)
    norm = {re.sub(r"\s+", " ", c.strip().lower()): c for c in cols}

    for cand in candidates:
        k = re.sub(r"\s+", " ", str(cand).strip().lower())
        if k in norm:
            return norm[k]

    for cand in candidates:
        k = re.sub(r"\s+", " ", str(cand).strip().lower())
        for nk, orig in norm.items():
            if k in nk:
                return orig
    return None

COL_CATEGORY  = pick_col(df, ["Category"])
COL_ACTIVITY  = pick_col(df, ["Activity/Subject Name", "Activity", "Subject"])
COL_TEAM      = pick_col(df, ["Team / Assessment", "Team/Assessment", "Team"])
COL_DATE      = pick_col(df, ["Date / Due Date", "Date/Due Date", "Date", "Due Date"])
COL_VENUE     = pick_col(df, ["Venue"])
COL_PROGRAMME = pick_col(df, ["Programme / Document Link", "Programme", "Programme Link", "Document Link"])
COL_TEAMS_LNK = pick_col(df, ["Team", "Team Link"])
COL_CONFIRM   = pick_col(df, ["Confirm", "Confirmation"])
COL_INFO      = pick_col(df, ["Information", "Info", "Notes", "Note"])
COL_GRADE     = pick_col(df, ["Age Group (9,10) / Grade (1,2,3)", "Age Group / Grade", "Age Group", "Grade"])
COL_TERM      = pick_col(df, ["Display Duration", "Term", "Duration"])

def s(colname):
    if colname and colname in df.columns:
        return df[colname].astype(str).fillna("")
    return pd.Series([""] * len(df), dtype=str)

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
    sub_cat   = sub_col("Category")
    sub_act   = sub_col("Activity/Subject Name")
    sub_team  = sub_col("Team / Assessment")
    sub_date  = sub_col("Date / Due Date")
    sub_ven   = sub_col("Venue")
    sub_prog  = sub_col("Programme / Document Link")
    sub_email = sub_col("Email address")

    for j in range(len(sub_df)):
        created_dt = parse_form_timestamp(sub_ts.iloc[j])
        if not created_dt:
            continue
        sig = row_signature(sub_cat.iloc[j], sub_act.iloc[j], sub_team.iloc[j],
                            sub_date.iloc[j], sub_ven.iloc[j], sub_prog.iloc[j])
        prev = sig_to_created.get(sig)
        if (prev is None) or (created_dt > prev):
            sig_to_created[sig] = created_dt
            sig_to_email[sig] = str(sub_email.iloc[j] or "").strip()

# =============================
# TOP BAR (Quick Select + Filter)
# =============================
if st.session_state.get("_pending_qg_reset", False):
    st.session_state["quick_grade_ui"] = QUICK_GRADE_PLACEHOLDER
    st.session_state["_qg_applied"] = QUICK_GRADE_PLACEHOLDER
    st.session_state["_pending_qg_reset"] = False

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
                st.session_state["_pending_clear_all"] = True
                st.session_state["_qg_applied"] = QUICK_GRADE_CLEAR
            elif qg == QUICK_GRADE_PLACEHOLDER:
                st.session_state["_qg_applied"] = qg
            else:
                if qg == "Gr 1-3":
                    st.session_state["gr_choice"] = ["Gr 1", "Gr 2", "Gr 3"]
                else:
                    st.session_state["gr_choice"] = [qg]
                st.session_state["u_choice"] = GRADE_TO_U_MAP.get(qg, [])
                st.session_state["_qg_applied"] = qg

with top_right:
    if st.session_state.screen_mode == "Events":
        if st.button("🔎 FILTER", key="go_filter_top", type="primary", use_container_width=True):
            st.session_state["screen_mode"] = "Filter"
            st.rerun()
    else:
        if st.button("⬅ Back to Events", key="back_events_top", type="secondary", use_container_width=True):
            st.session_state["screen_mode"] = "Events"
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
# FILTER SCREEN (buttons set pending flags)
# =============================
def click_save_filters():
    st.session_state["_pending_save_filters"] = True

def click_clear_filters():
    st.session_state["_pending_clear_all"] = True

def click_back_no_save():
    st.session_state["screen_mode"] = "Events"

wanted = set()
selected_u_norm = set()
selected_gr_norm = set()
force_sport = False
force_grades = False
new_hours = NEW_UPDATES_DEFAULT_HOURS

def render_filters_main():
    global wanted, selected_u_norm, selected_gr_norm, force_sport, force_grades, new_hours

    st.markdown("## 🔎 Filters")

    a1, a2, a3 = st.columns([1, 1, 1])
    with a1:
        st.button("✅ Save filters & Back to Events", key="save_back_top", type="primary", use_container_width=True, on_click=click_save_filters)
    with a2:
        st.button("🧹 Clear all filters", key="clear_all_top", type="secondary", use_container_width=True, on_click=click_clear_filters)
    with a3:
        st.button("⬅ Back (no changes)", key="back_no_save_top", type="secondary", use_container_width=True, on_click=click_back_no_save)

    st.markdown("---")

    st.multiselect("Category", ["Sport", "Culture", "Academics"], default=st.session_state.get("cat_choice", []), key="cat_choice")

    st.text_input("Whole school search", value=st.session_state.get("search_text", ""), placeholder="Type to filter...", key="search_text")

    wanted = {c.lower() for c in st.session_state.get("cat_choice", [])} if st.session_state.get("cat_choice") else set()

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
        act_opts = sorted(set(act_opts) | {"Test Breakdown"})

    act_default = [a for a in st.session_state.get("act_choice", []) if a in act_opts]
    st.multiselect("Activity/Subject", act_opts, default=act_default, key="act_choice")

    u_opts = [f"U{i}" for i in range(7, 14)]
    if (not wanted or "sport" in wanted):
        u_default = [u for u in st.session_state.get("u_choice", []) if u in u_opts]
        selected_u = st.multiselect("Age Groups (Sport)", u_opts, default=u_default, key="u_choice")
    else:
        selected_u = []

    grade_options = [f"Gr {i}" for i in range(1, 8)]
    if (not wanted or "culture" in wanted or "academics" in wanted):
        g_default = [g for g in st.session_state.get("gr_choice", []) if g in grade_options]
        selected_gr = st.multiselect("Grades (Culture/Academics)", grade_options, default=g_default, key="gr_choice")
    else:
        selected_gr = []

    selected_u_norm = {norm_token(x) for x in set(selected_u)}
    selected_gr_norm = {norm_token(x) for x in set(selected_gr)}

    force_sport  = (not wanted) and bool(selected_u_norm) and not bool(selected_gr_norm)
    force_grades = (not wanted) and bool(selected_gr_norm) and not bool(selected_u_norm)

    if st.session_state.get("view_mode") == "New Updates":
        new_hours = st.slider("New Updates window (hours)", 1, 336, NEW_UPDATES_DEFAULT_HOURS)
    else:
        new_hours = NEW_UPDATES_DEFAULT_HOURS

    st.markdown("---")
    b1, b2, b3 = st.columns([1, 1, 1])
    with b1:
        st.button("✅ Save filters & Back to Events", key="save_back_bottom", type="primary", use_container_width=True, on_click=click_save_filters)
    with b2:
        st.button("🧹 Clear all filters", key="clear_all_bottom", type="secondary", use_container_width=True, on_click=click_clear_filters)
    with b3:
        st.button("⬅ Back (no changes)", key="back_no_save_bottom", type="secondary", use_container_width=True, on_click=click_back_no_save)

if st.session_state.screen_mode == "Filter":
    render_filters_main()
    st.stop()

# =============================
# EVENTS SCREEN FILTER STATE (stickiness comes from session_state)
# =============================
wanted = {c.lower() for c in st.session_state.get("cat_choice", [])} if st.session_state.get("cat_choice") else set()
selected_u_norm = {norm_token(x) for x in set(st.session_state.get("u_choice", []))}
grade_options = [f"Gr {i}" for i in range(1, 8)]
selected_gr_norm = {norm_token(x) for x in set([g for g in st.session_state.get("gr_choice", []) if g in grade_options])}

force_sport  = (not wanted) and bool(selected_u_norm) and not bool(selected_gr_norm)
force_grades = (not wanted) and bool(selected_gr_norm) and not bool(selected_u_norm)
new_hours = NEW_UPDATES_DEFAULT_HOURS

# =============================
# BUILD RESULTS (Events screen)
# =============================
window_start = now_dt - timedelta(hours=new_hours)

if st.session_state.get("view_mode") == "New Updates" and not sig_to_created:
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

    if st.session_state.get("view_mode") == "Test Breakdown" and not row_is_tb:
        continue

    row_act_key = activity_filter_key(cn, act_s.iloc[i])

    if st.session_state.get("act_choice"):
        has_tb_pick = ("Test Breakdown" in st.session_state.act_choice)
        subject_match = (row_act_key in st.session_state.act_choice)
        tb_match = (has_tb_pick and row_is_tb)
        if not (subject_match or tb_match):
            continue

    d_raw = str(date_s.iloc[i]).strip()
    d_start, d_end = parse_date_range_sa(d_raw)

    if d_end and d_end.date() < today:
        continue

    if st.session_state.get("view_mode") == "Next 7 Days":
        if not d_start:
            continue
        window_end = today + timedelta(days=7)
        if (d_end or d_start).date() < today or d_start.date() > window_end:
            continue

    _, grp_matches = group_for_row(cn, grade_s.iloc[i], team_s.iloc[i])

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
                continue

    sig = hashlib.sha256("||".join([
        normalize_category(cat_s.iloc[i]),
        norm_token(act_s.iloc[i]),
        norm_token(team_s.iloc[i]),
        norm_token(date_s.iloc[i]),
        norm_token(ven_s.iloc[i]),
        norm_token(urls_signature_part(prog_s.iloc[i])),
    ]).encode("utf-8")).hexdigest()

    created_dt = sig_to_created.get(sig)
    is_recent = bool(created_dt and (window_start <= created_dt <= now_dt))

    if st.session_state.get("view_mode") == "New Updates" and not is_recent:
        continue

    title = build_title(cn, act_s.iloc[i], team_s.iloc[i], grade_s.iloc[i])

    if st.session_state.get("search_text"):
        needle = st.session_state.search_text.lower().replace(" ", "")
        hay = title.lower().replace(" ", "")
        if needle not in hay:
            continue

    sort_dt = d_start if d_start else datetime(2099, 1, 1)
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

        sig2 = row_signature(cat_s.iloc[i], act_s.iloc[i], team_s.iloc[i], date_s.iloc[i], ven_s.iloc[i], prog_s.iloc[i])
        contact_email = (sig_to_email.get(sig2, "") or "").strip()
        contact_line = ""
        if contact_email and "@" in contact_email:
            mail_label = "Mail Teacher" if cn == "academics" else "Mail Organiser"
            contact_line = (
                "<div class='meta'>"
                f"<a href='mailto:{safe_txt(contact_email)}' style='color:#008080;font-weight:900;text-decoration:none;'>"
                f"{mail_label}</a></div>"
            )

        if cn == "academics":
            if row_is_tb:
                src_links = info_links if len(info_links) >= 1 else prog_links
                if len(src_links) >= 1 and is_http(src_links[0]):
                    buttons.append(("English", src_links[0]))
                if len(src_links) >= 2 and is_http(src_links[1]):
                    buttons.append(("Afrikaans", src_links[1]))
            else:
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

            for idx, lk in enumerate(info_links, start=1):
                if is_http(lk):
                    buttons.append(("Information" if idx == 1 else f"Information {idx}", lk))

            for idx, lk in enumerate(confirm_links, start=1):
                if is_http(lk) and ("forms.gle" in lk.lower() or "docs.google.com/forms" in lk.lower()):
                    buttons.append(("Confirm" if idx == 1 else f"Confirm {idx}", lk))

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

        if info_text:
            notes_parts.append(f"<b>Note:</b><br>{safe_txt(info_text).replace('\\n','<br>')}")

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
                dot = "<span style='width:7px;height:7px;border-radius:999px;background:#22c55e;display:inline-block;opacity:.95;'></span>"
            ribbon = f"<div class='ribbon'>{dot}NEW</div>"

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
