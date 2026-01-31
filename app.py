# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import requests, io, re, pytz, hashlib
from datetime import datetime, timedelta

st.set_page_config(page_title="LMCP Hub", page_icon="📌", layout="wide")

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

# ✅ Replace this with your new logo URL
LOGO_URL = "https://midstream-primary.co.za/wp-content/uploads/2022/01/210828_Midstream_Icon-removebg-preview.png"

SCHOOL_SITE = "https://midstream-primary.co.za/en/home/"
TZ = pytz.timezone("Africa/Johannesburg")

if not str(CSV_URL).strip().lower().startswith(("http://", "https://")):
    st.error("CSV_URL is missing/invalid. Paste the FULL https://...output=csv link.")
    st.stop()

# ------------------ STYLE + HEADER ------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap');
html, body, [class*="css"] {font-family: 'Inter', sans-serif;}
:root{
  --card:#ffffff; --line:#e8edf5; --shadow:0 10px 30px rgba(0,0,0,.06);
  --maroon:#800000; --teal:#008080; --muted:#64748b; --soft:#f3fbfb;
}
.block-container{padding-top:1rem;}
.hero{
  border:1px solid var(--line);
  box-shadow:var(--shadow);
  border-radius:22px;
  padding:18px;
  margin-bottom:12px;
  background:linear-gradient(135deg, rgba(255,255,255,.96), rgba(240,251,251,.96));
}
.heroRow{display:flex;gap:14px;align-items:center;flex-wrap:wrap;}
.logo{
  width:86px;height:86px;border-radius:18px;
  background:#fff;
  border:1px solid var(--line);
  display:flex;align-items:center;justify-content:center;
  overflow:hidden;
}
.logo img{width:86px;height:auto;}
.hTitle{font-weight:900;color:var(--maroon);font-size:1.55rem;line-height:1.05;}
.hSub{font-weight:800;color:var(--teal);margin-top:6px;font-size:1.05rem;}
.hLink a{color:var(--teal);font-weight:800;text-decoration:none;}
.hLink a:hover{text-decoration:underline;}

.updateBanner{
  margin: 0 0 12px 0;
  border:1px solid rgba(0,128,128,0.30);
  background:rgba(0,128,128,0.08);
  padding:10px 12px;
  border-radius:14px;
  font-weight:900;
  color:#008080;
  display:flex; align-items:center; gap:10px;
}
.dot{
  width:10px;height:10px;border-radius:999px;background:#008080;
  animation:pulse 1.2s infinite;
}
@keyframes pulse{
  0%{transform:scale(1); opacity:0.35;}
  50%{transform:scale(1.7); opacity:1;}
  100%{transform:scale(1); opacity:0.35;}
}

.card{
  border:1px solid var(--line);
  background:var(--card);
  box-shadow:var(--shadow);
  border-radius:18px;
  padding:14px 14px 12px 14px;
  margin-bottom:14px;
  border-left:10px solid var(--maroon);
}
.card-title{font-weight:900;color:var(--maroon);font-size:1.15rem;line-height:1.2;}
.meta{color:var(--muted);margin-top:8px;font-size:.95rem;}
.noteBlock{
  margin-top:12px; padding:12px;
  border-radius:14px;
  background:rgba(0,128,128,0.08);
  border:1px solid rgba(0,128,128,0.25);
  color:#0f172a; font-size:.95rem; line-height:1.35;
}
.btnRow{display:flex;gap:10px;flex-wrap:wrap;margin-top:12px;}
.btn{
  display:inline-block;background:#008080;color:white !important;
  padding:9px 12px;border-radius:12px;font-weight:900;text-decoration:none;font-size:.90rem;
}
.btn:hover{opacity:.92;}
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="hero">
  <div class="heroRow">
    <div class="logo">
      <img src="{LOGO_URL}">
    </div>
    <div>
      <div class="hTitle">LAERSKOOL MIDSTREAM COLLEGE PRIMARY</div>
      <div class="hSub">Digital Hub</div>
      <div class="hLink"><a href="{SCHOOL_SITE}" target="_blank">midstream-primary.co.za</a></div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ------------------ HELPERS ------------------
def safe_txt(x) -> str:
    s = str(x or "")
    return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").strip()

def is_http(u: str) -> bool:
    s = str(u or "").strip().lower()
    return s.startswith("http://") or s.startswith("https://")

def is_form_link(u: str) -> bool:
    s = str(u or "").lower()
    return ("forms.gle" in s) or ("docs.google.com/forms" in s)

def clean_first_url(v: str) -> str:
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

    if s in ["ht", "afrikaans ht"] or "hooftaal" in s:
        return "Afrikaans Hooftaal"
    if s in ["eat", "afrikaans eat"] or "eerste addisionele" in s:
        return "Afrikaans Eerste Addisionele Taal"

    if "athletics" in s or "atletiek" in s: return "Athletics"
    if "swimming" in s or "swem" in s or "gala" in s: return "Swimming"
    if "tennis" in s: return "Tennis"
    if "rugby" in s: return "Rugby"
    if "hockey" in s: return "Hockey"
    if "netbal" in s or "netball" in s: return "Netball"

    return s.title()

def is_afrikaans_subject(b_raw: str) -> bool:
    s = str(b_raw or "").strip().lower()
    return ("afrikaans" in s) or (s in ["ht","eat"]) or ("hooftaal" in s) or ("eerste addisionele" in s)

def norm_gender_words(text: str) -> str:
    """
    Fix Meisies/Seuns; B/G tokens, but:
    - DO NOT convert 'B' -> Boys if string already contains 'boys'
    - DO NOT convert 'G' -> Girls if string already contains 'girls'
    - De-dupe accidental BoysBoys or GirlsGirls
    """
    s = str(text or "").strip().replace("_", " ")
    s = re.sub(r"\s+"," ", s).strip()

    # translate Afrikaans
    s = re.sub(r"\bmeisies\b", "Girls", s, flags=re.I)
    s = re.sub(r"\bseuns\b", "Boys", s, flags=re.I)

    has_boys = re.search(r"\bboys\b", s, flags=re.I) is not None
    has_girls = re.search(r"\bgirls\b", s, flags=re.I) is not None

    # normalize words
    s = re.sub(r"\bgirls\b", "Girls", s, flags=re.I)
    s = re.sub(r"\bboys\b", "Boys", s, flags=re.I)

    # single-letter tokens only if not already present
    if not has_boys:
        s = re.sub(r"\bB\b", "Boys", s)
    if not has_girls:
        s = re.sub(r"\bG\b", "Girls", s)

    # remove duplicates like BoysBoys or Boys Boys
    s = re.sub(r"(Boys)\s*(Boys)\b", r"\1", s)
    s = re.sub(r"(Girls)\s*(Girls)\b", r"\1", s)

    return re.sub(r"\s+"," ", s).strip()

def parse_date_sa(s):
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

    cleaned = raw.replace(".", "/").replace("-", "/")
    cleaned = re.sub(r"\s+"," ", cleaned)

    d = pd.to_datetime(cleaned, dayfirst=True, errors="coerce")
    if not pd.isnull(d): return d.to_pydatetime()

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
    "bondev field": "Bondev Field",
    "veld": "Field",
    "netbal bane": "Netball Courts",
    "netball courts": "Netball Courts",
    "cricket oval": "Cricket Oval",
    "swembad": "Swimming Pool",
    "swimming pool": "Swimming Pool",
    "tennis bane": "Tennis Courts",
    "tennis courts": "Tennis Courts",
    "ouditorium": "Auditorium",
    "auditorium": "Auditorium",
    "saal": "Hall",
    "hall": "Hall",
    "skaak": "Chess",
    "chess": "Chess",
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

def format_j_for_row(cat_norm: str, act_norm: str, j_raw: str):
    """
    Sport: prefix U no space; expands 10-13 to U10-U13 + matches U10..U13.
    Academics/Culture: prefix "Gr " with a SPACE. (Your correction)
    If Sport and J blank and Athletics/Swimming -> default range label + matches.
    """
    j = str(j_raw or "").strip().replace(" ", "")
    match = []

    if cat_norm == "sport" and j == "":
        if act_norm.lower() == "athletics":
            return "U7-U13", [f"U{x}" for x in range(7, 14)]
        if act_norm.lower() == "swimming":
            return "U8-U13", [f"U{x}" for x in range(8, 14)]
        return "", []

    if cat_norm == "sport":
        nums = re.findall(r"\d+", j)
        if "-" in j and len(nums) >= 2:
            lo, hi = sorted([int(nums[0]), int(nums[1])])
            match = [f"U{x}" for x in range(lo, hi + 1)]
            return f"U{lo}-U{hi}", match
        if j.lower().startswith("u"):
            return j, [j]
        if j:
            return f"U{j}", [f"U{j}"]
        return "", []

    # Academics/Culture: "Gr 6"
    if j.lower().startswith("gr"):
        # if someone typed Gr6 -> Gr 6
        digits = re.findall(r"\d+", j)
        if digits:
            return f"Gr {digits[0]}", [f"Gr {digits[0]}"]
        return j.replace("Gr", "Gr ").strip(), [j.replace("Gr", "Gr ").strip()]
    if j:
        return f"Gr {j}", [f"Gr {j}"]
    return "", []

def build_title(cat_val: str, b_val: str, j_val: str, c_val: str) -> str:
    """
    Sport:        B + ' ' + U+J + C   (NO space between J and C)
    Academ/Cult:  B + ' ' + 'Gr 6' + ' ' + C
    """
    cn = normalize_category(cat_val)
    act_norm = normalize_activity(b_val)

    b_txt = norm_gender_words(act_norm)
    c_txt = norm_gender_words(c_val).strip()

    j_display, _ = format_j_for_row(cn, act_norm, j_val)

    if not j_display:
        return f"{b_txt} {c_txt}".strip()

    if cn == "sport":
        return f"{b_txt} {j_display}{c_txt}".strip()

    return f"{b_txt} {j_display} {c_txt}".strip()

@st.cache_data(ttl=120)
def load_csv(url: str):
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, timeout=25, headers=headers, allow_redirects=True)
    # Force UTF-8 for special characters
    r.encoding = "utf-8"
    txt = r.text or ""
    if r.status_code != 200 or len(txt) < 20 or "<html" in txt.lower():
        return pd.DataFrame(), txt
    df = pd.read_csv(io.StringIO(txt), dtype=str, engine="python", on_bad_lines="skip").fillna("")
    return df, txt

df, raw_txt = load_csv(CSV_URL)
if df.empty:
    st.error("No data loaded. Check your published CSV link.")
    st.stop()

now_dt = datetime.now(TZ)
today = now_dt.date()

# NEW UPDATE (6 hours) when CSV changes
current_hash = hashlib.sha256((raw_txt or "").encode("utf-8")).hexdigest()
if "prev_hash" not in st.session_state:
    st.session_state.prev_hash = current_hash
    st.session_state.last_change = None
elif current_hash != st.session_state.prev_hash:
    st.session_state.prev_hash = current_hash
    st.session_state.last_change = now_dt

if st.session_state.get("last_change") and (now_dt - st.session_state.last_change) <= timedelta(hours=6):
    st.markdown("""<div class="updateBanner"><span class="dot"></span> NEW UPDATE</div>""", unsafe_allow_html=True)

# ---- COLUMN POSITIONS (A..K in your published sheet) ----
A_CAT = 0
B_ACT = 1
C_TEAM = 2
D_DATE = 3
E_VEN = 4
F_PROG = 5
G_TEAMLINK = 6
H_CONFIRM = 7
I_INFO = 8
J_GRADEU = 9
K_DUR = 10

def col(i, default=""):
    if df.shape[1] > i:
        return df.iloc[:, i].astype(str)
    return pd.Series([default]*len(df), dtype=str)

cat_s = col(A_CAT)
act_s = col(B_ACT)
team_s = col(C_TEAM)
date_s = col(D_DATE)
ven_s = col(E_VEN)
prog_s = col(F_PROG)
teamlink_s = col(G_TEAMLINK)
confirm_s = col(H_CONFIRM)
info_s = col(I_INFO)
j_s = col(J_GRADEU)
dur_s = col(K_DUR)
# ------------------ TOP TOGGLES ------------------
view_mode = st.radio("View", ["Upcoming", "Next 7 Days", "Term Documents"], horizontal=True)

# ------------------ SIDEBAR FILTERS (mobile hamburger) ------------------
st.sidebar.markdown("## Filters")
category_choice = st.sidebar.multiselect("Category", ["Sport", "Culture", "Academics"], default=[])
search = st.sidebar.text_input("Whole school search", placeholder="Type to filter...")

wanted = {c.lower() for c in category_choice} if category_choice else set()

def row_category_ok(i: int) -> bool:
    if not wanted:
        return True
    cn = normalize_category(cat_s.iloc[i])
    return (("sport" in wanted and cn == "sport") or
            ("culture" in wanted and cn == "culture") or
            ("academics" in wanted and cn == "academics"))

act_opts = sorted({normalize_activity(act_s.iloc[i]) for i in range(len(df)) if str(act_s.iloc[i]).strip() and row_category_ok(i)})
selected_activities = st.sidebar.multiselect("Activity/Subject", act_opts, default=[])

# Age / Grade filters back (with Gr space rule)
show_u = (not wanted) or ("sport" in wanted)
show_gr = (not wanted) or ("culture" in wanted) or ("academics" in wanted)

selected_u = st.sidebar.multiselect("Age Groups (Sport)", [f"U{i}" for i in range(7, 14)], default=[]) if show_u else []
selected_gr = st.sidebar.multiselect("Grades (Culture/Academics)", [f"Gr {i}" for i in range(1, 8)], default=[]) if show_gr else []

# ------------------ FILTER + SORT ------------------
res = []
for i in range(len(df)):
    cn = normalize_category(cat_s.iloc[i])

    # category filter
    if wanted and not ((cn == "sport" and "sport" in wanted) or
                       (cn == "culture" and "culture" in wanted) or
                       (cn == "academics" and "academics" in wanted)):
        continue

    # activity filter
    act_norm = normalize_activity(act_s.iloc[i])
    if selected_activities and act_norm not in selected_activities:
        continue

    # term docs mode (Full Term in K)
    term_flag = "full term" in str(dur_s.iloc[i]).strip().lower()

    d_raw = str(date_s.iloc[i]).strip()
    d_dt = parse_date_sa(d_raw)

    # hide yesterday if date exists
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
        # disappear on due date (today+ allowed)
        if d_dt and d_dt.date() < today:
            continue

    # Age/Grade filtering per row
    j_display, j_matches = format_j_for_row(cn, act_norm, j_s.iloc[i])

    if cn == "sport" and selected_u:
        if j_matches:
            if not any(x in selected_u for x in j_matches):
                continue
        else:
            if j_display and j_display not in selected_u:
                continue

    if cn in ["culture", "academics"] and selected_gr:
        if j_display and j_display not in selected_gr:
            continue

    title = build_title(cat_s.iloc[i], act_s.iloc[i], j_s.iloc[i], team_s.iloc[i])

    if search and search.lower().replace(" ", "") not in title.lower().replace(" ", ""):
        continue

    sort_dt = d_dt if d_dt else datetime(2099, 1, 1)
    res.append({"i": i, "dt": sort_dt, "title": title.lower(), "term": term_flag})

# Sort term docs first, then date, then title
term_items = sorted([x for x in res if x["term"]], key=lambda x: x["title"])
other_items = sorted([x for x in res if not x["term"]], key=lambda x: (x["dt"], x["title"]))
res_sorted = term_items + other_items

# ------------------ DISPLAY (NO QUICK INFO) ------------------
st.markdown("## 📅 Events")

if not res_sorted:
    st.info("Nothing matched your filters/search.")
else:
    for item in res_sorted:
        i = item["i"]
        cn = normalize_category(cat_s.iloc[i])
        is_academic = (cn == "academics")
        afr = is_afrikaans_subject(act_s.iloc[i])

        title = build_title(cat_s.iloc[i], act_s.iloc[i], j_s.iloc[i], team_s.iloc[i])

        # Date line (SA long)
        d_raw = str(date_s.iloc[i]).strip()
        date_line = format_date_long_sa(d_raw) if d_raw else ""

        # Venue conversion
        raw_ven = str(ven_s.iloc[i]).strip()
        ven_norm = normalize_venue(raw_ven)

        prog_link = clean_first_url(prog_s.iloc[i])
        team_val = str(teamlink_s.iloc[i]).strip()
        info_val = str(info_s.iloc[i]).strip()
        confirm_link = clean_first_url(confirm_s.iloc[i])

        # Button labels
        b_prog = "Documents" if is_academic else "Programme"
        b_team = "Team"
        b_info = "Information"
        b_confirm = "Confirm"

        if afr:
            if is_academic:
                b_prog = "Dokumente"
            b_info = "Inligting"

        # Venue line:
        venue_line = ""
        extra_prog_button = False
        if ven_norm == "SEE_PROGRAMME":
            extra_prog_button = True
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

        # Notes block (text only)
        notes_parts = []
        if ven_norm == "SEE_PROGRAMME":
            notes_parts.append("<b>Venue:</b><br>See programme")

        if team_val and not is_http(team_val):
            notes_parts.append(f"<b>{safe_txt(b_team)}:</b><br>{safe_txt(norm_gender_words(team_val))}")

        if info_val and not is_http(info_val):
            notes_parts.append(f"<b>{safe_txt(b_info)}:</b><br>{safe_txt(info_val.replace('_',' '))}")

        notes_block = f"<div class='noteBlock'>{'<br><br>'.join(notes_parts)}</div>" if notes_parts else ""

        # Buttons (links only)
        btns = []
        if prog_link and is_http(prog_link):
            btns.append((b_prog, prog_link))

        # Ensure programme button exists if venue says see programme
        if extra_prog_button and prog_link and is_http(prog_link):
            if not any(lbl.lower() == "programme" for lbl, _ in btns):
                btns.append(("Programme", prog_link))

        if team_val and is_http(team_val):
            btns.append((b_team, clean_first_url(team_val)))

        if info_val and is_http(info_val):
            btns.append((b_info, clean_first_url(info_val)))

        if confirm_link and is_http(confirm_link) and is_form_link(confirm_link):
            btns.append((b_confirm, confirm_link))

        btn_html = ""
        if btns:
            btn_html = "<div class='btnRow'>" + "".join(
                [f"<a class='btn' href='{u}' target='_blank'>{safe_txt(lbl)}</a>" for lbl, u in btns[:4]]
            ) + "</div>"

        st.markdown(f"""
<div class="card">
  <div class="card-title">{safe_txt(title)}</div>
  {f"<div class='meta'>📅 <b>{safe_txt(date_line)}</b></div>" if date_line else ""}
  {venue_line}
  {notes_block}
  {btn_html}
</div>
""", unsafe_allow_html=True)

st.markdown(
    "<br><center style='font-size:0.85rem;color:#94a3b8;'>LAERSKOOL MIDSTREAM COLLEGE PRIMARY Digital Hub 2026</center>",
    unsafe_allow_html=True
)

