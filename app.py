# -*- coding: utf-8 -*-
import streamlit as st
import streamlit.components.v1 as components
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

TZ = pytz.timezone("Africa/Johannesburg")
now_dt = datetime.now(TZ)
today = now_dt.date()

VIEW_OPTIONS = ["Upcoming", "Next 7 Days", "Term Documents", "New Updates"]
NEW_UPDATES_DEFAULT_HOURS = 72
BADGE_ANIMATE_MINUTES = 10

# =============================
# ✅ iOS BOOKMARK FIX
# - Restore only if URL has no useful params.
# - Save ONLY when user clicks "Save filters".
# =============================
LS_KEY = "lmcp_filters_v2"

components.html(
    f"""
<script>
(function() {{
  const KEY = "{LS_KEY}";
  const p = new URLSearchParams(window.location.search || "");
  const hasUseful = ["view","cat","act","u","gr","q"].some(k => p.has(k));
  if (!hasUseful) {{
    const saved = localStorage.getItem(KEY);
    if (saved && typeof saved === "string" && saved.trim().length > 0) {{
      const url = new URL(window.location.href);
      url.search = saved.startsWith("?") ? saved : ("?" + saved);
      window.location.replace(url.toString());
    }}
  }}
}})();
</script>
""",
    height=0,
)

def js_save_localstorage(querystring: str):
    qs = (querystring or "").replace("`", "").replace("\\", "")
    components.html(
        f"""
<script>
(function(){{
  localStorage.setItem("{LS_KEY}", `{qs}`);
}})();
</script>
""",
        height=0,
    )

def js_clear_localstorage():
    components.html(
        f"""
<script>
(function(){{
  localStorage.removeItem("{LS_KEY}");
}})();
</script>
""",
        height=0,
    )

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

def payload_to_qs(payload: dict) -> str:
    parts = []
    for k, v in payload.items():
        if isinstance(v, list):
            if v:
                parts.append(f"{k}=" + requests.utils.quote(",".join(v)))
        else:
            sv = str(v).strip()
            if sv:
                parts.append(f"{k}=" + requests.utils.quote(sv))
    return "&".join(parts)

# =============================
# SESSION DEFAULTS
# =============================
def ss_init(key, default):
    if key not in st.session_state:
        st.session_state[key] = default

ss_init("screen_mode", "Events")  # Events | Filter
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
button[data-testid="collapsedControl"]::after{
  content:"  Filter here";
  font-weight: 1000;
  font-size: 1.05rem;
  color: var(--teal);
  margin-left: 8px;
}
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

def norm_gender_words(text: str) -> str:
    s = str(text or "").strip().replace("_", " ")
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"\bmeisies\b", "Girls", s, flags=re.I)
    s = re.sub(r"\bseuns\b", "Boys", s, flags=re.I)
    s = re.sub(r"\bgirls\b", "Girls", s, flags=re.I)
    s = re.sub(r"\bboys\b", "Boys", s, flags=re.I)
    return re.sub(r"\s+", " ", s).strip()

# =============================
# ACTIVITY: display vs filter
# =============================
def display_activity(cat_norm: str, activity_raw: str, grade_raw: str = "") -> str:
    """What shows in the CARD title (and filter for non-sport)."""
    s = str(activity_raw or "").strip()

    if cat_norm == "sport":
        return s

    sl = re.sub(r"\s+", " ", s.lower().strip())
    if sl in ["ht", "afrikaans ht"] or "hooftaal" in sl:
        return "Afrikaans Hooftaal"
    if sl in ["eat", "afrikaans eat"] or "eerste addisionele" in sl:
        return "Afrikaans Eerste Addisionele Taal"

    # ✅ HARD CODE: Maths / Math / Wiskunde => Mathematics (Gr 4–7)
    gtxt = str(grade_raw or "").lower()
    is_gr_4_7 = any(x in gtxt.replace(" ", "") for x in ["gr4", "gr5", "gr6", "gr7", "4-7", "4–7"])
    if is_gr_4_7:
        if ("wiskunde" in sl) or ("mathematics" in sl) or (sl == "math") or ("maths" in sl):
            return "Mathematics"

    # (safe fallback: still normalize globally)
    if "wiskunde" in sl or "mathematics" in sl or sl == "math" or "maths" in sl:
        return "Mathematics"

    return s.title()

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

def activity_filter_key(cat_norm: str, activity_raw: str, grade_raw: str = "") -> str:
    return sport_base_activity(activity_raw) if cat_norm == "sport" else display_activity(cat_norm, activity_raw, grade_raw)

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
        return [f"U{x}" for x in seq]
