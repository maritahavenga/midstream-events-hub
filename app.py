import streamlit as st
import pandas as pd
import requests, io, re, pytz, hashlib
from datetime import datetime, timedelta

st.set_page_config(page_title="LMCP Hub", page_icon="📌", layout="wide")

# ✅ PASTE your published CSV link here
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

TZ = pytz.timezone("Africa/Johannesburg")

if not str(CSV_URL).strip().lower().startswith(("http://", "https://")):
    st.error("CSV_URL is missing or invalid. Paste the FULL https://...output=csv link.")
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

def clean_first_url(v: str) -> str:
    s = str(v or "").replace("\n"," ").strip()
    m = re.search(r"https?://\S+", s)
    return m.group(0) if m else s

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
    s = re.sub(r"\s+"," ", s)

    # Afrikaans subjects
    if s in ["ht", "afrikaans ht"] or "hooftaal" in s:
        return "Afrikaans Hooftaal"
    if s in ["eat", "afrikaans eat"] or "eerste addisionele" in s:
        return "Afrikaans Eerste Addisionele Taal"

    # Sport normalization
    if "athletics" in s or "atletiek" in s:
        return "Athletics"
    if "swimming" in s or "swem" in s or "gala" in s:
        return "Swimming"
    if "tennis" in s:
        return "Tennis"
    if "rugby" in s:
        return "Rugby"
    if "hockey" in s:
        return "Hockey"
    if "netbal" in s or "netball" in s:
        return "Netball"

    return s.title()

# Gender / team words in C (and if it appears in B)
def norm_gender_words(text: str) -> str:
    s = str(text or "").strip()
    s = re.sub(r"\bmeisies\b", "Girls", s, flags=re.I)
    s = re.sub(r"\bseuns\b", "Boys", s, flags=re.I)
    s = re.sub(r"\bgirls\b", "Girls", s, flags=re.I)
    s = re.sub(r"\bboys\b", "Boys", s, flags=re.I)
    # single letter tokens
    s = re.sub(r"\bB\b", "Boys", s)
    s = re.sub(r"\bG\b", "Girls", s)
    return re.sub(r"\s+"," ", s).strip()

def format_j_with_prefix(category_norm: str, j_raw: str) -> str:
    """
    A=Sport => U + J (no space).
    A=Academics/Culture => Gr + J (no space).
    If sport and J is 10-13 => U10-U13.
    If J already starts with U or Gr, keep it (just remove spaces).
    """
    j = str(j_raw or "").strip()
    if not j:
        return ""

    j_clean = j.replace(" ", "")

    if category_norm == "sport":
        nums = re.findall(r"\d+", j_clean)
        if "-" in j_clean and len(nums) >= 2:
            return f"U{nums[0]}-U{nums[1]}"
        if j_clean.lower().startswith("u"):
            return j_clean
        return f"U{j_clean}"

    # academics / culture
    if j_clean.lower().startswith("gr"):
        return j_clean
    return f"Gr{j_clean}"

def build_card_title(cat_value: str, b_value: str, j_value: str, c_value: str) -> str:
    """
    Title format:
      B + space + (U/Gr + J no space) + (C with NO space before C)
    Example:
      Tennis U13B Girls
    """
    cn = normalize_category(cat_value)
    b_txt = norm_gender_words(normalize_activity(b_value))
    c_txt = norm_gender_words(str(c_value or "").strip()).lstrip()
    j_txt = format_j_with_prefix(cn, j_value)

    if j_txt:
        return f"{b_txt} {j_txt}{c_txt}".strip()
    return f"{b_txt} {c_txt}".strip()

def is_afrikaans_subject(b_raw: str) -> bool:
    s = str(b_raw or "").strip().lower()
    return ("afrikaans" in s) or (s in ["ht", "eat"]) or ("hooftaal" in s) or ("eerste addisionele" in s)

# ---- HARD CODE DATE PARSING (SA) ----
def parse_date_sa(s):
    """
    Robust SA parser:
    - dd/mm/yyyy (day-first)
    - month names
    - Excel serials
    """
    if s is None:
        return None
    raw = str(s).strip()
    if raw == "" or raw.lower() in ["nan", "none"]:
        return None

    # Excel serials (e.g. 45234)
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
    if not pd.isnull(d):
        return d.to_pydatetime()

    d2 = pd.to_datetime(cleaned, dayfirst=False, errors="coerce")
    if not pd.isnull(d2):
        return d2.to_pydatetime()

    return None

def format_date_long_sa(s) -> str:
    dt = parse_date_sa(s)
    if not dt:
        return str(s or "").strip()
    return f"{dt.day} {dt.strftime('%B %Y')}"

@st.cache_data(ttl=60)
def load_csv(url: str):
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, timeout=25, headers=headers, allow_redirects=True)
    txt = r.text or ""
    if r.status_code != 200 or len(txt) < 20 or "<html" in txt.lower():
        return pd.DataFrame(), txt
    df = pd.read_csv(io.StringIO(txt), dtype=str, engine="python", on_bad_lines="skip").fillna("")
    return df, txt

# ------------------ SIDEBAR ------------------
st.sidebar.markdown("## 🧭 Navigation")
view_mode = st.sidebar.radio("View", ["Upcoming", "Next 7 Days"], horizontal=True)
category_choice = st.sidebar.multiselect("Category", ["Sport", "Culture", "Academics"], default=[])
search = st.sidebar.text_input("Search", placeholder="Type to filter...")

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

# Column mapping (0-based): A..K (YOUR SHEET)
A_CAT = 0   # Category
B_ACT = 1   # Activity/Subject
C_TEAM = 2  # Team / Assessment
D_DATE = 3  # Date / Due Date
E_VEN = 4   # Venue
F_PROG = 5  # Programme / Documents link
G_TEAMLINK = 6  # Team link (or text)
H_CONFIRM = 7   # Confirm (Google Form link)
I_INFO = 8      # Information (text or link)
J_GRADEU = 9    # U8 or Gr 4 (or blank)
K_DUR = 10      # optional (not used here)

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

# Activity options for filter
act_opts = sorted({normalize_activity(act_s.iloc[i]) for i in range(len(df)) if str(act_s.iloc[i]).strip()})
selected_activities = st.sidebar.multiselect("Activity", act_opts, default=[])

res = []
# ------------------ FILTER + SORT ------------------
wanted = {c.lower() for c in category_choice} if category_choice else set()

for i in range(len(df)):
    cn = normalize_category(cat_s.iloc[i])

    # Category filter
    if wanted:
        if not ((cn == "sport" and "sport" in wanted) or
                (cn == "culture" and "culture" in wanted) or
                (cn == "academics" and "academics" in wanted)):
            continue

    # Activity filter (normalized)
    act_norm = normalize_activity(act_s.iloc[i])
    if selected_activities and act_norm not in selected_activities:
        continue

    # Date logic: show today and future; hide yesterday
    d_raw = str(date_s.iloc[i]).strip()
    d_dt = parse_date_sa(d_raw)

    # If date exists, enforce today/future (for Next 7 Days too)
    if d_dt:
        if d_dt.date() < today:
            continue
        if view_mode == "Next 7 Days" and d_dt.date() > (today + timedelta(days=7)):
            continue
    else:
        # If no date, keep it in Upcoming, but not in Next 7 Days
        if view_mode == "Next 7 Days":
            continue

    # Build title EXACTLY as requested
    title = build_card_title(cat_s.iloc[i], act_s.iloc[i], j_s.iloc[i], team_s.iloc[i])

    # Search filter
    if search and search.lower().replace(" ", "") not in title.lower().replace(" ", ""):
        continue

    res.append({"i": i, "dt": d_dt if d_dt else datetime(2099, 1, 1), "title": title.lower()})

# Sort by date then title
res_sorted = sorted(res, key=lambda x: (x["dt"], x["title"]))

# ------------------ DISPLAY ------------------
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
        i = item["i"]

        cn = normalize_category(cat_s.iloc[i])
        is_academic = (cn == "academics")
        afr = is_afrikaans_subject(act_s.iloc[i])

        title = build_card_title(cat_s.iloc[i], act_s.iloc[i], j_s.iloc[i], team_s.iloc[i])

        # Date line (hard-coded SA format)
        d_raw = str(date_s.iloc[i]).strip()
        date_line = format_date_long_sa(d_raw) if d_raw else ""

        # Venue pin
        ven = str(ven_s.iloc[i]).strip()
        venue_line = ""
        if ven:
            map_url = f"https://www.google.com/maps/search/?api=1&query={ven.replace(' ','+')}+Midstream"
            venue_line = (
                f"<div class='meta'>📍 "
                f"<a href='{map_url}' target='_blank' style='color:#008080;font-weight:900;text-decoration:none;'>"
                f"{safe_txt(ven).upper()}</a></div>"
            )

        # Links & Notes
        prog_link = clean_first_url(prog_s.iloc[i])
        team_val = str(teamlink_s.iloc[i]).strip()
        confirm_link = clean_first_url(confirm_s.iloc[i])
        info_val = str(info_s.iloc[i]).strip()

        # Button labels
        b_prog = "Documents" if is_academic else "Programme"
        b_team = "Team"
        b_info = "Information"
        b_confirm = "Confirm"

        if afr:
            if is_academic:
                b_prog = "Dokumente"
            b_info = "Inligting"

        # Notes block (only if text and not link)
        notes_parts = []
        if team_val and not is_http(team_val):
            notes_parts.append(f"<b>{safe_txt(b_team)}:</b><br>{safe_txt(norm_gender_words(team_val))}")
        if info_val and not is_http(info_val):
            notes_parts.append(f"<b>{safe_txt(b_info)}:</b><br>{safe_txt(info_val)}")

        notes_block = f"<div class='noteBlock'>{'<br><br>'.join(notes_parts)}</div>" if notes_parts else ""

        # Buttons row (links only)
        btns = []
        if prog_link and is_http(prog_link):
            btns.append((b_prog, prog_link))
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

        shown += 1

    if shown == 0:
        st.info("Nothing matched your filters/search.")

st.markdown(
    "<br><center style='font-size:0.85rem;color:#94a3b8;'>LAERSKOOL MIDSTREAM COLLEGE PRIMARY Digital Hub 2026</center>",
    unsafe_allow_html=True
)

