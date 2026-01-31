import streamlit as st
import pandas as pd
import requests, io, re, pytz
from datetime import datetime

st.set_page_config(page_title="LMCP Hub", page_icon="📌", layout="wide")

# ✅ UPCOMING TAB (gid=37057995)
U = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

# ---------------- STYLE (MODERN) ----------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap');
html, body, [class*="css"] {font-family: 'Inter', sans-serif;}

:root{
  --card:#ffffff;
  --line:#e8edf5;
  --shadow:0 10px 30px rgba(0,0,0,.06);
  --maroon:#800000;
  --teal:#008080;
  --muted:#64748b;
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
  margin-bottom:16px;
}
.hero img{width:80px;border-radius:16px;}
.hero .title{font-weight:900;color:var(--maroon);font-size:1.45rem;line-height:1.1;}
.hero .sub{font-weight:800;color:var(--teal);margin-top:6px;font-size:1.05rem;}

.card{
  border:1px solid var(--line);
  background:var(--card);
  box-shadow:var(--shadow);
  border-radius:18px;
  padding:14px 14px 12px 14px;
  margin-bottom:14px;
  border-left:10px solid var(--maroon);
}
.card-title{
  font-weight:900;
  color:var(--maroon);
  font-size:1.15rem;
  line-height:1.2;
}
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
  display:inline-block;
  background:#008080;
  color:white !important;
  padding:9px 12px;
  border-radius:12px;
  font-weight:900;
  text-decoration:none;
  font-size:0.90rem;
}
.tealbtn:hover{opacity:0.92;}
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
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
def cl(v):
    return str(v).replace(".0", "").replace("nan", "").strip()

def safe_txt(x: str) -> str:
    s = str(x or "")
    return (s.replace("&","&amp;")
             .replace("<","&lt;")
             .replace(">","&gt;")
             .strip())

def is_http(u: str) -> bool:
    s = (u or "").strip().lower()
    return s.startswith("http://") or s.startswith("https://")

def is_form_link(u: str) -> bool:
    s = (u or "").lower()
    return ("forms.gle" in s) or ("docs.google.com/forms" in s)

def looks_like_html(txt: str) -> bool:
    s = (txt or "").lower()
    return ("<!doctype" in s) or ("<html" in s)

def format_date_long(ds: str) -> str:
    dt = pd.to_datetime(ds, dayfirst=True, errors="coerce")
    if pd.isnull(dt):
        return str(ds).strip()
    return f"{dt.day} {dt.strftime('%B %Y')}"

def split_label(label: str, is_academic: bool) -> str:
    s = (label or "").strip()
    if "/" not in s:
        return s
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

def find_col_by_header(df: pd.DataFrame, keywords: list[str]):
    # return column index or None
    cols = [str(c).strip().lower() for c in df.columns]
    for i, name in enumerate(cols):
        for k in keywords:
            if k in name:
                return i
    return None

# --- Translation (Afrikaans -> English) for sport/culture/other subjects on cards ---
AFR_EN = {
    "atletiek": "Athletics",
    "netbal": "Netball",
    "swem": "Swimming",
    "swemgala": "Swimming Gala",
    "gala": "Gala",
    "saal": "Hall",
    "veld": "Field",
    "wiskunde": "Math",
    "kultuur": "Culture",
    "sport": "Sport",
    "program": "Programme",
    "programme": "Programme",
    "toets": "Test",
    "assessering": "Assessment",
    "inligting": "Information",
    "dokumente": "Documents",
}

def tr_card_text(s: str, keep_afrikaans: bool) -> str:
    # If Afrikaans subject, keep Afrikaans words; else translate common Afrikaans terms
    if keep_afrikaans:
        return str(s or "").strip()

    txt = str(s or "").strip()

    # word-level replacements (case-insensitive)
    for k, v in AFR_EN.items():
        txt = re.sub(rf"\\b{k}\\b", v, txt, flags=re.I)

    # tidy spacing
    return re.sub(r"\\s+", " ", txt).strip()

# ---------------- LOAD DATA ----------------
@st.cache_data(ttl=60)
def load_upcoming(url: str):
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, timeout=25, headers=headers, allow_redirects=True)
    txt = r.text or ""
    meta = {
        "status_code": r.status_code,
        "content_type": r.headers.get("content-type", ""),
        "text_len": len(txt),
        "head_lines": "\n".join(txt.splitlines()[:3]),
    }
    if r.status_code != 200 or looks_like_html(txt) or len(txt) < 20:
        return pd.DataFrame(), meta

    df = pd.read_csv(io.StringIO(txt), dtype=str, engine="python", on_bad_lines="skip").fillna("")
    return df, meta

# ---------------- SIDEBAR ----------------
st.sidebar.markdown("## 🔎 Filters")
debug = st.sidebar.checkbox("Debug mode", value=False)
show_past = st.sidebar.checkbox("Show past events", value=False)
sq = st.sidebar.text_input("Search", placeholder="Type to filter...")

df, meta = load_upcoming(U)

if debug:
    st.sidebar.markdown("### Debug (load)")
    st.sidebar.write("Status:", meta["status_code"])
    st.sidebar.write("Content-Type:", meta["content_type"])
    st.sidebar.write("Text length:", meta["text_len"])
    st.sidebar.code(meta["head_lines"] if meta["head_lines"] else "(no content)")
    st.sidebar.write("Columns:", df.shape[1] if not df.empty else 0)
    if not df.empty:
        st.sidebar.write("Headers:", list(df.columns)[:12])

if df.empty:
    st.error("No data loaded from Google Sheet (CSV may be returning HTML or is empty).")
    st.stop()

# ---------------- COLUMN MAPPING ----------------
# Confirmed columns:
# B = Subject
# C = Category
# F = Programme/Documents link (button)
# G = Team link OR text
# H = Google Form link (optional button if not empty)
# I = Information (text or link)
# J = Grade/U value for heading prefix

subj_series = get_col_by_letter(df, "B", "")
cat_series  = get_col_by_letter(df, "C", "")
j_series    = get_col_by_letter(df, "J", "")

programme_series = get_col_by_letter(df, "F", "")
team_series      = get_col_by_letter(df, "G", "")
form_series      = get_col_by_letter(df, "H", "")
info_series      = get_col_by_letter(df, "I", "")

# Date / Venue: auto-detect by header keywords, else fallback to E and D
date_idx = find_col_by_header(df, ["date", "datum"])  # common
venue_idx = find_col_by_header(df, ["venue", "plek", "location", "lokasie"])

date_series  = get_col(df, date_idx, "") if date_idx is not None else get_col_by_letter(df, "E", "")
venue_series = get_col(df, venue_idx, "") if venue_idx is not None else get_col_by_letter(df, "D", "")

# Button headers (with / rule)
F_idx = col_letter_to_idx("F")
G_idx = col_letter_to_idx("G")
H_idx = col_letter_to_idx("H")
I_idx = col_letter_to_idx("I")

F_header = str(df.columns[F_idx]) if df.shape[1] > F_idx else "Programme / Documents"
G_header = str(df.columns[G_idx]) if df.shape[1] > G_idx else "Team"
H_header = str(df.columns[H_idx]) if df.shape[1] > H_idx else "Register"
I_header = str(df.columns[I_idx]) if df.shape[1] > I_idx else "Information / Inligting"

# ---------------- FILTER OPTIONS ----------------
st.sidebar.markdown("---")
# category options from data (normalized)
cat_opts = sorted({str(x).strip() for x in cat_series if str(x).strip()})
sc = st.sidebar.multiselect("Category", ["Sport", "Culture", "Academics"], default=[])

# subject options (optional)
subj_opts = sorted({str(x).strip() for x in subj_series if str(x).strip()})
ss = st.sidebar.multiselect("Subject", subj_opts, default=[])

tz = pytz.timezone("Africa/Johannesburg")
today = datetime.now(tz).date()

res, skipped = [], []
# ---------------- FILTER LOOP ----------------
for idx in range(len(df)):
    raw_cat = str(cat_series.iloc[idx]).lower().strip()
    # Programme counts as Sport
    cat_norm = "sport" if "programme" in raw_cat or "program" in raw_cat else raw_cat

    subject_raw = str(subj_series.iloc[idx]).strip()
    subject_lc = subject_raw.lower().strip()

    # Afrikaans subject rules:
    # - If Subject contains "afrikaans" OR is exactly "eat" OR "ht" => Afrikaans subject
    is_afrikaans_subject = ("afrikaans" in subject_lc) or (subject_lc == "eat") or (subject_lc == "ht")

    # normalize subject abbreviations
    if subject_lc == "eat":
        subject_show = "Afrikaans EAT"
    elif subject_lc == "ht":
        subject_show = "Afrikaans HT"
    else:
        subject_show = subject_raw

    # Determine academic/culture/sport
    is_academic = ("academic" in cat_norm) or ("academics" in cat_norm)
    is_culture = ("culture" in cat_norm) or ("kultuur" in cat_norm)
    is_sport = ("sport" in cat_norm)

    # Apply Subject filter
    if ss and subject_raw not in ss:
        if debug:
            skipped.append(("Subject filter", subject_raw, "", ""))
        continue

    # Date
    rd = cl(date_series.iloc[idx])
    dt = pd.to_datetime(rd, dayfirst=True, errors="coerce")
    if pd.isnull(dt):
        dt = datetime(2099, 1, 1)
    elif (not show_past) and dt.date() < today:
        if debug:
            skipped.append(("Past date", subject_raw, rd, ""))
        continue

    # Category filter selection (Sport/Culture/Academics)
    if sc:
        wanted = [x.lower() for x in sc]
        ok = False
        if "sport" in wanted and is_sport:
            ok = True
        if "culture" in wanted and is_culture:
            ok = True
        if "academics" in wanted and is_academic:
            ok = True
        if not ok:
            if debug:
                skipped.append(("Category filter", subject_raw, rd, cat_norm))
            continue

    res.append({"idx": idx, "dt": dt, "ds": rd})

res.sort(key=lambda x: x["dt"])

# ---------------- MAIN LAYOUT ----------------
left, right = st.columns([2.2, 1])

with right:
    st.markdown("### 📌 Quick Info")
    st.metric("Rows loaded", len(df))
    st.metric("Events after filters", len(res))

    if debug:
        with st.expander("Skipped (first 40)"):
            for item in skipped[:40]:
                st.write("•", item)

with left:
    st.markdown("## 📅 Upcoming Events")

    shown = 0
    if not res:
        st.info("No upcoming events found. Try loosening filters or enable 'Show past events'.")
    else:
        for item in res:
            idx = item["idx"]
            ds = item["ds"]

            raw_cat = str(cat_series.iloc[idx]).lower().strip()
            cat_norm = "sport" if "programme" in raw_cat or "program" in raw_cat else raw_cat

            subject_raw = str(subj_series.iloc[idx]).strip()
            subject_lc = subject_raw.lower().strip()

            is_afrikaans_subject = ("afrikaans" in subject_lc) or (subject_lc == "eat") or (subject_lc == "ht")
            if subject_lc == "eat":
                subject_show = "Afrikaans EAT"
            elif subject_lc == "ht":
                subject_show = "Afrikaans HT"
            else:
                subject_show = subject_raw

            is_academic = ("academic" in cat_norm) or ("academics" in cat_norm)
            is_culture = ("culture" in cat_norm) or ("kultuur" in cat_norm)
            is_sport = ("sport" in cat_norm)

            # J heading prefix rule
            j_val = cl(j_series.iloc[idx])
            if is_sport:
                j_show = f"U{j_val}" if j_val else ""
            else:
                # Academics and Culture
                j_show = f"Gr {j_val}" if j_val else ""

            # Card heading: Column B then J then C
            # Translate to English for non-Afrikaans subjects
            subject_card = tr_card_text(subject_show, keep_afrikaans=is_afrikaans_subject)
            cat_card = tr_card_text(str(cat_series.iloc[idx]).strip(), keep_afrikaans=is_afrikaans_subject)

            heading = " ".join([x for x in [subject_card, j_show, cat_card] if x]).strip()

            # Search filter
            if sq and sq.lower().replace(" ", "") not in heading.lower().replace(" ", ""):
                continue

            # Date line: 5 February 2026
            pretty_date = format_date_long(ds)

            # Venue drop pin (only if venue)
            ven = cl(venue_series.iloc[idx])
            venue_line = ""
            if ven:
                ven_show = tr_card_text(ven, keep_afrikaans=is_afrikaans_subject)
                map_url = f"https://www.google.com/maps/search/?api=1&query={ven.replace(' ','+')}+Midstream"
                venue_line = (
                    f"<div class='meta'>📍 "
                    f"<a href='{map_url}' target='_blank' style='color:#008080;font-weight:900;text-decoration:none;'>"
                    f"{safe_txt(ven_show).upper()}</a></div>"
                )

            # Links/Text columns
            prog_link = cl(programme_series.iloc[idx])   # F
            team_val  = cl(team_series.iloc[idx])        # G (link or text)
            form_link = cl(form_series.iloc[idx])        # H (google form link - optional)
            info_val  = cl(info_series.iloc[idx])        # I (link or text)

            # Button labels from headers (apply "/" rule)
            prog_btn_label = split_label(F_header, is_academic)
            team_btn_label = split_label(G_header, is_academic)
            info_btn_label = split_label(I_header, is_academic)
            form_btn_label = H_header.strip()  # link always applicable (no split needed)

            # Afrikaans subject: Documents/Dokumente, Information/Inligting
            # We keep the split logic but replace words accordingly.
            if is_afrikaans_subject:
                prog_btn_label = prog_btn_label.replace("Documents", "Dokumente").replace("documents", "Dokumente")
                info_btn_label = info_btn_label.replace("Information", "Inligting").replace("information", "Inligting")

            # Translate button labels if not Afrikaans subject (for Afrikaans words in headers)
            prog_btn_label = tr_card_text(prog_btn_label, keep_afrikaans=is_afrikaans_subject)
            team_btn_label = tr_card_text(team_btn_label, keep_afrikaans=is_afrikaans_subject)
            info_btn_label = tr_card_text(info_btn_label, keep_afrikaans=is_afrikaans_subject)
            form_btn_label = tr_card_text(form_btn_label, keep_afrikaans=is_afrikaans_subject)

            # Notes block inside card (only if text; no dropdown)
            notes_parts = []
            if team_val and (not is_http(team_val)):
                notes_parts.append(f"<b>{safe_txt(team_btn_label)}:</b><br>{safe_txt(tr_card_text(team_val, keep_afrikaans=is_afrikaans_subject))}")
            if info_val and (not is_http(info_val)):
                notes_parts.append(f"<b>{safe_txt(info_btn_label)}:</b><br>{safe_txt(tr_card_text(info_val, keep_afrikaans=is_afrikaans_subject))}")

            notes_block = ""
            if notes_parts:
                notes_block = f"<div class='noteBlock'>{'<br><br>'.join(notes_parts)}</div>"

            # Buttons (teal, next to each other). Only if link exists.
            btn_items = []
            if prog_link and is_http(prog_link):
                btn_items.append((prog_btn_label, prog_link))
            if team_val and is_http(team_val):
                btn_items.append((team_btn_label, team_val))
            if info_val and is_http(info_val):
                btn_items.append((info_btn_label, info_val))
            # Column H confirmed: if empty don't show; if link show (usually Google Form)
            if form_link and is_http(form_link) and is_form_link(form_link):
                btn_items.append((form_btn_label, form_link))

            btn_html = ""
            if btn_items:
                btn_html = "<div class='tealbtns'>" + "".join(
                    [f"<a class='tealbtn' href='{u}' target='_blank'>{safe_txt(lbl)}</a>" for lbl, u in btn_items[:4]]
                ) + "</div>"

            # Render card
            st.markdown(f"""
<div class="card">
  <div class="card-title">{safe_txt(heading)}</div>
  <div class="meta">📅 <b>{safe_txt(pretty_date)}</b></div>
  {venue_line}
  {notes_block}
  {btn_html}
</div>
""", unsafe_allow_html=True)

            shown += 1

    if shown == 0 and res:
        st.info("Nothing matched your search text. Clear the search box to see events.")

st.markdown(
    "<br><center style='font-size:0.85rem;color:#94a3b8;'>LAERSKOOL MIDSTREAM COLLEGE PRIMARY Digital Hub 2026</center>",
    unsafe_allow_html=True
)

