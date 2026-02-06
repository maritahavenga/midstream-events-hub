# -*- coding: utf-8 -*-
# =============================
# LMCP HUB (Feb 2026)
# =============================
# Views:
#   - All
#   - Next 7 Days
#   - Term Documents
#   - Assessment Schedule
#   - New Updates
#
# Sorting:
#   - ALWAYS by Due Date then alphabetical (no "term items pinned at top")
#
# Links:
#   - Programme/Document Link supports multiple URLs
#   - Team supports multiple URLs -> Team, Team 2, ...
#   - Confirm supports multiple URLs -> Confirm, Confirm 2, ...
#   - Information supports multiple URLs inside text -> Information, Information 2, ...
#
# Assessment Schedule special:
#   - If Programme/Document Link has 2 URLs -> buttons are English (1) and Afrikaans (2)
#
# Quick Grade preset (clean dropdown on Events screen):
#   - Defaults to "Quick select..."
#   - Selecting a grade prefills BOTH Grade + Sport Age Group
#   - Choosing "Switch off" means stop using the shortcut (does NOT switch the app off)
# =============================

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

TZ = pytz.timezone("Africa/Johannesburg")
now_dt = datetime.now(TZ)
today = now_dt.date()

VIEW_OPTIONS = ["All", "Next 7 Days", "Term Documents", "Assessment Schedule", "New Updates"]
NEW_UPDATES_DEFAULT_HOURS = 72
BADGE_ANIMATE_MINUTES = 10

# =============================
# QUICK GRADE PRESET (clean dropdown)
# =============================
QUICK_GRADE_PLACEHOLDER = "Quick select…"
QUICK_GRADE_OFF = "Switch off"
QUICK_GRADE_OPTIONS = [QUICK_GRADE_PLACEHOLDER, "Gr 1-3", "Gr 4", "Gr 5", "Gr 6", "Gr 7", QUICK_GRADE_OFF]

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

ss_init("screen_mode", "Events")          # Events | Filter
ss_init("view_mode", "All")               # default All
ss_init("cat_choice", [])
ss_init("act_choice", [])
ss_init("u_choice", [])
ss_init("gr_choice", [])
ss_init("search_text", "")

# Quick preset state
ss_init("quick_grade", QUICK_GRADE_PLACEHOLDER)
ss_init("_qg_applied", QUICK_GRADE_PLACEHOLDER)

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
        st.session_state.quick_grade = qg
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
.smallTopRow div[data-baseweb="select"]{max-width:260px;}
.smallTopHelp{font-size:.85rem;color:#64748b;margin-top:-8px;}
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

def extract_urls(v: str):
    raw = str(v or "").strip()
    if not raw:
        return []
    urls = [u.strip() for u in URL_RE.findall(raw) if u.strip()]
    seen = set()
    out = []
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

def activity_filter_key(cat_norm: str, activity_raw: str) -> str:
    return sport_base_activity(activity_raw) if cat_norm == "sport" else display_activity(cat_norm, activity_raw)

# =============================
# DATE PARSING (Due dates)
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

    if cat_norm == "sport" and not team_clean:
        grp_disp, _ = group_for_row("sport", grade_val, team_val)
        return f"{act_txt} ({grp_disp})".strip() if grp_disp else act_txt

    return re.sub(r"\s{2,}", " ", f"{act_txt} {team_clean}".strip())

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
    st.error("No data loaded from the sheet.")
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
# Matching Upcoming <-> Responses for New Updates
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
if not sub_df.empty and "Timestamp" in sub_df.columns:
    ts_col = "Timestamp"

    def sub_col(name):
        return sub_df[name].astype(str) if name in sub_df.columns else pd.Series([""] * len(sub_df), dtype=str)

    sub_ts   = sub_df[ts_col].astype(str)
    sub_cat  = sub_col(COL_CATEGORY)
    sub_act  = sub_col(COL_ACTIVITY)
    sub_team = sub_col(COL_TEAM)
    sub_date = sub_col(COL_DATE)
    sub_ven  = sub_col(COL_VENUE)
    sub_prog = sub_col(COL_PROGRAMME)

    for j in range(len(sub_df)):
        created_dt = parse_form_timestamp(sub_ts.iloc[j])
        if not created_dt:
            continue
        sig = row_signature(sub_cat.iloc[j], sub_act.iloc[j], sub_team.iloc[j],
                            sub_date.iloc[j], sub_ven.iloc[j], sub_prog.iloc[j])
        prev = sig_to_created.get(sig)
        if (prev is None) or (created_dt > prev):
            sig_to_created[sig] = created_dt

# =============================
# TOP BAR: Quick select dropdown + Filter button
# =============================
top_left, top_mid, top_right = st.columns([2.2, 1.0, 1.2])

with top_left:
    if st.session_state.screen_mode == "Events":
        st.markdown("<div class='smallTopRow'>", unsafe_allow_html=True)
        st.selectbox(
            "Quick select",
            QUICK_GRADE_OPTIONS,
            index=QUICK_GRADE_OPTIONS.index(st.session_state.quick_grade) if st.session_state.quick_grade in QUICK_GRADE_OPTIONS else 0,
            key="quick_grade",
            label_visibility="collapsed",
        )
        st.markdown(
            "<div class='smallTopHelp'><b>Quick select:</b> choose a grade shortcut. "
            "<b>Switch off</b> = stop using the shortcut (does not switch the app off).</div>",
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

with top_mid:
    # Apply preset ONLY when changed (Events screen)
    if st.session_state.screen_mode == "Events":
        qg = st.session_state.quick_grade
        if qg in QUICK_GRADE_OPTIONS and qg != st.session_state._qg_applied:
            if qg in [QUICK_GRADE_PLACEHOLDER, QUICK_GRADE_OFF]:
                st.session_state._qg_applied = qg
            else:
                if qg == "Gr 1-3":
                    st.session_state.gr_choice = ["Gr 1", "Gr 2", "Gr 3"]
                else:
                    st.session_state.gr_choice = [qg]
                st.session_state.u_choice = GRADE_TO_U_MAP.get(qg, [])
                st.session_state._qg_applied = qg

                payload_now = {
                    "view": st.session_state.view_mode,
                    "cat": st.session_state.cat_choice,
                    "act": st.session_state.act_choice,
                    "u": st.session_state.u_choice,
                    "gr": st.session_state.gr_choice,
                    "q": st.session_state.search_text,
                    "qg": st.session_state.quick_grade,
                }
                qp_set_from_state(payload_now)
                st.rerun()

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
# VIEW
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
# FILTERS + EVENTS OUTPUT
# (unchanged from previous full version except quick select labels)
# =============================
# ---- Everything below stays the same as the previous full script you have. ----
# If you want me to paste the rest as well (it is long), say:
# "paste the full script including the events loop" and I will paste it in one block.
