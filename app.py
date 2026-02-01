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

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"
LOGO_URL = "https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg"

TZ = pytz.timezone("Africa/Johannesburg")
now_dt = datetime.now(TZ)
today = now_dt.date()

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
  margin-bottom:22px;
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

/* ✅ badge moved to bottom-right (no overlap on phone) */
.ribbon{
  position:absolute;
  right:12px;
  bottom:12px;
  top:auto;
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
.rDot{width:8px;height:8px;border-radius:999px;background:#B00000;}
.rDot.pulse{animation:pulse 1.0s infinite;}
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
    if "sport" in s:
        return "sport"
    if "culture" in s or "kultuur" in s:
        return "culture"
    if "academic" in s or "academics" in s or "akadem" in s:
        return "academics"
    return s

def normalize_activity(v: str) -> str:
    s = str(v or "").strip().lower()
    s = re.sub(r"\s+", " ", s)

    if s in ["ht", "afrikaans ht"] or "hooftaal" in s:
        return "Afrikaans Hooftaal"
    if s in ["eat", "afrikaans eat"] or "eerste addisionele" in s:
        return "Afrikaans Eerste Addisionele Taal"

    if "wiskunde" in s:
        return "Math"
    if "atletiek" in s or "athletics" in s:
        return "Athletics"
    if "swem" in s or "swimming" in s or "gala" in s:
        return "Swimming"
    if "tennis" in s:
        return "Tennis"
    if "rugby" in s:
        return "Rugby"
    if "hockey" in s:
        return "Hockey"
    if "netbal" in s or "netball" in s:
        return "Netball"
    if "koor" in s or "choir" in s:
        return "Choir"
    if "revue" in s:
        return "Revue"
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

# ---------- SA DATE ----------
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
    if s is None:
        return None
    raw = str(s).strip()
    if raw == "" or raw.lower() in ["nan", "none"]:
        return None

    if re.fullmatch(r"\d+(\.\d+)?", raw):
        try:
            n = float(raw)
            if n > 30000:
                base = datetime(1899, 12, 30)
                return base + timedelta(days=int(n))
        except:
            pass

    m = re.match(r"^\s*(\d{1,2})\s+([A-Za-z]+)\s*$", raw)
    if m:
        d = int(m.group(1))
        mon = m.group(2).lower()
        if mon in MONTHS:
            year = datetime.now(TZ).year
            try:
                return datetime.strptime(f"{d} {MONTHS[mon]} {year}", "%d %B %Y")
            except:
                pass

    cleaned = raw.replace(".", "/").replace("-", "/")
    cleaned = re.sub(r"\s+", " ", cleaned)

    d1 = pd.to_datetime(cleaned, dayfirst=True, errors="coerce")
    if not pd.isnull(d1):
        return d1.to_pydatetime()

    d2 = pd.to_datetime(cleaned, dayfirst=False, errors="coerce")
    if not pd.isnull(d2):
        return d2.to_pydatetime()

    return None

def format_date_long_sa(s) -> str:
    dt = parse_date_sa(s)
    if not dt:
        return str(s or "").strip()
    return f"{dt.day} {dt.strftime('%B %Y')}"

# ---------- VENUE ----------
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
# AGE GROUP / GRADE PARSING (GLOBAL RULE)
# =============================
def parse_groups(raw: str, prefix: str):
    """
    GLOBAL parser for BOTH Sport and Academics/Culture
    Returns expanded list like:
      ['U10','U11'...] or ['Gr 4','Gr 5'...]
    Accepts:
      U10-U13 / 10-13 / 07-13 / U10,11,12,13 / 10,11,12,13
      Gr4-Gr7 / 4-7 / Gr 4,5,6,7 / 4,5,6,7
    """
    s = str(raw or "").strip()
    if not s:
        return []

    s = s.replace("–", "-").replace("—", "-")
    s = re.sub(r"\s+", "", s)  # remove spaces

    nums = [int(n) for n in re.findall(r"\d{1,2}", s)]
    if not nums:
        return []

    def fmt(n: int) -> str:
        return f"U{n}" if prefix == "U" else f"Gr {n}"

    # range
    if "-" in s and len(nums) >= 2:
        lo, hi = nums[0], nums[1]
        if lo > hi:
            lo, hi = hi, lo
        return [fmt(i) for i in range(lo, hi + 1)]

    # list
    if "," in s:
        seen = set()
        out = []
        for n in nums:
            if n not in seen:
                seen.add(n)
                out.append(n)

        if len(out) >= 3:
            lo, hi = min(out), max(out)
            if (hi - lo) <= 10:
                out = list(range(lo, hi + 1))

        return [fmt(i) for i in out]

    # single
    if len(nums) == 1:
        return [fmt(nums[0])]

    return [fmt(i) for i in nums]

def extract_u_groups_from_text(text: str):
    t = str(text or "").strip()
    if not t:
        return []
    t = t.replace("–", "-").replace("—", "-")

    m = re.search(r"\bU?\d{1,2}\s*-\s*U?\d{1,2}\b", t, flags=re.I)
    if m:
        return parse_groups(m.group(0), "U")

    m = re.search(r"\bU?\d{1,2}(?:\s*,\s*U?\d{1,2}){1,}\b", t, flags=re.I)
    if m:
        return parse_groups(m.group(0), "U")

    m = re.search(r"\bU(\d{1,2})\b", t, flags=re.I)
    if m:
        return [f"U{int(m.group(1))}"]

    return []

def group_for_row(cat_norm: str, grade_raw: str, team_raw: str):
    if cat_norm == "sport":
        g = str(grade_raw or "").strip()
        m = parse_groups(g, "U") if g else extract_u_groups_from_text(team_raw)
        if len(m) >= 2:
            return f"{m[0]}-{m[-1]}", m
        return (m[0] if m else ""), m

    g = str(grade_raw or "").strip()
    if not g:
        return "", []
    m = parse_groups(g, "Gr")
    if len(m) >= 2:
        return f"{m[0]}–{m[-1]}", m
    return (m[0] if m else ""), m

# ---------- TEXT CLEANUP / NO DUPLICATE GROUP ----------
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

    grp_disp, _ = group_for_row(cn, grade_val, team_val)

    team_clean = strip_group_tokens(team_val)
    team_clean = tidy_team_text(norm_gender_words(team_clean))

    if grp_disp:
        if grp_disp.lower() in team_clean.lower():
            return re.sub(r"\s{2,}", " ", f"{act_txt} {team_clean}".strip())
        return re.sub(r"\s{2,}", " ", f"{act_txt} {grp_disp} {team_clean}".strip())

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
    if st.button("🔄 Refresh data"):
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

# =============================
# VIEW TOGGLES
# =============================
view_mode = st.radio("View", ["Upcoming", "Next 7 Days", "Term Documents"], horizontal=True)

# =============================
# FILTERS
# =============================
st.sidebar.markdown("## Filters")

category_choice = st.sidebar.multiselect("Category", ["Sport", "Culture", "Academics"], default=[])
search = st.sidebar.text_input("Whole school search", placeholder="Type to filter...")

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
selected_act = st.sidebar.multiselect("Activity/Subject", act_opts, default=[])

selected_u = st.sidebar.multiselect(
    "Age Groups (Sport)",
    [f"U{i}" for i in range(7, 14)],
    default=[]
) if (not wanted or "sport" in wanted) else []

selected_gr = st.sidebar.multiselect(
    "Grades (Culture/Academics)",
    [f"Gr {i}" for i in range(1, 8)],
    default=[]
) if (not wanted or "culture" in wanted or "academics" in wanted) else []

selected_u_set = set(selected_u)
selected_gr_set = set(selected_gr)

# =============================
# NEW UPDATE TRACKING (badge)
# =============================
def row_signature(i: int) -> str:
    parts = [
        cat_s.iloc[i], act_s.iloc[i], team_s.iloc[i], date_s.iloc[i], ven_s.iloc[i],
        prog_s.iloc[i], teamlnk_s.iloc[i], conf_s.iloc[i], info_s.iloc[i],
        grade_s.iloc[i], term_s.iloc[i]
    ]
    return hashlib.sha256(("||".join(map(str, parts))).encode("utf-8")).hexdigest()

if "row_hashes" not in st.session_state:
    st.session_state.row_hashes = {}
if "row_updated_at" not in st.session_state:
    st.session_state.row_updated_at = {}

# ✅ Parents miss updates: badge shows for 1 hour, pulses for 10 minutes
BADGE_VISIBLE_HOURS = 1
BADGE_PULSE_MINUTES = 10

# =============================
# BUILD RESULTS
# =============================
res = []
for i in range(len(df)):
    cn = normalize_category(cat_s.iloc[i])
    act_norm = normalize_activity(act_s.iloc[i])

    if wanted and not cat_ok(i):
        continue
    if selected_act and act_norm not in selected_act:
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

    if view_mode == "Next 7 Days":
        if not d_dt:
            continue
        if d_dt.date() > (today + timedelta(days=7)):
            continue

    if view_mode == "Term Documents":
        if not term_flag:
            continue

    grp_disp, grp_matches = group_for_row(cn, grade_s.iloc[i], team_s.iloc[i])

    if cn == "sport" and selected_u_set:
        if grp_matches and not any(x in selected_u_set for x in grp_matches):
            continue
        if not grp_matches:
            continue

    if cn in ["culture", "academics"] and selected_gr_set:
        if grp_matches and not any(x in selected_gr_set for x in grp_matches):
            continue
        if not grp_matches:
            continue

    title = build_title(cat_s.iloc[i], act_s.iloc[i], team_s.iloc[i], grade_s.iloc[i])

    if search and search.lower().replace(" ", "") not in title.lower().replace(" ", ""):
        continue

    sig = row_signature(i)
    prev = st.session_state.row_hashes.get(i)
    if prev is None:
        st.session_state.row_hashes[i] = sig
        st.session_state.row_updated_at[i] = now_dt
    elif prev != sig:
        st.session_state.row_hashes[i] = sig
        st.session_state.row_updated_at[i] = now_dt

    updated_at = st.session_state.row_updated_at.get(i)

    # ✅ badge for ALL categories: Sport + Culture + Academics
    show_badge = False
    pulse_badge = False
    if updated_at:
        age = now_dt - updated_at
        show_badge = age <= timedelta(hours=BADGE_VISIBLE_HOURS)
        pulse_badge = age <= timedelta(minutes=BADGE_PULSE_MINUTES)

    sort_dt = d_dt if d_dt else datetime(2099, 1, 1)
    grade_raw_for_sort = str(grade_s.iloc[i] or "").strip()

    res.append({
        "i": i,
        "dt": sort_dt,
        "title": title.lower(),
        "term": term_flag,
        "badge": show_badge,
        "pulse": pulse_badge,
        "grade": grade_raw_for_sort
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
    st.info("Niks pas by jou filters nie.")
else:
    for item in res_sorted:
        i = item["i"]
        cn = normalize_category(cat_s.iloc[i])
        afr = is_afrikaans_subject(act_s.iloc[i])

        title = build_title(cat_s.iloc[i], act_s.iloc[i], team_s.iloc[i], grade_s.iloc[i])

        d_raw = str(date_s.iloc[i]).strip()
        date_line = format_date_long_sa(d_raw) if d_raw else ""

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

        if "revue" in (title.lower() + " " + info_raw.lower()):
            notes_parts.append("<b>Note:</b><br>Revue")

        notes_block = f"<div class='noteBlock'>{'<br><br>'.join(notes_parts)}</div>" if notes_parts else ""

        btn_html = ""
        if buttons:
            btn_html = "<div class='btnRow'>" + "".join(
                [f"<a class='btn' href='{u}' target='_blank'>{safe_txt(lbl)}</a>" for lbl, u in buttons[:4]]
            ) + "</div>"

        ribbon = ""
        if item.get("badge"):
            dot_class = "rDot pulse" if item.get("pulse") else "rDot"
            ribbon = f"<div class='ribbon'><span class='{dot_class}'></span>NEW UPDATE</div>"

        st.markdown(
            f"""
<div class="card">
  {ribbon}
  <div class="card-title">{safe_txt(title)}</div>
  {f"<div class='meta'>📅 <b>{safe_txt(date_line)}</b></div>" if date_line else ""}
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
