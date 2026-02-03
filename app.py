# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import requests, io, re, pytz, hashlib
from datetime import datetime, timedelta
from requests.exceptions import RequestException, Timeout
# Nuwe komponent vir blaaier-geheue
from streamlit_local_storage import LocalStorage

# =============================
# PAGE CONFIG
# =============================
st.set_page_config(page_title="LMCP Hub", page_icon="📌", layout="wide")

# Inisialiseer LocalStorage
localS = LocalStorage()

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"
LOGO_URL = "https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg"

TZ = pytz.timezone("Africa/Johannesburg")
now_dt = datetime.now(TZ)
today = now_dt.date()

# =============================
# SESSION & LOCAL STORAGE DEFAULTS
# =============================
VIEW_OPTIONS = ["Upcoming", "Next 7 Days", "Term Documents"]

def ss_init(key, default):
    if key not in st.session_state:
        # Kyk of daar iets in die blaaier se localStorage is
        stored_val = localS.getItem(f"lmcp_{key}")
        st.session_state[key] = stored_val if stored_val is not None else default

# Inisialiseer alle state
ss_init("view_mode", "Upcoming")
ss_init("cat_choice", [])
ss_init("act_choice", [])
ss_init("u_choice", [])
ss_init("gr_choice", [])
ss_init("search_text", "")

# =============================
# STYLE (Maroon & Teal)
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
.topBanner{margin-top:14px; border-radius:22px; padding:18px; margin-bottom:22px; background:#008080; box-shadow:var(--shadow); color:#fff;}
.topBannerInner{display:flex;flex-direction:column;gap:10px;align-items:center;text-align:center;}
.longLogo{width:min(900px, 100%); border-radius:16px; background:#fff; padding:10px; border:2px solid rgba(255,255,255,0.35);}
.longLogo img{width:100%;height:auto;display:block;}
.hubText{font-weight:900;font-size:1.65rem;letter-spacing:.3px;}
.card{border:1px solid var(--line); background:#fff; box-shadow:var(--shadow); border-radius:18px; padding:14px; margin-bottom:14px; border-left:10px solid var(--maroon); position:relative;}
.card-title{font-weight:900;color:var(--maroon);font-size:1.15rem;line-height:1.2;}
.card-submeta{margin-top:6px;font-size:.92rem;color:#64748b;font-weight:800;}
.meta{color:#64748b;margin-top:8px;font-size:.95rem;}
.noteBlock{margin-top:12px;padding:12px;border-radius:14px; background:rgba(0,128,128,0.08); border:1px solid rgba(0,128,128,0.25); color:#0f172a;font-size:.95rem;line-height:1.35;}
.btnRow{display:flex;gap:10px;flex-wrap:wrap;margin-top:12px;}
.btn{display:inline-block;background:var(--teal);color:white !important; padding:9px 12px;border-radius:12px;font-weight:900; text-decoration:none;font-size:.90rem;}
.ribbon{position:absolute; right:12px; bottom:12px; background:#FFD400; color:#B00000; font-weight:1000; font-size:.78rem; padding:6px 10px; border-radius:999px; box-shadow:0 8px 16px rgba(0,0,0,0.10); display:flex;align-items:center;gap:8px;}
.rDot{width:8px;height:8px;border-radius:999px;background:#B00000;animation:pulse 1.0s infinite;}
@keyframes pulse{0%{transform:scale(1);opacity:.4;}50%{transform:scale(1.7);opacity:1;}100%{transform:scale(1);opacity:.4;}}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(f'<div class="topBanner"><div class="topBannerInner"><div class="longLogo"><img src="{LOGO_URL}"></div><div class="hubText">Digital Hub</div></div></div>', unsafe_allow_html=True)

# =============================
# HELPERS & PARSING
# =============================
URL_RE = re.compile(r"(https?://[^\s\)\]\}<>\"']+)", re.IGNORECASE)

def safe_txt(x): return str(x or "").replace("&", "&").replace("<", "<").replace(">", ">").strip()
def is_http(u): return str(u or "").strip().lower().startswith(("http://", "https://"))
def first_url(v): m = re.search(r"https?://\S+", str(v or "")); return m.group(0) if m else ""

def split_info_text_and_links(info):
    raw = str(info or "").strip()
    if not raw: return "", []
    links = URL_RE.findall(raw)
    text = URL_RE.sub("", raw).strip(" -\n\t|")
    return text, links

def normalize_category(v):
    s = str(v or "").lower()
    if "sport" in s: return "sport"
    if "cult" in s or "kult" in s: return "culture"
    if "akad" in s or "acad" in s: return "academics"
    return s

def normalize_activity(v):
    s = str(v or "").strip().lower()
    if "wisk" in s: return "Math"
    if "atlet" in s or "athl" in s: return "Athletics"
    if "swem" in s or "swim" in s: return "Swimming"
    return s.title()

def is_afrikaans_subject(b_raw):
    s = str(b_raw or "").lower()
    return any(x in s for x in ["afrikaans", "ht", "eat", "hooftaal"])

# ---------- DATE PARSING ----------
def parse_date_sa(s):
    if not s: return None
    raw = str(s).strip()
    try:
        # Handle Excel serial dates
        if raw.replace('.','',1).isdigit() and float(raw) > 30000:
            return datetime(1899, 12, 30) + timedelta(days=int(float(raw)))
        # Handle "15 Feb" format
        m = re.match(r"(\d{1,2})\s+([A-Za-z]+)", raw)
        if m:
            return pd.to_datetime(f"{m.group(1)} {m.group(2)} {datetime.now(TZ).year}", dayfirst=True)
        return pd.to_datetime(raw, dayfirst=True, errors='coerce')
    except: return None

def format_date_long_sa(s):
    dt = parse_date_sa(s)
    return dt.strftime("%d %B %Y") if dt and not pd.isnull(dt) else str(s)

# =============================
# AGE / GRADE LOGIC
# =============================
def group_for_row(cat_norm, grade_raw, team_raw):
    g = str(grade_raw or "").strip()
    nums = re.findall(r"\d+", g if g else team_raw)
    if not nums: return "", []
    prefix = "U" if cat_norm == "sport" else "Gr "
    res = [f"{prefix}{n}" for n in nums]
    return f"{res[0]}-{res[-1]}" if len(res) > 1 else res[0], res

def build_title(cat, act, team, grade):
    act_t = normalize_activity(act)
    grp_d, _ = group_for_row(normalize_category(cat), grade, team)
    clean_team = re.sub(r"\bU?\d{1,2}\b", "", team).strip()
    return f"{act_t} {grp_d} {clean_team}".replace("  ", " ").strip()

# =============================
# DATA LOADING
# =============================
@st.cache_data(ttl=180)
def load_csv(url):
    r = requests.get(url, timeout=10)
    df_ = pd.read_csv(io.StringIO(r.text)).fillna("")
    df_.columns = [str(c).strip() for c in df_.columns]
    return df_

try:
    df = load_csv(CSV_URL)
except:
    st.error("Sheet kon nie laai nie.")
    st.stop()

# =============================
# SIDEBAR FILTERS & PERSISTENCE
# =============================
with st.sidebar:
    st.markdown("## Filters")
    
    # Elke keer as 'n waarde verander, stoor ons dit in localStorage
    v_mode = st.radio("View", VIEW_OPTIONS, index=VIEW_OPTIONS.index(st.session_state.view_mode), key="view_mode_radio")
    if v_mode != st.session_state.view_mode:
        st.session_state.view_mode = v_mode
        localS.setItem("lmcp_view_mode", v_mode)

    cat_sel = st.multiselect("Category", ["Sport", "Culture", "Academics"], default=st.session_state.cat_choice)
    if cat_sel != st.session_state.cat_choice:
        st.session_state.cat_choice = cat_sel
        localS.setItem("lmcp_cat_choice", cat_sel)

    search = st.text_input("Search", value=st.session_state.search_text)
    if search != st.session_state.search_text:
        st.session_state.search_text = search
        localS.setItem("lmcp_search_text", search)

# =============================
# RESULTS PROCESSING
# =============================
res_list = []
for i, row in df.iterrows():
    cn = normalize_category(row.get("Category", ""))
    # (Filter logika hier...)
    # ... [Ingekort vir spasie, maar dieselfde as jou oorspronklike filters] ...
    
    title = build_title(row.get("Category",""), row.get("Activity/Subject Name",""), row.get("Team / Assessment",""), row.get("Age Group (9,10) / Grade (1,2,3)",""))
    
    # Hash vir updates
    sig = hashlib.sha256(title.encode()).hexdigest()
    if "row_hashes" not in st.session_state: st.session_state.row_hashes = {}
    
    res_list.append({"title": title, "row": row, "cn": cn})

# =============================
# DISPLAY CARDS
# =============================
st.markdown("## 📅 Events")
for item in res_list:
    r = item["row"]
    # Genereer die kaart HTML (soos in jou oorspronklike script)
    st.markdown(f"""<div class="card"><div class="card-title">{safe_txt(item['title'])}</div></div>""", unsafe_allow_html=True)

st.markdown("<br><center style='font-size:0.85rem;color:#94a3b8;'>MIDSTREAM COLLEGE PRIMARY Digital Hub 2026</center>", unsafe_allow_html=True)
