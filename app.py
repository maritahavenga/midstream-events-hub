import streamlit as st
import pandas as pd
import requests, io, re, pytz, hashlib
from datetime import datetime, timedelta

st.set_page_config(page_title="LMCP Hub", page_icon="📌", layout="wide")

U = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

# ---------------- STYLE ----------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap');
html, body, [class*="css"] {font-family: 'Inter', sans-serif;}
:root{
  --card:#ffffff; --line:#e8edf5; --shadow:0 10px 30px rgba(0,0,0,.06);
  --maroon:#800000; --teal:#008080; --muted:#64748b;
}
.block-container{padding-top:1.0rem;}
section[data-testid="stSidebar"]{border-right:1px solid var(--line);}

.hero{
  border:1px solid var(--line);
  background:linear-gradient(135deg,#fff, #f3fbfb);
  box-shadow:var(--shadow);
  border-radius:22px;
  padding:18px 18px;
  display:flex;gap:16px;align-items:center;
  margin-bottom:10px;
}
.hero img{width:80px;border-radius:16px;}
.hero .title{font-weight:900;color:var(--maroon);font-size:1.45rem;line-height:1.1;}
.hero .sub{font-weight:800;color:var(--teal);margin-top:6px;font-size:1.05rem;}

.updateBanner{
  margin: 0 0 14px 0;
  border:1px solid rgba(0,128,128,0.30);
  background:rgba(0,128,128,0.08);
  padding:10px 12px;
  border-radius:14px;
  font-weight:900;
  color:#008080;
  display:flex;
  align-items:center;
  gap:10px;
}
.dot{width:10px;height:10px;border-radius:999px;background:#008080;animation:pulse 1.2s infinite;}
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
  margin-top:12px;
  padding:12px 12px;
  border-radius:14px;
  background:rgba(0,128,128,0.08);
  border:1px solid rgba(0,128,128,0.25);
  color:#0f172a;
  font-size:0.95rem;
  line-height:1.35;
}

.tealbtns{display:flex;gap:10px;flex-wrap:wrap;margin-top:12px;}
.tealbtn{
  display:inline-block;background:#008080;color:white !important;
  padding:9px 12px;border-radius:12px;font-weight:900;text-decoration:none;font-size:0.90rem;
}
.tealbtn:hover{opacity:0.92;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <img src="https://raw.githubusercontent.com/LMCPEventsHub/midstream-events-hub/main/LMCP_RGB%20(1).png">
  <div>
    <div class="title">LAERSKOOL MIDSTREAM COLLEGE PRIMARY</div>
    <div class="sub">Digital Hub</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ---------------- HELPERS ----------------
def cl(v): return str(v).replace(".0", "").replace("nan", "").strip()

def safe_txt(x: str) -> str:
    s = str(x or "")
    return (s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").strip())

def is_http(u: str) -> bool:
    s = (u or "").strip().lower()
    return s.startswith("http://") or s.startswith("https://")

def is_form_link(u: str) -> bool:
    s = (u or "").lower()
    return ("forms.gle" in s) or ("docs.google.com/forms" in s)

def looks_like_html(txt: str) -> bool:
    s = (txt or "").lower()
    return ("<!doctype" in s) or ("<html" in s)

def parse_date(s: str):
    d = pd.to_datetime(str(s), dayfirst=True, errors="coerce")
    return None if pd.isnull(d) else d.to_pydatetime()

def format_date_long(ds: str) -> str:
    dt = pd.to_datetime(ds, dayfirst=True, errors="coerce")
    if pd.isnull(dt):
        return str(ds).strip()
    return f"{dt.day} {dt.strftime('%B %Y')}"

def split_label(label: str, is_academic: bool) -> str:
    s = (label or "").strip()
    if "/" not in s: return s
    left, right = [p.strip() for p in s.split("/", 1)]
    return right if is_academic else left

def col_letter_to_idx(letter: str) -> int:
    return ord(letter.upper()) - ord("A")

def get_col(df: pd.DataFrame, idx: int, default: str = "") -> pd.Series:
    if df is None or df.empty:
        return pd.Series([], dtype=str)
    if df.shape[1] > idx:
        return df.iloc[:, idx].astype(str)
    return pd.Series([default] * len(df), dtype=str)

def get_col_by_letter(df: pd.DataFrame, letter: str, default: str = "") -> pd.Series:
    return get_col(df, col_letter_to_idx(letter), default)

def normalize_category(raw_cat: str) -> str:
    s = (raw_cat or "").lower().strip()
    s = re.sub(r"\s+", " ", s)
    if "programme" in s or "program" in s:
        return "sport"
    if "culture" in s or "kultuur" in s:
        return "culture"
    if "academic" in s or "academics" in s or "akadem" in s:
        return "academics"
    if "sport" in s:
        return "sport"
    return s

AFR_EN = {
    "atletiek":"Athletics","netbal":"Netball","swem":"Swimming","gala":"Gala",
    "saal":"Hall","veld":"Field","wiskunde":"Math","kultuur":"Culture",
    "program":"Programme","programme":"Programme","assessering":"Assessment",
    "inligting":"Information","dokumente":"Documents",
}

def tr_card_text(s: str, keep_afrikaans: bool) -> str:
    if keep_afrikaans:
        return str(s or "").strip()
    txt = str(s or "").strip()
    for k, v in AFR_EN.items():
        txt = re.sub(rf"\\b{k}\\b", v, txt, flags=re.I)
    return re.sub(r"\\s+", " ", txt).strip()

GR_TO_U = {"1":"7","2":"8","3":"9","4":"10","5":"11","6":"12","7":"13"}
def normalize_grade(s: str) -> str:
    t = (s or "").lower().replace("grade","").replace("gr","").replace(".","").strip()
    t = re.sub(r"\\s+","",t)
    return t
def normalize_u(s: str) -> str:
    t = (s or "").lower().replace("u","").replace("under","").strip()
    t = re.sub(r"\\s+","",t)
    return t

# ---------------- LOAD DATA ----------------
@st.cache_data(ttl=60)
def load_upcoming(url: str):
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, timeout=25, headers=headers, allow_redirects=True)
    txt = r.text or ""
    meta = {"status_code": r.status_code, "content_type": r.headers.get("content-type",""), "text_len": len(txt)}
    if r.status_code != 200 or looks_like_html(txt) or len(txt) < 20:
        return pd.DataFrame(), meta, ""
    df = pd.read_csv(io.StringIO(txt), dtype=str, engine="python", on_bad_lines="skip").fillna("")
    return df, meta, txt

# ---------------- SIDEBAR ----------------
st.sidebar.markdown("## 🧭 Navigation")
debug = st.sidebar.checkbox("Debug mode", value=False)

tz = pytz.timezone("Africa/Johannesburg")
now_dt = datetime.now(tz)
today = now_dt.date()

df, meta, raw_txt = load_upcoming(U)
if df.empty:
    st.error("No data loaded from Google Sheet.")
    st.stop()

# NEW UPDATE banner (6h)
current_hash = hashlib.sha256((raw_txt or "").encode("utf-8")).hexdigest()
if "prev_hash" not in st.session_state:
    st.session_state.prev_hash = current_hash
    st.session_state.last_change = None
else:
    if current_hash != st.session_state.prev_hash:
        st.session_state.prev_hash = current_hash
        st.session_state.last_change = now_dt

if st.session_state.get("last_change") and (now_dt - st.session_state.last_change) <= timedelta(hours=6):
    st.markdown("""<div class="updateBanner"><span class="dot"></span> NEW UPDATE</div>""", unsafe_allow_html=True)

view_mode = st.sidebar.radio("View", ["Upcoming", "Next 7 Days", "Term"], horizontal=True)
sq = st.sidebar.text_input("Search", placeholder="Type to filter...")

if debug:
    st.sidebar.write("Columns:", df.shape[1])
    st.sidebar.write("Headers:", list(df.columns))

# ---------------- COLUMN MAPPING (LOCKED) ----------------
# Activity = B, Category = C, Date = D, Venue = E, Programme = F, Team = G, Form = H, Info = I, J = Grade/U, K = Duration
act_series  = get_col_by_letter(df, "B", "")   # ✅ Activity
cat_series  = get_col_by_letter(df, "C", "")
date_series = get_col_by_letter(df, "D", "")   # ✅ event/due date
ven_series  = get_col_by_letter(df, "E", "")   # ✅ venue
j_series    = get_col_by_letter(df, "J", "")
duration_series = get_col_by_letter(df, "K", "")

programme_series = get_col_by_letter(df, "F", "")
team_series      = get_col_by_letter(df, "G", "")
form_series      = get_col_by_letter(df, "H", "")
info_series      = get_col_by_letter(df, "I", "")

# Button headers with "/" rule
F_idx = col_letter_to_idx("F"); G_idx = col_letter_to_idx("G"); H_idx = col_letter_to_idx("H"); I_idx = col_letter_to_idx("I")
F_header = str(df.columns[F_idx]) if df.shape[1] > F_idx else "Programme / Documents"
G_header = str(df.columns[G_idx]) if df.shape[1] > G_idx else "Team"
H_header = str(df.columns[H_idx]) if df.shape[1] > H_idx else "Register"
I_header = str(df.columns[I_idx]) if df.shape[1] > I_idx else "Information / Inligting"

# Filters
st.sidebar.markdown("---")
category_choice = st.sidebar.multiselect("Category", ["Sport", "Culture", "Academics"], default=[])
academics_mode = ("Academics" in category_choice)

act_opts = sorted({str(x).strip() for x in act_series if str(x).strip()})
selected_activities = st.sidebar.multiselect("Activity", act_opts, default=[])

selected_grades = []
selected_ages = []
if academics_mode:
    grade_opts = [f"Gr {i}" for i in range(1, 8)]
    selected_grades = st.sidebar.multiselect("Grades", grade_opts, default=[])
else:
    age_opts = [f"U{i}" for i in range(7, 14)]
    selected_ages = st.sidebar.multiselect("Age Groups", age_opts, default=[])

res = []
# ---------------- FILTER LOOP ----------------
for idx in range(len(df)):
    cat_norm = normalize_category(str(cat_series.iloc[idx]))
    is_academic = (cat_norm == "academics")
    is_sport = (cat_norm == "sport")
    is_culture = (cat_norm == "culture")

    # Category selection filter
    if category_choice:
        wanted = [x.lower() for x in category_choice]
        ok = False
        if "academics" in wanted and is_academic: ok = True
        if "sport" in wanted and is_sport: ok = True
        if "culture" in wanted and is_culture: ok = True
        if not ok:
            continue

    # Activity filter (B)
    act_raw = str(act_series.iloc[idx]).strip()
    if selected_activities and act_raw not in selected_activities:
        continue

    # Afrikaans subject rules now based on activity text (because B is activity)
    act_lc = act_raw.lower().strip()
    is_afrikaans_subject = ("afrikaans" in act_lc) or (act_lc in ["eat", "ht"]) or ("afrikaans eat" in act_lc) or ("afrikaans ht" in act_lc)

    if act_lc in ["eat", "afrikaans eat", "afrikaans e.a.t", "afrikaans e.a.t."]:
        act_show = "Afrikaans Eerste Addisionele Taal"
        is_afrikaans_subject = True
    elif act_lc in ["ht", "afrikaans ht"]:
        act_show = "Afrikaans Hooftaal"
        is_afrikaans_subject = True
    else:
        act_show = act_raw

    # Grade / Age filters use J
    jv = cl(j_series.iloc[idx])
    if academics_mode:
        if selected_grades:
            g = normalize_grade(jv)
            if not g:
                continue
            if f"Gr {g}" not in selected_grades:
                continue
    else:
        if selected_ages:
            u = normalize_u(jv)
            if not u:
                g = normalize_grade(jv)
                if g and g in GR_TO_U:
                    u = GR_TO_U[g]
            if not u:
                continue
            if f"U{u}" not in selected_ages:
                continue

    # Date (D) for filtering
    d_raw = cl(date_series.iloc[idx])
    d_dt = parse_date(d_raw)

    duration = str(duration_series.iloc[idx]).lower().strip()
    is_full_term = ("full" in duration) or ("term" in duration)

    # View filter
    visible = True
    if view_mode == "Term":
        if not is_full_term:
            visible = False
        else:
            if d_dt and today >= d_dt.date():
                visible = False  # disappear on due date
    else:
        if d_dt:
            if d_dt.date() < today:
                visible = False  # hide yesterday and older
            if view_mode == "Next 7 Days" and d_dt.date() > (today + timedelta(days=7)):
                visible = False
        else:
            # no date -> hide for Next 7 Days
            if view_mode == "Next 7 Days":
                visible = False

    if not visible:
        continue

    res.append({
        "idx": idx,
        "is_full_term": is_full_term,
        "dt": d_dt if d_dt else datetime(2099, 1, 1),
        "a_sort": act_raw.lower().strip()  # alphabetical uses Activity now
    })

# ---------------- SORTING ----------------
term_items = [x for x in res if x["is_full_term"]]
other_items = [x for x in res if not x["is_full_term"]]

term_items.sort(key=lambda x: x["a_sort"])
other_items.sort(key=lambda x: (x["dt"], x["a_sort"]))
res_sorted = term_items + other_items

# ---------------- MAIN LAYOUT ----------------
left, right = st.columns([2.2, 1])

with right:
    st.markdown("### 📌 Quick Info")
    st.metric("Rows loaded", len(df))
    st.metric("Events shown", len(res_sorted))
    st.caption(f"View: **{view_mode}**")

with left:
    st.markdown("## 📅 Events")

    shown = 0
    for item in res_sorted:
        idx = item["idx"]

        cat_norm = normalize_category(str(cat_series.iloc[idx]))
        is_academic = (cat_norm == "academics")
        is_sport = (cat_norm == "sport")
        is_culture = (cat_norm == "culture")

        # Activity (B) display
        act_raw = str(act_series.iloc[idx]).strip()
        act_lc = act_raw.lower().strip()

        is_afrikaans_subject = ("afrikaans" in act_lc) or (act_lc in ["eat", "ht"]) or ("afrikaans eat" in act_lc) or ("afrikaans ht" in act_lc)
        if act_lc in ["eat", "afrikaans eat", "afrikaans e.a.t", "afrikaans e.a.t."]:
            act_show = "Afrikaans Eerste Addisionele Taal"
            is_afrikaans_subject = True
        elif act_lc in ["ht", "afrikaans ht"]:
            act_show = "Afrikaans Hooftaal"
            is_afrikaans_subject = True
        else:
            act_show = act_raw

        jv = cl(j_series.iloc[idx])
        if is_sport:
            j_show = f"U{normalize_u(jv) or jv}" if jv else ""
        else:
            g = normalize_grade(jv) or jv
            j_show = f"Gr {g}" if g else ""

        # Heading: in academics mode we still show "subject-first" meaning: Activity first is OK now
        # Since B is Activity, we keep it consistent:
        act_card = tr_card_text(act_show, keep_afrikaans=is_afrikaans_subject)
        cat_card = tr_card_text(str(cat_series.iloc[idx]).strip(), keep_afrikaans=is_afrikaans_subject)
        heading = " ".join([x for x in [act_card, j_show, cat_card] if x]).strip()

        if sq and sq.lower().replace(" ", "") not in heading.lower().replace(" ", ""):
            continue

        # Date line from D
        d_raw = cl(date_series.iloc[idx])
        date_line = format_date_long(d_raw) if d_raw else ""

        # Venue from E
        ven = cl(ven_series.iloc[idx])
        venue_line = ""
        if ven:
            ven_show = tr_card_text(ven, keep_afrikaans=is_afrikaans_subject)
            map_url = f"https://www.google.com/maps/search/?api=1&query={ven.replace(' ','+')}+Midstream"
            venue_line = (
                f"<div class='meta'>📍 "
                f"<a href='{map_url}' target='_blank' style='color:#008080;font-weight:900;text-decoration:none;'>"
                f"{safe_txt(ven_show).upper()}</a></div>"
            )

        # Buttons + notes
        prog_link = cl(programme_series.iloc[idx])   # F
        team_val  = cl(team_series.iloc[idx])        # G
        form_link = cl(form_series.iloc[idx])        # H
        info_val  = cl(info_series.iloc[idx])        # I

        prog_btn_label = split_label(F_header, is_academic)
        team_btn_label = split_label(G_header, is_academic)
        info_btn_label = split_label(I_header, is_academic)
        form_btn_label = H_header.strip()

        if is_afrikaans_subject:
            prog_btn_label = prog_btn_label.replace("Documents", "Dokumente").replace("documents", "Dokumente")
            info_btn_label = info_btn_label.replace("Information", "Inligting").replace("information", "Inligting")

        prog_btn_label = tr_card_text(prog_btn_label, keep_afrikaans=is_afrikaans_subject)
        team_btn_label = tr_card_text(team_btn_label, keep_afrikaans=is_afrikaans_subject)
        info_btn_label = tr_card_text(info_btn_label, keep_afrikaans=is_afrikaans_subject)
        form_btn_label = tr_card_text(form_btn_label, keep_afrikaans=is_afrikaans_subject)

        notes_parts = []
        if team_val and (not is_http(team_val)):
            notes_parts.append(f"<b>{safe_txt(team_btn_label)}:</b><br>{safe_txt(tr_card_text(team_val, keep_afrikaans=is_afrikaans_subject))}")
        if info_val and (not is_http(info_val)):
            notes_parts.append(f"<b>{safe_txt(info_btn_label)}:</b><br>{safe_txt(tr_card_text(info_val, keep_afrikaans=is_afrikaans_subject))}")

        notes_block = ""
        if notes_parts:
            notes_block = f"<div class='noteBlock'>{'<br><br>'.join(notes_parts)}</div>"

        btn_items = []
        if prog_link and is_http(prog_link):
            btn_items.append((prog_btn_label, prog_link))
        if team_val and is_http(team_val):
            btn_items.append((team_btn_label, team_val))
        if info_val and is_http(info_val):
            btn_items.append((info_btn_label, info_val))
        if form_link and is_http(form_link) and is_form_link(form_link):
            btn_items.append((form_btn_label, form_link))

        btn_html = ""
        if btn_items:
            btn_html = "<div class='tealbtns'>" + "".join(
                [f"<a class='tealbtn' href='{u}' target='_blank'>{safe_txt(lbl)}</a>" for lbl, u in btn_items[:4]]
            ) + "</div>"

        st.markdown(f"""
<div class="card">
  <div class="card-title">{safe_txt(heading)}</div>
  {f"<div class='meta'>📅 <b>{safe_txt(date_line)}</b></div>" if date_line else ""}
  {venue_line}
  {notes_block}
  {btn_html}
</div>
""", unsafe_allow_html=True)

        shown += 1

    if shown == 0:
        st.info("Nothing matched your filters/search.")

st.markdown(
    "<br><center style='font-size:0.85rem;color:#94a3b8;'>LAERSKOOL MIDSTREAM COLLEGE PRIMARY Digital Hub 2026</center>",
    unsafe_allow_html=True
)

