import streamlit as st
import pandas as pd
import requests, io, re, pytz
from datetime import datetime

st.set_page_config(page_title="LMCP Hub", page_icon="📌", layout="wide")

# ✅ UPCOMING TAB (gid=37057995)
U = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

# ---------- STYLE ----------
st.markdown("""
<style>
:root{--maroon:#800000;--teal:#008080;--line:#e9edf3;}
.block-container{padding-top:1.0rem;}
.banner{
  display:flex;gap:16px;align-items:center;
  background:linear-gradient(135deg,#ffffff, #f7fbfb);
  border:1px solid var(--line);
  border-radius:18px;padding:16px 18px;margin-bottom:14px;
}
.card{
  background:white;border:1px solid var(--line);
  border-left:10px solid var(--maroon);
  border-radius:16px;padding:14px 14px 12px 14px;
  box-shadow:0 6px 18px rgba(0,0,0,0.05);
  margin-bottom:12px;
}
.title{font-size:1.12rem;font-weight:900;color:var(--maroon);line-height:1.2;}
.meta{color:#4b5563;margin-top:6px;font-size:0.95rem;}
.pills{margin-top:10px;display:flex;gap:8px;flex-wrap:wrap;}
.pill{
  display:inline-block;padding:4px 10px;border-radius:999px;
  background:rgba(0,128,128,0.10);color:var(--teal);
  font-weight:800;font-size:0.82rem;
}
</style>
""", unsafe_allow_html=True)

# ---------- BANNER ----------
st.markdown("""
<div class="banner">
  <img src="https://raw.githubusercontent.com/LMCPEventsHub/midstream-events-hub/main/LMCP_RGB%20(1).png"
       style="width:76px;height:auto;border-radius:12px;">
  <div>
    <div style="font-weight:950;color:#800000;font-size:1.35rem;line-height:1.1;">
      LAERSKOOL MIDSTREAM COLLEGE PRIMARY
    </div>
    <div style="color:#008080;font-size:1.05rem;font-weight:800;margin-top:4px;">
      Digital Hub
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ---------- HELPERS ----------
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
    if "eerste" in n:
        return "Afrikaans EAT"
    if "hooftaal" in n:
        return "Afrikaans HT"
    if "afrikaans" in n:
        return "Afrikaans"
    return n.capitalize()

def looks_like_html(txt: str) -> bool:
    s = (txt or "").lower()
    return ("<!doctype" in s) or ("<html" in s)

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

# ---------- SIDEBAR ----------
st.sidebar.markdown("## 🔎 Filters")
debug = st.sidebar.checkbox("Show debug", value=False)
show_past = st.sidebar.checkbox("Show past events", value=False)
sq = st.sidebar.text_input("Search", placeholder="Type to filter titles...")

# ---------- LOAD ----------
df, meta = load_upcoming(U)

if debug:
    st.sidebar.markdown("### Debug")
    st.sidebar.write("Status:", meta["status_code"])
    st.sidebar.write("Content-Type:", meta["content_type"])
    st.sidebar.write("Text length:", meta["text_len"])
    st.sidebar.code(meta["head_lines"] if meta["head_lines"] else "(no content)")

if df.empty:
    st.error("Geen data is gelaai nie vanaf die Upcoming tab. (CSV link gee waarskynlik HTML of is leeg.)")
    if debug:
        st.write(meta)
    st.stop()

# ---------- EXPECTED COLUMNS BY POSITION ----------
# 2=Category, 3=Activity, 4=Extra, 5=Date, 6=Venue, 7=DocLink, 8=Teams/List, 10=InfoLink, 11=Age
cat_series = df.iloc[:, 2].astype(str)
act_series = df.iloc[:, 3].astype(str)

sc = st.sidebar.multiselect("Category", ["Sport", "Culture", "Academics"])
sa = st.sidebar.multiselect("Activity", sorted({c_a(x) for x in act_series}))
ao = ["Gr 1","Gr 2","Gr 3","Gr 4","Gr 5","Gr 6","Gr 7","U7","U8","U9","U10","U11","U12","U13"]
sg = st.sidebar.multiselect("Age Group", ao)

# ---------- FILTER ----------
tz = pytz.timezone("Africa/Johannesburg")
today = datetime.now(tz).date()

res = []
skipped = []

for _, r in df.iterrows():
    cat = str(r.iloc[2]).lower().strip()
    act = str(r.iloc[3]).strip()
    age = cl(r.iloc[11])
    rd  = cl(r.iloc[5])

    dt = pd.to_datetime(rd, dayfirst=True, errors="coerce")
    if pd.isnull(dt):
        dt = datetime(2099, 1, 1)
    elif (not show_past) and dt.date() < today:
        if debug:
            skipped.append(("Date in past", act, rd, age))
        continue

    if sc and not any(x.lower() in cat for x in sc):
        if debug:
            skipped.append(("Category", act, rd, age))
        continue

    if sa and not any(x.lower() in act.lower() for x in sa):
        if debug:
            skipped.append(("Activity", act, rd, age))
        continue

    if sg and age:
        if not any(v.replace("Gr ", "").replace("U", "") in age for v in sg):
            if debug:
                skipped.append(("Age", act, rd, age))
            continue

    res.append({"r": r, "dt": dt, "ds": rd})

res.sort(key=lambda x: x["dt"])

# ⛔ STOP HIER – PLAK DEEL 2 DIREK HIERONDER
# ---------- MAIN DISPLAY ----------
left, right = st.columns([2.2, 1])

with left:
    st.markdown("## 📅 Upcoming Events")

    shown = 0

    if not res:
        st.info("Geen komende items gevind nie. Probeer filters losser maak of skakel 'Show past events' aan.")
    else:
        for i in res:
            r = i["r"]
            ds = i["ds"]


