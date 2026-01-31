# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import requests, io, re, pytz, hashlib
from datetime import datetime, timedelta

st.set_page_config(page_title="LMCP Hub", page_icon="📌", layout="wide")

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"
LOGO_URL = "https://midstream-primary.co.za/wp-content/uploads/2022/01/210828_Midstream_Icon-removebg-preview.png"
TZ = pytz.timezone("Africa/Johannesburg")

# ---------- PAGE BANNER (ONE COLOUR, MOVED DOWN) ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap');
html, body, [class*="css"] {font-family: 'Inter', sans-serif;}
:root{
  --maroon:#800000; --teal:#008080; --line:#e8edf5; --shadow:0 10px 30px rgba(0,0,0,.06);
}
.block-container{padding-top:1.25rem;}  /* moves banner down */
.topBanner{
  margin-top:10px;
  border-radius:22px;
  padding:16px 18px;
  margin-bottom:18px;
  background: var(--maroon);          /* ONE colour */
  box-shadow: var(--shadow);
  color: #fff;
  display:flex; align-items:center; gap:14px; flex-wrap:wrap;
}
.topLogo{
  width:66px;height:66px;border-radius:16px;
  background:#fff; display:flex; align-items:center; justify-content:center;
  overflow:hidden;
  border:2px solid rgba(255,255,255,0.35);
}
.topLogo img{width:66px;height:auto;}
.topTitle{font-weight:900;font-size:1.22rem;letter-spacing:.2px;line-height:1.05;}
.topSub{margin-top:6px;font-weight:800;font-size:1.0rem;opacity:.95;}

.card{
  border:1px solid var(--line);
  background:#fff;
  box-shadow: var(--shadow);
  border-radius:18px;
  padding:14px 14px 12px 14px;
  margin-bottom:14px;
  border-left:10px solid var(--maroon);
  position:relative;
}
.card-title{font-weight:900;color:var(--maroon);font-size:1.15rem;line-height:1.2;}
.meta{color:#64748b;margin-top:8px;font-size:.95rem;}
.noteBlock{
  margin-top:12px; padding:12px;
  border-radius:14px;
  background:rgba(0,128,128,0.08);
  border:1px solid rgba(0,128,128,0.25);
  color:#0f172a; font-size:.95rem; line-height:1.35;
}
.btnRow{display:flex;gap:10px;flex-wrap:wrap;margin-top:12px;}
.btn{
  display:inline-block;background:var(--teal);color:white !important;
  padding:9px 12px;border-radius:12px;font-weight:900;
  text-decoration:none;font-size:.90rem;
}
.btn:hover{opacity:.92;}

.ribbon{
  position:absolute; top:12px; right:12px;
  background:#FFD400;
  color:#B00000;
  font-weight:1000;
  font-size:.78rem;
  padding:6px 10px;
  border-radius:999px;
  border: 1px solid rgba(176,0,0,0.25);
  box-shadow: 0 8px 16px rgba(0,0,0,0.10);
  display:flex; align-items:center; gap:8px;
}
.rDot{
  width:8px;height:8px;border-radius:999px;background:#B00000;
  animation:pulse 1.0s infinite;
}
@keyframes pulse{
  0%{transform:scale(1); opacity:.4;}
  50%{transform:scale(1.7); opacity:1;}
  100%{transform:scale(1); opacity:.4;}
}
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="topBanner">
  <div class="topLogo"><img src="{LOGO_URL}"></div>
  <div>
    <div class="topTitle">LAERSKOOL MIDSTREAM COLLEGE PRIMARY</div>
    <div class="topSub">Digital Hub</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ---------- HELPERS ----------
def safe_txt(x) -> str:
    s = str(x or "")
    return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").strip()

def is_http(u: str) -> bool:
    s = str(u or "").strip().lower()
    return s.startswith("http://") or s.startswith("https://")

def is_form_link(u: str) -> bool:
    s = str(u or "").lower()
    return ("forms.gle" in s) or ("docs.google.com/forms" in s)

def first_url(v: str) -> str:
    s = str(v or "").replace("\n"," ").strip()
    m = re.search(r"https?://\S+", s)
    return m.group(0) if m else s

def normalize_category(v: str) -> str:
    s = str(v or "").strip().lower()
    if "sport" in s: return "sport"
    if "culture" in s or "kultuur" in s: return "culture"
    if "academic" in s or "academics" in s or "akadem" in s: return "academics"
    return s

def normalize_activity(v: str) -> str:
    s = str(v or "").strip().lower()
    s = re.sub(r"\s+"," ", s)
    if s in ["ht","afrikaans ht"] or "hooftaal" in s:
        return "Afrikaans Hooftaal"
    if s in ["eat","afrikaans eat"] or "eerste addisionele" in s:
        return "Afrikaans Eerste Addisionele Taal"
    if "athletics" in s or "atletiek" in s: return "Athletics"
    if "swimming" in s or "swem" in s or "gala" in s: return "Swimming"
    if "tennis" in s: return "Tennis"
    if "rugby" in s: return "Rugby"
    if "hockey" in s: return "Hockey"
    if "netbal" in s or "netball" in s: return "Netball"
    if "koor" in s or "choir" in s: return "Choir"
    if "revue" in s: return "Revue"
    return s.title()

def is_afrikaans_subject(b_raw: str) -> bool:
    s = str(b_raw or "").strip().lower()
    return ("afrikaans" in s) or (s in ["ht","eat"]) or ("hooftaal" in s) or ("eerste addisionele" in s)

def norm_gender_words(text: str) -> str:
    """
    Fix Meisies/Seuns; B/G tokens, but:
    - DO NOT convert 'B' -> Boys if string already contains 'Boys'
    - DO NOT duplicate BoysBoys / GirlsGirls
    """
    s = str(text or "").strip().replace("_", " ")
    s = re.sub(r"\s+"," ", s).strip()

    s = re.sub(r"\bmeisies\b", "Girls", s, flags=re.I)
    s = re.sub(r"\bseuns\b", "Boys", s, flags=re.I)

    has_boys = re.search(r"\bboys\b", s, flags=re.I) is not None
    has_girls = re.search(r"\bgirls\b", s, flags=re.I) is not None

    s = re.sub(r"\bgirls\b", "Girls", s, flags=re.I)
    s = re.sub(r"\bboys\b", "Boys", s, flags=re.I)

    if not has_boys:
        s = re.sub(r"\bB\b", "Boys", s)
    if not has_girls:
        s = re.sub(r"\bG\b", "Girls", s)

    s = re.sub(r"(Boys)\s*(Boys)\b", r"\1", s)
    s = re.sub(r"(Girls)\s*(Girls)\b", r"\1", s)
    return re.sub(r"\s+"," ", s).strip()

MONTHS = {
    "jan":"January","january":"January",
    "feb":"February","february":"February",
    "mar":"March","march":"March",
    "apr":"April","april":"April",
    "may":"May",
    "jun":"June","june":"June",
    "jul":"July","july":"July",
    "aug":"August","august":"August",
    "sep":"September","september":"September",
    "oct":"October","october":"October",
    "nov":"November","november":"November",
    "dec":"December","december":"December",
}

def parse_date_sa(s):
    """
    Accepts:
      - 2/11/2026, 2-11-2026, 02.11.2026 (day-first)
      - "2 NOVEMBER" (assumes current year)
      - Excel serials
    """
    if s is None: return None
    raw = str(s).strip()
    if raw == "" or raw.lower() in ["nan","none"]: return None

    # Excel serial
    if re.fullmatch(r"\d+(\.\d+)?", raw):
        try:
            n = float(raw)
            if n > 30000:
                base = datetime(1899, 12, 30)
                return base + timedelta(days=int(n))
        except:
            pass

    # "2 NOVEMBER" (no year)
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
    cleaned = re.sub(r"\s+"," ", cleaned)

    d1 = pd.to_datetime(cleaned, dayfirst=True, errors="coerce")
    if not pd.isnull(d1): return d1.to_pydatetime()

    d2 = pd.to_datetime(cleaned, dayfirst=False, errors="coerce")
    if not pd.isnull(d2): return d2.to_pydatetime()

    return None

def format_date_long_sa(s) -> str:
    dt = parse_date_sa(s)
    if not dt:
        return str(s or "").strip()
    return f"{dt.day} {dt.strftime('%B %Y')}"

VENUE_MAP = {
    "bondev": "Bondev Field",
    "veld": "Field",
    "saal": "Hall",
    "ouditorium": "Auditorium",
    "netbal bane": "Netball Courts",
    "tennis bane": "Tennis Courts",
    "swembad": "Swimming Pool",
    "cricket oval": "Cricket Oval",
    "skaak": "Chess",
    "musiekkamer": "Music Room",
    "musiek kamer": "Music Room",
}

def normalize_venue(v: str) -> str:
    s = str(v or "").strip().replace("_", " ")
    s = re.sub(r"\s+"," ", s)
    sl = s.lower()
    if "see programme" in sl or "see program" in sl or "sien program" in sl or "sien programme" in sl:
        return "SEE_PROGRAMME"
    for k, vv in VENUE_MAP.items():
        if k in sl:
            return vv
    return s

def expand_group_range(raw: str, kind: str):
    """
    FIXED: no IndexError.
    Accepts:
      - U7-9, U8-13, 7-9
      - Gr5-7, Gr 2-4, 2-4
      - U7, Gr 7
    Returns list of labels: ["U7","U8"...] or ["Gr 5","Gr 6"...]
    """
    s = str(raw or "").strip().replace(" ", "")
    if not s:
        return []
    s = s.replace("–", "-").replace("to", "-").replace("TO", "-")

    nums = re.findall(r"\d+", s)
    if len(nums) >= 2 and "-" in s:
        lo, hi = sorted([int(nums[0]), int(nums[1])])
        if kind == "U":
            return [f"U{i}" for i in range(lo, hi + 1)]
        return [f"Gr {i}" for i in range(lo, hi + 1)]

    if len(nums) == 1:
        n = nums[0]
        if kind == "U":
            return [f"U{n}"]
        return [f"Gr {n}"]

    return []

def group_from_category_and_M(cat_norm: str, act_norm: str, m_raw: str):
    """
    Uses Column M (grade/age group).
    If M empty:
      - Swimming => U8-U13
      - Athletics => U7-U13
    """
    m = str(m_raw or "").strip()
    if cat_norm == "sport":
        if m:
            matches = expand_group_range(m, "U")
            if len(matches) >= 2:
                return f"{matches[0]}-{matches[-1]}", matches
            return matches[0] if matches else "", matches
        if act_norm.lower() == "swimming":
            matches = [f"U{i}" for i in range(8, 14)]
            return "U8-U13", matches
        if act_norm.lower() == "athletics":
            matches = [f"U{i}" for i in range(7, 14)]
            return "U7-U13", matches
        return "", []

    # academics/culture
    if m:
        matches = expand_group_range(m, "Gr")
        if len(matches) >= 2:
            return f"{matches[0]}–{matches[-1]}", matches
        return matches[0] if matches else "", matches
    return "", []

def build_title(cat_val: str, b_val: str, c_val: str, m_val: str) -> str:
    """
    Sport: B + ' ' + U.. + C (NO space between group and C)
    Academics/Culture: B + ' ' + Gr .. + ' ' + C
    """
    cn = normalize_category(cat_val)
    act_norm = normalize_activity(b_val)
    b_txt = norm_gender_words(act_norm)
    c_txt = norm_gender_words(c_val).strip()

    group_disp, _ = group_from_category_and_M(cn, act_norm, m_val)
    if not group_disp:
        return f"{b_txt} {c_txt}".strip()

    if cn == "sport":
        return f"{b_txt} {group_disp}{c_txt}".strip()

    return f"{b_txt} {group_disp} {c_txt}".strip()

@st.cache_data(ttl=120)
def load_csv(url: str):
    r = requests.get(url, timeout=25, headers={"User-Agent":"Mozilla/5.0"}, allow_redirects=True)
    r.encoding = "utf-8"
    txt = r.text or ""
    if r.status_code != 200 or len(txt) < 20 or "<html" in txt.lower():
        return pd.DataFrame(), txt
    df = pd.read_csv(io.StringIO(txt), dtype=str, engine="python", on_bad_lines="skip").fillna("")
    return df, txt

df, raw_txt = load_csv(CSV_URL)
if df.empty:
    st.error("No data loaded. Check your published CSV link (sometimes Google returns HTML right after republish).")
    st.stop()

now_dt = datetime.now(TZ)
today = now_dt.date()

# ----- COLUMN MAP (A..M) -----
# A Category
# B Activity/Subject
# C Team/Assessment
# D Due Date
# E Venue
# G Programme link
# H Team link
# I Confirm link (form)
# J Information (text or link)
# K Term marker ("Full Term")
# M Grade/Age group (Gr 7 / Gr 5-7 / U8-13 etc.)
A_CAT = 0
B_ACT = 1
C_TEAM = 2
D_DATE = 3
E_VEN = 4
G_PROG = 6
H_TEAM = 7
I_CONFIRM = 8
J_INFO = 9
K_TERM = 10
M_GROUP = 12

def col(i, default=""):
    if df.shape[1] > i:
        return df.iloc[:, i].astype(str)
    return pd.Series([default]*len(df), dtype=str)

cat_s = col(A_CAT)
act_s = col(B_ACT)
team_s = col(C_TEAM)
date_s = col(D_DATE)
ven_s = col(E_VEN)
prog_s = col(G_PROG)
teamlink_s = col(H_TEAM)
confirm_s = col(I_CONFIRM)
info_s = col(J_INFO)
term_s = col(K_TERM)
m_s = col(M_GROUP)
# ---------- VIEW TOGGLES ----------
view_mode = st.radio("View", ["Upcoming", "Next 7 Days", "Term Documents"], horizontal=True)

# ---------- FILTERS ----------
st.sidebar.markdown("## Filters")
category_choice = st.sidebar.multiselect("Category", ["Sport", "Culture", "Academics"], default=[])
search = st.sidebar.text_input("Whole school search", placeholder="Type to filter...")

wanted = {c.lower() for c in category_choice} if category_choice else set()

def cat_ok(i: int) -> bool:
    if not wanted:
        return True
    cn = normalize_category(cat_s.iloc[i])
    return (("sport" in wanted and cn == "sport") or
            ("culture" in wanted and cn == "culture") or
            ("academics" in wanted and cn == "academics"))

act_opts = sorted({normalize_activity(act_s.iloc[i]) for i in range(len(df)) if str(act_s.iloc[i]).strip() and cat_ok(i)})
selected_act = st.sidebar.multiselect("Activity/Subject", act_opts, default=[])

# Only single options (no Gr 4–7 etc), but sheet ranges still match via expansion
selected_u = st.sidebar.multiselect("Age Groups (Sport)", [f"U{i}" for i in range(7,14)], default=[]) if (not wanted or "sport" in wanted) else []
selected_gr = st.sidebar.multiselect("Grades (Culture/Academics)", [f"Gr {i}" for i in range(1,8)], default=[]) if (not wanted or "culture" in wanted or "academics" in wanted) else []

selected_u_set = set(selected_u)
selected_gr_set = set(selected_gr)

# ---------- NEW UPDATE (DOCUMENTS ONLY): last hour, animation only 10 minutes ----------
def row_signature(i: int) -> str:
    parts = [
        cat_s.iloc[i], act_s.iloc[i], team_s.iloc[i], date_s.iloc[i], ven_s.iloc[i],
        prog_s.iloc[i], teamlink_s.iloc[i], confirm_s.iloc[i], info_s.iloc[i],
        term_s.iloc[i], m_s.iloc[i]
    ]
    return hashlib.sha256(("||".join(map(str, parts))).encode("utf-8")).hexdigest()

if "row_hashes" not in st.session_state:
    st.session_state.row_hashes = {}
if "row_updated_at" not in st.session_state:
    st.session_state.row_updated_at = {}

# ---------- BUILD RESULTS ----------
res = []
for i in range(len(df)):
    cn = normalize_category(cat_s.iloc[i])
    act_norm = normalize_activity(act_s.iloc[i])

    if wanted and not cat_ok(i):
        continue

    if selected_act and act_norm not in selected_act:
        continue

    # term documents (filter toggle only)
    term_flag = "full term" in str(term_s.iloc[i]).strip().lower()

    # due date
    d_raw = str(date_s.iloc[i]).strip()
    d_dt = parse_date_sa(d_raw)

    # show today + future; hide yesterday
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

    # Group uses M
    group_disp, group_matches = group_from_category_and_M(cn, act_norm, m_s.iloc[i])

    # Filtering expansion (ranges in sheet)
    if cn == "sport" and selected_u_set:
        if group_matches:
            if not any(x in selected_u_set for x in group_matches):
                continue
        else:
            continue

    if cn in ["culture", "academics"] and selected_gr_set:
        if group_matches:
            if not any(x in selected_gr_set for x in group_matches):
                continue
        else:
            continue

    title = build_title(cat_s.iloc[i], act_s.iloc[i], team_s.iloc[i], m_s.iloc[i])

    if search and search.lower().replace(" ", "") not in title.lower().replace(" ", ""):
        continue

    # Update tracking
    sig = row_signature(i)
    prev = st.session_state.row_hashes.get(i)
    if prev is None:
        st.session_state.row_hashes[i] = sig
        st.session_state.row_updated_at[i] = now_dt
    elif prev != sig:
        st.session_state.row_hashes[i] = sig
        st.session_state.row_updated_at[i] = now_dt

    updated_at = st.session_state.row_updated_at.get(i)

    # Documents only (academics): badge if updated within last hour,
    # BUT animation only shows for 10 minutes then disappears.
    show_new = False
    if cn == "academics" and updated_at:
        if (now_dt - updated_at) <= timedelta(hours=1) and (now_dt - updated_at) <= timedelta(minutes=10):
            show_new = True

    sort_dt = d_dt if d_dt else datetime(2099,1,1)
    res.append({"i": i, "dt": sort_dt, "title": title.lower(), "term": term_flag, "new": show_new})

# Sort: term docs first (alpha), then date then title
term_items = sorted([x for x in res if x["term"]], key=lambda x: x["title"])
other_items = sorted([x for x in res if not x["term"]], key=lambda x: (x["dt"], x["title"]))
res_sorted = term_items + other_items

# ---------- DISPLAY ----------
st.markdown("## 📅 Events")

if not res_sorted:
    st.info("Nothing matched your filters/search.")
else:
    for item in res_sorted:
        i = item["i"]
        cn = normalize_category(cat_s.iloc[i])
        act_norm = normalize_activity(act_s.iloc[i])
        afr = is_afrikaans_subject(act_s.iloc[i])

        title = build_title(cat_s.iloc[i], act_s.iloc[i], team_s.iloc[i], m_s.iloc[i])

        # D + M + E (your final order)
        d_raw = str(date_s.iloc[i]).strip()
        date_line = format_date_long_sa(d_raw) if d_raw else ""

        group_disp, _ = group_from_category_and_M(cn, act_norm, m_s.iloc[i])
        group_line = group_disp

        ven_norm = normalize_venue(str(ven_s.iloc[i]).strip())

        # links
        prog_link = first_url(prog_s.iloc[i])
        team_link = first_url(teamlink_s.iloc[i])
        confirm_link = first_url(confirm_s.iloc[i])
        info_val = str(info_s.iloc[i]).strip().replace("_"," ")
        info_link = first_url(info_val) if is_http(info_val) else ""

        # Buttons per category
        if cn == "academics":
            # academics: Documents + Information only
            b1 = "Dokumentasie" if afr else "Documents"
            b2 = "Inligting" if afr else "Information"
            buttons = []
            if prog_link and is_http(prog_link):
                buttons.append((b1, prog_link))
            if info_link and is_http(info_link):
                buttons.append((b2, info_link))
        else:
            # sport/culture: Programme + Teams + Information + Confirm
            buttons = []
            if prog_link and is_http(prog_link):
                buttons.append(("Programme", prog_link))
            if team_link and is_http(team_link):
                buttons.append(("Teams", team_link))
            if info_link and is_http(info_link):
                buttons.append(("Information", info_link))
            if confirm_link and is_http(confirm_link) and is_form_link(confirm_link):
                buttons.append(("Confirm", confirm_link))

        # Venue line OR "See programme" behaviour
        venue_line = ""
        notes_parts = []

        if ven_norm == "SEE_PROGRAMME":
            notes_parts.append("<b>Venue:</b><br>See programme")
        elif ven_norm:
            q = ven_norm
            if "midstream" in ven_norm.lower():
                q = f"{ven_norm} Midstream College"
            map_url = f"https://www.google.com/maps/search/?api=1&query={q.replace(' ','+')}"
            venue_line = (
                f"<div class='meta'>📍 "
                f"<a href='{map_url}' target='_blank' style='color:#008080;font-weight:900;text-decoration:none;'>"
                f"{safe_txt(ven_norm).upper()}</a></div>"
            )

        # Info as NOTE if not a link
        if info_val and not is_http(info_val):
            # spelling cleanup (junior/senior choir, revue)
            note_txt = re.sub(r"\s+"," ", info_val).strip()
            notes_parts.append(f"<b>Note:</b><br>{safe_txt(note_txt)}")

        # Note “Revue” if present
        if "revue" in (title.lower() + " " + info_val.lower()):
            notes_parts.append("<b>Note:</b><br>Revue")

        notes_block = f"<div class='noteBlock'>{'<br><br>'.join(notes_parts)}</div>" if notes_parts else ""

        btn_html = ""
        if buttons:
            btn_html = "<div class='btnRow'>" + "".join(
                [f"<a class='btn' href='{u}' target='_blank'>{safe_txt(lbl)}</a>" for lbl, u in buttons[:4]]
            ) + "</div>"

        ribbon = "<div class='ribbon'><span class='rDot'></span>NEW UPDATE</div>" if item["new"] else ""

        st.markdown(f"""
<div class="card">
  {ribbon}
  <div class="card-title">{safe_txt(title)}</div>
  {f"<div class='meta'>📅 <b>{safe_txt(date_line)}</b></div>" if date_line else ""}
  {f"<div class='meta'>🏷 <b>{safe_txt(group_line)}</b></div>" if group_line else ""}
  {venue_line}
  {notes_block}
  {btn_html}
</div>
""", unsafe_allow_html=True)

st.markdown(
    "<br><center style='font-size:0.85rem;color:#94a3b8;'>LAERSKOOL MIDSTREAM COLLEGE PRIMARY Digital Hub 2026</center>",
    unsafe_allow_html=True
)
