import streamlit as st
import pandas as pd
import requests, io, re, pytz, hashlib
from datetime import datetime, timedelta

st.set_page_config(page_title="LMCP Hub", page_icon="📌", layout="wide")

# ---- PASTE YOUR PUBLISHED CSV HERE ----
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

TZ = pytz.timezone("Africa/Johannesburg")

if not str(CSV_URL).strip().lower().startswith(("http://", "https://")):
    st.error("CSV link (CSV_URL) is missing or invalid. Paste the FULL https://...output=csv link into CSV_URL.")
    st.stop()

# ------------------ STYLE ------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap');
html, body, [class*="css"] {font-family: 'Inter', sans-serif;}
:root{
  --card:#ffffff; --line:#e8edf5; --shadow:0 10px 30px rgba(0,0,0,.06);
  --maroon:#800000; --teal:#008080; --muted:#64748b; --soft:#f3fbfb;
}
.block-container{padding-top:1rem;}
section[data-testid="stSidebar"]{border-right:1px solid var(--line);}

.hero{
  border:1px solid var(--line);
  background:linear-gradient(135deg,#fff, var(--soft));
  box-shadow:var(--shadow);
  border-radius:22px;
  padding:18px;
  display:flex;gap:16px;align-items:center;
  margin-bottom:10px;
}
.hero img{width:86px;border-radius:16px;}
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

st.markdown("""
<div class="hero">
  <img src="https://raw.githubusercontent.com/LMCPEventsHub/midstream-events-hub/main/LMCP_RGB%20(1).png">
  <div>
    <div class="title">LAERSKOOL MIDSTREAM COLLEGE PRIMARY</div>
    <div class="sub">Digital Hub</div>
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

def normalize_category(v: str) -> str:
    s = str(v or "").strip().lower()
    s = re.sub(r"\s+"," ",s)
    if "sport" in s or "programme" in s or "program" in s:
        return "sport"
    if "culture" in s or "kultuur" in s:
        return "culture"
    if "academic" in s or "academics" in s or "akadem" in s:
        return "academics"
    return s

def normalize_activity(v: str) -> str:
    s = str(v or "").strip().lower()
    s = re.sub(r"\s+"," ",s)

    # Afrikaans mappings (HT / EAT)
    if s in ["ht", "afrikaans ht"] or "hooftaal" in s:
        return "Afrikaans Hooftaal"
    if s in ["eat", "afrikaans eat"] or "eerste addisionele" in s:
        return "Afrikaans Eerste Addisionele Taal"

    # Athletics (and Atletiek)
    if "athletics" in s or "atletiek" in s:
        return "Athletics"

    # Common sport normalisation
    if "netbal" in s or "netball" in s:
        return "Netball"
    if "rugby" in s:
        return "Rugby"
    if "hockey" in s:
        return "Hockey"
    if "tennis" in s:
        return "Tennis"
    if "swimming" in s or "swem" in s or "gala" in s:
        return "Swimming"

    return s.title()

AFR_EN = {
    "atletiek":"Athletics","netbal":"Netball","swem":"Swimming","gala":"Gala",
    "saal":"Hall","veld":"Field","wiskunde":"Math","kultuur":"Culture",
    "inligting":"Information","dokumente":"Documents",
}
def tr_en_if_needed(text: str, keep_afrikaans: bool) -> str:
    if keep_afrikaans:
        return str(text or "").strip()
    t = str(text or "").strip()
    for k, v in AFR_EN.items():
        t = re.sub(rf"\b{k}\b", v, t, flags=re.I)
    return re.sub(r"\s+"," ",t).strip()

def parse_date_sa(s: str):
    d = pd.to_datetime(str(s), dayfirst=True, errors="coerce")
    return None if pd.isnull(d) else d.to_pydatetime()

def format_date_long_sa(s: str) -> str:
    dt = parse_date_sa(s)
    if not dt:
        return str(s or "").strip()
    return f"{dt.day} {dt.strftime('%B %Y')}"

def is_full_term(v: str) -> bool:
    s = str(v or "").strip().lower()
    return ("full term" in s) or (s == "full") or ("term" in s and "specific" not in s)

def clean_first_url(v: str) -> str:
    s = str(v or "").replace("\n"," ").strip()
    m = re.search(r"https?://\S+", s)
    return m.group(0) if m else s

@st.cache_data(ttl=60)
def load_csv(url: str):
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, timeout=25, headers=headers, allow_redirects=True)
    txt = r.text or ""
    if r.status_code != 200 or len(txt) < 20:
        return pd.DataFrame(), ""
    df = pd.read_csv(io.StringIO(txt), dtype=str, engine="python", on_bad_lines="skip").fillna("")
    return df, txt

# ------------------ SIDEBAR ------------------
st.sidebar.markdown("## 🧭 Navigation")
view_mode = st.sidebar.radio("View", ["Upcoming", "Next 7 Days", "Term"], horizontal=True)
category_choice = st.sidebar.multiselect("Category", ["Sport", "Culture", "Academics"], default=[])
search = st.sidebar.text_input("Search", placeholder="Type to filter...")
debug = st.sidebar.checkbox("Debug mode", value=False)

df, raw_txt = load_csv(CSV_URL)
if df.empty:
    st.error("No data loaded. Check your published CSV link.")
    st.stop()

now_dt = datetime.now(TZ)
today = now_dt.date()

# NEW UPDATE banner for 6 hours after CSV changes
current_hash = hashlib.sha256((raw_txt or "").encode("utf-8")).hexdigest()
if "prev_hash" not in st.session_state:
    st.session_state.prev_hash = current_hash
    st.session_state.last_change = None
elif current_hash != st.session_state.prev_hash:
    st.session_state.prev_hash = current_hash
    st.session_state.last_change = now_dt

if st.session_state.get("last_change") and (now_dt - st.session_state.last_change) <= timedelta(hours=6):
    st.markdown("""<div class="updateBanner"><span class="dot"></span> NEW UPDATE</div>""", unsafe_allow_html=True)

# Column mapping (0-based): A..K
A_CAT = 0
B_ACT = 1
C_GROUP = 2
D_DATE = 3
E_VEN = 4
F_PROG = 5
G_TEAM = 6
H_FORM = 7
I_INFO = 8
J_GRADEU = 9
K_DUR = 10

def col(i, default=""):
    if df.shape[1] > i:
        return df.iloc[:, i].astype(str)
    return pd.Series([default]*len(df), dtype=str)

cat_s = col(A_CAT)
act_s = col(B_ACT)
grp_s = col(C_GROUP)
date_s = col(D_DATE)
ven_s = col(E_VEN)
prog_s = col(F_PROG)
team_s = col(G_TEAM)
form_s = col(H_FORM)
info_s = col(I_INFO)
j_s = col(J_GRADEU)
dur_s = col(K_DUR)

# Activity options (normalized) limited by category selection
wanted = {c.lower() for c in category_choice} if category_choice else set()

def row_ok_cat(i: int) -> bool:
    if not wanted:
        return True
    cn = normalize_category(cat_s.iloc[i])
    return (("sport" in wanted and cn == "sport") or
            ("culture" in wanted and cn == "culture") or
            ("academics" in wanted and cn == "academics"))

act_opts = sorted({normalize_activity(act_s.iloc[i]) for i in range(len(df)) if act_s.iloc[i].strip() and row_ok_cat(i)})
selected_activities = st.sidebar.multiselect("Activity", act_opts, default=[])

# Age group nav: show only for sport selection, grades for academics mode
academics_mode = ("Academics" in category_choice)
if academics_mode:
    selected_grades = st.sidebar.multiselect("Grades", [f"Gr {i}" for i in range(1, 8)], default=[])
else:
    selected_ages = st.sidebar.multiselect("Age Groups", [f"U{i}" for i in range(7, 14)], default=[])

res = []
# ------------------ FILTER + SORT ------------------
for i in range(len(df)):
    cn = normalize_category(cat_s.iloc[i])

    is_sport = (cn == "sport")
    is_academic = (cn == "academics")
    is_culture = (cn == "culture")

    # Category filter (Column A)
    if category_choice:
        ok = (("Sport" in category_choice and is_sport) or
              ("Culture" in category_choice and is_culture) or
              ("Academics" in category_choice and is_academic))
        if not ok:
            continue

    # Activity filter (normalized)
    act_raw = act_s.iloc[i]
    act_norm = normalize_activity(act_raw)
    if selected_activities and act_norm not in selected_activities:
        continue

    # Afrikaans subject detection (Column B)
    act_lc = str(act_raw).strip().lower()
    is_afrikaans_subject = ("afrikaans" in act_lc) or (act_lc in ["ht", "eat"]) or ("hooftaal" in act_lc) or ("eerste addisionele" in act_lc)

    # J label: USE EXACTLY AS IN SHEET (Sport = U8, Academics/Culture = Gr 4)
    j_label = str(j_s.iloc[i]).strip()

    # Grade/Age filter uses J label now
    if academics_mode:
        if selected_grades and j_label not in selected_grades:
            continue
    else:
        if selected_ages and j_label not in selected_ages:
            continue

    # Date filtering (Column D) — SA parsing
    d_raw = str(date_s.iloc[i]).strip()
    d_dt = parse_date_sa(d_raw)

    term_flag = is_full_term(dur_s.iloc[i])

    # view_mode rules
    visible = True
    if view_mode == "Term":
        if not term_flag:
            visible = False
        else:
            if d_dt and today >= d_dt.date():
                visible = False  # disappear on due date
    else:
        if d_dt:
            if d_dt.date() < today:
                visible = False
            if view_mode == "Next 7 Days" and d_dt.date() > (today + timedelta(days=7)):
                visible = False
        else:
            if view_mode == "Next 7 Days":
                visible = False

    if not visible:
        continue

    # Title = Column B + Column J + Column C ONLY
    group_txt = tr_en_if_needed(grp_s.iloc[i], keep_afrikaans=is_afrikaans_subject)
    act_txt = tr_en_if_needed(act_norm, keep_afrikaans=is_afrikaans_subject)
    title = " ".join([x for x in [act_txt, j_label, group_txt] if x]).strip()

    if search and search.lower().replace(" ", "") not in title.lower().replace(" ", ""):
        continue

    res.append({
        "i": i,
        "dt": d_dt if d_dt else datetime(2099, 1, 1),
        "term": term_flag,
        "alpha": act_txt.lower()
    })

# Sort: Full Term on top (alphabetical), then by date, then alphabetical
term_items = sorted([x for x in res if x["term"]], key=lambda x: x["alpha"])
other_items = sorted([x for x in res if not x["term"]], key=lambda x: (x["dt"], x["alpha"]))
res_sorted = term_items + other_items

# ------------------ DISPLAY ------------------
left, right = st.columns([2.2, 1])

with right:
    st.markdown("### 📌 Quick Info")
    st.metric("Rows loaded", len(df))
    st.metric("Events shown", len(res_sorted))
    st.caption(f"View: **{view_mode}**")
    if debug:
        st.write("Columns:", df.shape[1])
        st.write("Headers:", list(df.columns))

with left:
    st.markdown("## 📅 Events")

    shown = 0
    for item in res_sorted:
        i = item["i"]
        cn = normalize_category(cat_s.iloc[i])
        is_sport = (cn == "sport")
        is_academic = (cn == "academics")

        act_raw = act_s.iloc[i]
        act_norm = normalize_activity(act_raw)
        act_lc = str(act_raw).strip().lower()
        is_afrikaans_subject = ("afrikaans" in act_lc) or (act_lc in ["ht", "eat"]) or ("hooftaal" in act_lc) or ("eerste addisionele" in act_lc)

        j_label = str(j_s.iloc[i]).strip()

        group_txt = tr_en_if_needed(grp_s.iloc[i], keep_afrikaans=is_afrikaans_subject)
        act_txt = tr_en_if_needed(act_norm, keep_afrikaans=is_afrikaans_subject)
        title = " ".join([x for x in [act_txt, j_label, group_txt] if x]).strip()

        # Date line (SA)
        d_raw = str(date_s.iloc[i]).strip()
        date_line = format_date_long_sa(d_raw) if d_raw else ""

        # Venue line
        ven = str(ven_s.iloc[i]).strip()
        venue_line = ""
        if ven:
            ven_show = tr_en_if_needed(ven, keep_afrikaans=is_afrikaans_subject)
            map_url = f"https://www.google.com/maps/search/?api=1&query={ven.replace(' ','+')}+Midstream"
            venue_line = (
                f"<div class='meta'>📍 "
                f"<a href='{map_url}' target='_blank' style='color:#008080;font-weight:900;text-decoration:none;'>"
                f"{safe_txt(ven_show).upper()}</a></div>"
            )

        # Links & Notes
        prog_link = clean_first_url(prog_s.iloc[i])
        team_val  = str(team_s.iloc[i]).strip()
        form_link = clean_first_url(form_s.iloc[i])
        info_val  = str(info_s.iloc[i]).strip()

        # Button labels
        b_prog = "Documents" if is_academic else "Programme"
        b_team = "Team"
        b_info = "Information"
        b_form = "Confirm"

        if is_afrikaans_subject:
            # If Afrikaans subject: Documents -> Dokumente, Information -> Inligting
            b_prog = "Dokumente" if is_academic else "Programme"
            b_info = "Inligting"

        # Notes block (only if text and not link)
        notes_parts = []
        if team_val and not is_http(team_val):
            notes_parts.append(f"<b>{safe_txt(b_team)}:</b><br>{safe_txt(tr_en_if_needed(team_val, keep_afrikaans=is_afrikaans_subject))}")
        if info_val and not is_http(info_val):
            notes_parts.append(f"<b>{safe_txt(b_info)}:</b><br>{safe_txt(tr_en_if_needed(info_val, keep_afrikaans=is_afrikaans_subject))}")

        notes_block = f"<div class='noteBlock'>{'<br><br>'.join(notes_parts)}</div>" if notes_parts else ""

        # Buttons row (links only)
        btns = []
        if prog_link and is_http(prog_link):
            btns.append((b_prog, prog_link))

        if team_val and is_http(team_val):
            btns.append((b_team, clean_first_url(team_val)))

        if info_val and is_http(info_val):
            btns.append((b_info, clean_first_url(info_val)))

        if form_link and is_http(form_link) and is_form_link(form_link):
            btns.append((b_form, form_link))

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

        shown += 1

    if shown == 0:
        st.info("Nothing matched your filters/search.")

st.markdown(
    "<br><center style='font-size:0.85rem;color:#94a3b8;'>LAERSKOOL MIDSTREAM COLLEGE PRIMARY Digital Hub 2026</center>",
    unsafe_allow_html=True
)

