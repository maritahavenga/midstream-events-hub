import streamlit as st
import pandas as pd
import requests, io, re, pytz
from datetime import datetime

st.set_page_config(page_title="LMCP Hub", page_icon="📌", layout="wide")

# =========================
# 1) PLAK JOU 2 CSV LINKS HIER
# =========================
U_TAB1 = "PASTE_TAB1_CSV_LINK_HIER"
U_TAB2 = "PASTE_TAB2_CSV_LINK_HIER"

# --- STYLE (mooier UI) ---
st.markdown("""
<style>
:root{
  --maroon:#800000;
  --teal:#008080;
  --soft:#f6f8fb;
  --line:#e9edf3;
}
.block-container{padding-top:1.2rem;}
.card{
  background:white;
  border:1px solid var(--line);
  border-left:10px solid var(--maroon);
  border-radius:16px;
  padding:16px 16px 14px 16px;
  box-shadow:0 6px 18px rgba(0,0,0,0.05);
  margin-bottom:14px;
}
.title{
  font-size:1.15rem;
  font-weight:800;
  color:var(--maroon);
  line-height:1.2;
}
.meta{color:#4b5563; margin-top:6px;}
.pill{
  display:inline-block;
  padding:4px 10px;
  border-radius:999px;
  background:rgba(0,128,128,0.09);
  color:var(--teal);
  font-weight:700;
  font-size:0.85rem;
  margin-top:8px;
}
.small{font-size:0.9rem; color:#374151;}
hr.soft{border:none;border-top:1px solid var(--line); margin:10px 0;}
</style>
""", unsafe_allow_html=True)

# --- BANNER ---
st.markdown("""
<div style="display:flex;gap:16px;align-items:center;background:linear-gradient(135deg,#ffffff, #f7fbfb);
            border:1px solid #e9edf3;border-radius:18px;padding:16px 18px;margin-bottom:14px;">
  <img src="https://raw.githubusercontent.com/LMCPEventsHub/midstream-events-hub/main/LMCP_RGB%20(1).png"
       style="width:76px;height:auto;border-radius:12px;">
  <div>
    <div style="font-weight:900;color:#800000;font-size:1.35rem;line-height:1.1;">
      LAERSKOOL MIDSTREAM COLLEGE PRIMARY
    </div>
    <div style="color:#008080;font-size:1.05rem;font-weight:700;margin-top:4px;">
      Digital Hub
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# --- HELPERS ---
def cl(v):
    return str(v).replace(".0", "").replace("nan", "").strip()

def tr(t, a=""):
    t = str(t).replace("-", " ").replace("/", " ")
    d = {"Saal":"Hall","Veld":"Field","Atletiek":"Athletics","Wiskunde":"Math","Netbal":"Netball"}
    for k, v in d.items():
        t = re.sub(rf"\b{k}\b", v, t, flags=re.I)
    return t.strip()

def c_a(n):
    n = str(n).lower()
    for x in ["hockey","rugby","netball","swimming","athletics","tennis"]:
        if x in n:
            return x.capitalize()
    if "eerste" in n:
        return "Afrikaans Eerste Addisionele Taal"
    if "hooftaal" in n:
        return "Afrikaans Hooftaal"
    return n.capitalize()

def safe_read_csv(url: str) -> pd.DataFrame:
    # Robust: werk met slegte rye / quotes / multiline
    r = requests.get(url, timeout=15)
    txt = r.text
    return pd.read_csv(
        io.StringIO(txt),
        dtype=str,
        engine="python",
        on_bad_lines="skip"
    ).fillna("")

@st.cache_data(ttl=60)
def load_all(tab1_url: str, tab2_url: str) -> pd.DataFrame:
    frames = []
    if tab1_url and "http" in tab1_url:
        frames.append(safe_read_csv(tab1_url))
    if tab2_url and "http" in tab2_url:
        frames.append(safe_read_csv(tab2_url))

    if not frames:
        return pd.DataFrame()

    # concat + drop heeltemal leë rye
    df_all = pd.concat(frames, ignore_index=True)
    df_all = df_all.dropna(how="all")
    return df_all

# --- LOAD ---
df = load_all(U_TAB1, U_TAB2)

# =========================
# SIDEBAR: Filters + Debug
# =========================
st.sidebar.markdown("## 🔎 Filters")
debug = st.sidebar.checkbox("Show debug", value=False)

if df.empty:
    st.error("Geen data is gelaai nie. Maak seker jy het jou 2 CSV links bo by U_TAB1 en U_TAB2 geplak.")
    if debug:
        st.sidebar.write("Tip: Plak elke tab se **Publish to web → CSV** link hier.")
    st.stop()

# Build filter options safely
try:
    cat_series = df.iloc[:, 2].astype(str)
    act_series = df.iloc[:, 3].astype(str)
    age_series = df.iloc[:, 11].astype(str)
    date_series = df.iloc[:, 5].astype(str)
except Exception:
    st.error("Jou sheet se kolomme pas nie by die verwagte uitleg nie (kolom 3/4/6/12).")
    if debug:
        st.write("Columns preview:")
        st.dataframe(df.head(5))
    st.stop()

sc = st.sidebar.multiselect("Category", ["Sport", "Culture", "Academics"])
sa = st.sidebar.multiselect("Activity", sorted({c_a(x) for x in act_series}))
ao = ["Gr 1","Gr 2","Gr 3","Gr 4","Gr 5","Gr 6","Gr 7","U7","U8","U9","U10","U11","U12","U13"]
sg = st.sidebar.multiselect("Age Group", ao)
sq = st.sidebar.text_input("Search", placeholder="Type to filter titles...")

st.sidebar.markdown("---")
show_past = st.sidebar.checkbox("Show past events", value=False)

# Debug info (safe)
if debug:
    st.sidebar.markdown("### Debug")
    st.sidebar.write("Rows loaded:", len(df))
    st.sidebar.write("Sample date values:", list(date_series.head(5)))

# =========================
# FILTER + PREP RESULTS
# =========================
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

    # Category filter (relaxed)
    if sc and not any(x.lower() in cat for x in sc):
        if debug:
            skipped.append(("Category", act, rd, age))
        continue

    # Activity filter (relaxed contains)
    if sa and not any(x.lower() in act.lower() for x in sa):
        if debug:
            skipped.append(("Activity", act, rd, age))
        continue

    # Age filter (safe)
    if sg and age:
        if not any(v.replace("Gr ", "").replace("U", "") in age for v in sg):
            if debug:
                skipped.append(("Age", act, rd, age))
            continue

    res.append({"r": r, "dt": dt, "ds": rd})

res.sort(key=lambda x: x["dt"])

# ⛔ STOP HIER – PLAK DEEL 2 DIREK HIERONDER
# =========================
# MAIN DISPLAY
# =========================
left, right = st.columns([2.2, 1])

with left:
    st.markdown("## 📅 Upcoming Events")

    if not res:
        st.info("Geen komende items gevind nie. Probeer filters losser maak of skakel 'Show past events' aan.")
    else:
        for i in res:
            r = i["r"]
            ds = i["ds"]

            act = str(r.iloc[3]).strip()
            age = cl(r.iloc[11])
            ven = cl(r.iloc[6])
            extra = cl(r.iloc[4])

            t_l = cl(r.iloc[8])   # teams/list
            i_r = cl(r.iloc[10])  # info/note
            doc = cl(r.iloc[7])   # documents link

            is_sport = any(x in act.lower() for x in ["hockey","rugby","netball","swimming","athletics","tennis"])
            prefix = "U" if is_sport else "Gr "
            age_lbl = (prefix + age) if age else ""

            title = f"{c_a(act)} {age_lbl} {tr(extra, act)}".strip()
            if sq and sq.lower().replace(" ", "") not in title.lower().replace(" ", ""):
                if debug:
                    skipped.append(("Search", act, ds, age))
                continue

            map_url = ""
            if ven:
                map_url = f"https://www.google.com/maps/search/?api=1&query={ven.replace(' ','+')}+Midstream"

            # Card UI
            st.markdown(f"""
<div class="card">
  <div class="title">{title}</div>
  <div class="meta">📅 <b>{tr(ds, act)}</b></div>
  {f'<div class="meta">📍 <a href="{map_url}" target="_blank" style="color:#008080;font-weight:800;text-decoration:none;">{tr(ven, act).upper()}</a></div>' if ven else ''}
  <div class="pill">{'SPORT' if is_sport else 'ACADEMIC / OTHER'}</div>
  <hr class="soft"/>
</div>
""", unsafe_allow_html=True)

            # Buttons + extra info (native Streamlit – looks clean)
            b1, b2, b3 = st.columns(3)

            if doc and "http" in doc.lower():
                b1.link_button("📄 Documents", doc, use_container_width=True)

            # Team list or assessment link can sometimes sit in t_l
            if t_l and "http" in t_l.lower():
                b2.link_button("👥 Team / List", t_l, use_container_width=True)

            if i_r and "http" in i_r.lower():
                b3.link_button("ℹ️ Info", i_r, use_container_width=True)

            # Notes text (if not links)
            if (t_l and "http" not in t_l.lower()) or (i_r and "http" not in i_r.lower()):
                with st.expander("Notes / Teams", expanded=False):
                    if t_l and "http" not in t_l.lower():
                        st.info(f"**Teams:** {t_l}")
                    if i_r and "http" not in i_r.lower():
                        st.info(f"**Note:** {i_r}")

            st.write("")  # spacing

with right:
    st.markdown("## 🧭 Quick Info")
    st.markdown(
        "- Gebruik filters in die sidebar.\n"
        "- Skakel **Show past events** aan om ou items te sien.\n"
        "- As niks wys nie, skakel **Show debug** aan."
    )

    if debug:
        st.markdown("### Debug panel")
        st.write("Rows loaded:", len(df))
        st.write("Results after filters:", len(res))
        if skipped:
            st.markdown("**Skipped (first 25):**")
            for reason, act, rd, age in skipped[:25]:
                st.write(f"- {reason} | {act} | {rd} | {age}")
        else:
            st.write("No skipped items logged.")

st.markdown(
    "<hr style='border:none;border-top:1px solid #e9edf3;margin-top:18px;'>"
    "<center style='font-size:0.85rem;color:#999;'>LAERSKOOL MIDSTREAM COLLEGE PRIMARY Digital Hub 2026</center>",
    unsafe_allow_html=True
)

