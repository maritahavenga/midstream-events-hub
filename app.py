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
  --bg:#f6f8fb;
  --card:#ffffff;
  --line:#e8edf5;
  --shadow:0 10px 30px rgba(0,0,0,.06);
  --maroon:#800000;
  --teal:#008080;
  --text:#0f172a;
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
.tags{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px;}
.tag{
  padding:5px 10px;border-radius:999px;
  font-weight:800;font-size:.80rem;
  background:rgba(0,128,128,.10);
  color:var(--teal);
}
.small-note{
  border:1px dashed var(--line);
  border-radius:14px;
  padding:10px 12px;
  margin-top:10px;
  color:#0f172a;
  background:#fbfdff;
}
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

def tr(t):
    t = str(t).replace("-", " ").replace("/", " ").strip()
    d = {"Saal":"Hall","Veld":"Field","Atletiek":"Athletics","Wiskunde":"Math","Netbal":"Netball"}
    for k, v in d.items():
        t = re.sub(rf"\\b{k}\\b", v, t, flags=re.I)
    return t

def c_a(n):
    n = str(n).lower()
    for x in ["hockey","rugby","netball","swimming","athletics","tennis"]:
        if x in n:
            return x.capitalize()
    if "eerste" in n: return "Afrikaans EAT"
    if "hooftaal" in n: return "Afrikaans HT"
    if "afrikaans" in n: return "Afrikaans"
    return n.capitalize()

def looks_like_html(txt: str) -> bool:
    s = (txt or "").lower()
    return ("<!doctype" in s) or ("<html" in s)

def get_col(df: pd.DataFrame, idx: int, default: str = "") -> pd.Series:
    # Safe positional getter: nooit IndexError nie
    if df is None or df.empty:
        return pd.Series([], dtype=str)
    if df.shape[1] > idx:
        return df.iloc[:, idx].astype(str)
    return pd.Series([default] * len(df), dtype=str)

@st.cache_data(ttl=60)
def load_upcoming(url: str):
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, timeout=20, headers=headers, allow_redirects=True)
    txt = r.text or ""

    meta = {
        "status_code": r.status_code,
        "content_type": r.headers.get("content-type", ""),
        "text_len": len(txt),
        "head_lines": "\n".join(txt.splitlines()[:3])
    }

    if r.status_code != 200 or looks_like_html(txt) or len(txt) < 20:
        return pd.DataFrame(), meta

    df = pd.read_csv(
        io.StringIO(txt),
        dtype=str,
        engine="python",
        on_bad_lines="skip"
    ).fillna("")
    return df, meta

# ---------------- SIDEBAR ----------------
st.sidebar.markdown("## 🔎 Filters")
debug = st.sidebar.checkbox("Debug mode", value=False)
show_past = st.sidebar.checkbox("Show past events", value=False)
sq = st.sidebar.text_input("Search", placeholder="Type e.g. Hockey, U10...")

# ---------------- LOAD ----------------
df, meta = load_upcoming(U)

if debug:
    st.sidebar.markdown("### Debug (load)")
    st.sidebar.write("Status:", meta["status_code"])
    st.sidebar.write("Content-Type:", meta["content_type"])
    st.sidebar.write("Text length:", meta["text_len"])
    st.sidebar.code(meta["head_lines"] if meta["head_lines"] else "(no content)")

if df.empty:
    st.error("No data loaded from Google Sheet (CSV link may be returning HTML or is empty).")
    if debug:
        st.write(meta)
    st.stop()

# ---------------- SAFE COLUMNS (BY POSITION) ----------------
# These are your original positions, but now safe if missing:
cat_series   = get_col(df, 2, "")
act_series   = get_col(df, 3, "")
extra_series = get_col(df, 4, "")
date_series  = get_col(df, 5, "")
venue_series = get_col(df, 6, "")
doc_series   = get_col(df, 7, "")
team_series  = get_col(df, 8, "")
info_series  = get_col(df, 10, "")
age_series   = get_col(df, 11, "")

# ---------------- FILTER OPTIONS ----------------
st.sidebar.markdown("---")
sc = st.sidebar.multiselect("Category", ["Sport", "Culture", "Academics"])
sa = st.sidebar.multiselect("Activity", sorted({c_a(x) for x in act_series}))
ao = ["Gr 1","Gr 2","Gr 3","Gr 4","Gr 5","Gr 6","Gr 7","U7","U8","U9","U10","U11","U12","U13"]
sg = st.sidebar.multiselect("Age Group", ao)

tz = pytz.timezone("Africa/Johannesburg")
today = datetime.now(tz).date()

res, skipped = [], []
# ---------------- FILTER LOOP ----------------
for idx in range(len(df)):
    cat = str(cat_series.iloc[idx]).lower().strip()
    act = str(act_series.iloc[idx]).strip()
    age = cl(age_series.iloc[idx])
    rd  = cl(date_series.iloc[idx])

    dt = pd.to_datetime(rd, dayfirst=True, errors="coerce")
    if pd.isnull(dt):
        dt = datetime(2099, 1, 1)
    elif (not show_past) and dt.date() < today:
        if debug: skipped.append(("Past date", act, rd, age))
        continue

    if sc and not any(x.lower() in cat for x in sc):
        if debug: skipped.append(("Category", act, rd, age))
        continue

    if sa and not any(x.lower() in act.lower() for x in sa):
        if debug: skipped.append(("Activity", act, rd, age))
        continue

    if sg and age:
        if not any(v.replace("Gr ", "").replace("U", "") in age for v in sg):
            if debug: skipped.append(("Age", act, rd, age))
            continue

    res.append({"idx": idx, "dt": dt, "ds": rd})

res.sort(key=lambda x: x["dt"])

# ---------------- MAIN LAYOUT ----------------
left, right = st.columns([2.2, 1])

with right:
    st.markdown("### 📌 Quick Info")
    st.markdown("- Use filters in the sidebar\n- Search works for U10 / Hockey\n- Turn on Debug if blank")
    st.markdown("---")
    st.metric("Rows loaded", len(df))
    st.metric("Events after filters", len(res))

    if debug:
        with st.expander("Skipped items (first 40)"):
            for reason, act, rd, age in skipped[:40]:
                st.write(f"• **{reason}** | {act} | {rd} | {age}")

with left:
    st.markdown("## 📅 Upcoming Events")

    shown = 0

    if not res:
        st.info("No upcoming events. Try loosening filters or enable 'Show past events'.")
    else:
        for item in res:
            idx = item["idx"]
            ds = item["ds"]

            act = str(act_series.iloc[idx]).strip()
            age = cl(age_series.iloc[idx])
            ven = cl(venue_series.iloc[idx])
            extra = cl(extra_series.iloc[idx])

            doc = cl(doc_series.iloc[idx])
            t_l = cl(team_series.iloc[idx])
            info = cl(info_series.iloc[idx])

            is_sport = any(x in act.lower() for x in ["hockey","rugby","netball","swimming","athletics","tennis"])
            age_lbl = (("U" if is_sport else "Gr ") + age) if age else ""

            title = f"{c_a(act)} {age_lbl} {tr(extra)}".strip()
            if sq and sq.lower().replace(" ", "") not in title.lower().replace(" ", ""):
                continue

            map_url = ""
            if ven:
                map_url = f"https://www.google.com/maps/search/?api=1&query={ven.replace(' ','+')}+Midstream"

            # MODERN CARD
            st.markdown(f"""
<div class="card">
  <div class="card-title">{title}</div>
  <div class="meta">📅 <b>{tr(ds)}</b></div>
  {f'<div class="meta">📍 <a href="{map_url}" target="_blank" style="color:#008080;font-weight:900;text-decoration:none;">{tr(ven).upper()}</a></div>' if ven else ''}
  <div class="tags">
    <span class="tag">{'SPORT' if is_sport else 'ACADEMICS / OTHER'}</span>
    {f'<span class="tag">{age_lbl}</span>' if age_lbl else ''}
  </div>
</div>
""", unsafe_allow_html=True)

            # Buttons row (native)
            b1, b2, b3 = st.columns(3)
            if doc and "http" in doc.lower():
                b1.link_button("📄 Documents", doc, use_container_width=True)
            if t_l and "http" in t_l.lower():
                b2.link_button("👥 Team/List", t_l, use_container_width=True)
            if info and "http" in info.lower():
                b3.link_button("ℹ️ Info", info, use_container_width=True)

            # Notes / Teams text (if not links)
            if (t_l and "http" not in t_l.lower()) or (info and "http" not in info.lower()):
                with st.expander("Notes / Teams", expanded=False):
                    if t_l and "http" not in t_l.lower():
                        st.markdown(f"<div class='small-note'><b>Teams:</b><br>{t_l}</div>", unsafe_allow_html=True)
                    if info and "http" not in info.lower():
                        st.markdown(f"<div class='small-note'><b>Note:</b><br>{info}</div>", unsafe_allow_html=True)

            st.write("")  # spacing
            shown += 1

    if shown == 0 and res:
        st.info("Nothing matched your search text. Clear the search box to see events.")

st.markdown(
    "<br><center style='font-size:0.85rem;color:#94a3b8;'>LAERSKOOL MIDSTREAM COLLEGE PRIMARY Digital Hub 2026</center>",
    unsafe_allow_html=True
)

