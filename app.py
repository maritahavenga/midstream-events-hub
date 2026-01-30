import streamlit as st
import pandas as pd
import requests, io, re, pytz
from datetime import datetime
import streamlit.components.v1 as v1
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="LMCP Hub", layout="centered")
st_autorefresh(interval=120000, key="r_token")

# --- BANNER ---
st.markdown("""
<div style='text-align:center;margin-bottom:20px;'>
<img src='https://raw.githubusercontent.com/LMCPEventsHub/midstream-events-hub/main/LMCP_RGB%20(1).png' width='180'>
<h1 style='color:#800000;margin-bottom:0;'>LAERSKOOL MIDSTREAM COLLEGE PRIMARY</h1>
<p style='color:#008080;font-size:1.2rem;margin-top:5px;'>Digital Hub</p>
</div>
""", unsafe_allow_html=True)

# --- GOOGLE SHEET CSV ---
U = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig-2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

# --- HELPERS ---
def cl(v):
    return str(v).replace(".0","").replace("nan","").strip()

def tr(t,a):
    t = str(t).replace("-", " ").replace("/", " ")
    d = {"Saal":"Hall","Veld":"Field","Atletiek":"Athletics","Wiskunde":"Math"}
    for k,v in d.items():
        t = re.sub(rf"\b{k}\b", v, t, flags=re.I)
    return t

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

# --- DATA LOAD (FIXED PARSER) ---
@st.cache_data(ttl=60)
def ld():
    try:
        r = requests.get(U, timeout=10)
        return pd.read_csv(
            io.StringIO(r.text),
            dtype=str,
            engine="python",
            on_bad_lines="skip"
        ).fillna("")
    except Exception as e:
        st.error("⚠️ Kon nie data laai nie")
        st.write(e)
        return pd.DataFrame()

# --- LOAD DATA ---
df = ld()

# --- DEBUG CHECKBOX ---
debug = st.checkbox("Show debug info (skipped items)")

if debug:
    st.write("Aantal rye in sheet:", len(df))
    st.dataframe(df.head(5))

# --- MAIN APP ---
if not df.empty:

    c1, c2, c3 = st.columns(3)
    with c1:
        sc = st.multiselect("Category", ["Sport", "Culture", "Academics"])
    with c2:
        sa = st.multiselect("Activity", sorted({c_a(x) for x in df.iloc[:,3]}))
    with c3:
        sg = st.multiselect("Age Group", ["Gr 1","Gr 2","Gr 3","Gr 4","Gr 5","Gr 6","Gr 7",
                                          "U7","U8","U9","U10","U11","U12","U13"])

    sq = st.text_input("Search events")

    now = datetime.now(pytz.timezone("Africa/Johannesburg")).date()
    res = []
    skipped = []  # vir debug

    for _, r in df.iterrows():

        cat = str(r.iloc[2]).lower()
        act = str(r.iloc[3])
        age = cl(r.iloc[11])
        rd  = cl(r.iloc[5])

        dt = pd.to_datetime(rd, dayfirst=True, errors="coerce")
        if pd.isnull(dt):
            dt = datetime(2099,1,1)
        elif dt.date() < now:
            skipped.append((r, "Date in past"))
            continue

        if sc and not any(x.lower() in cat for x in sc):
            skipped.append((r, "Category filter"))
            continue

        if sa and not any(x.lower() in act.lower() for x in sa):
            skipped.append((r, "Activity filter"))
            continue

        if sg and age:
            if not any(v.replace("Gr ","").replace("U","") in age for v in sg):
                skipped.append((r, "Age filter"))
                continue

        res.append({"r":r,"dt":dt,"ds":rd})

    res.sort(key=lambda x:x["dt"])

# ⛔ STOP HIER – PLAK DEEL 2 DIREK HIERONDER
    html = """
    <style>
    .card{
        background:white;
        padding:20px;
        border-radius:12px;
        border-left:10px solid #800000;
        margin-bottom:15px;
        box-shadow:0 4px 12px rgba(0,0,0,0.08);
        font-family:sans-serif;
    }
    .title{
        color:#800000;
        font-weight:bold;
        font-size:1.1rem;
        margin-bottom:6px;
    }
    </style>
    """

    for i in res:
        r = i["r"]
        act = str(r.iloc[3])
        age = cl(r.iloc[11])
        ven = cl(r.iloc[6])

        is_sp = any(x in act.lower() for x in ["hockey","rugby","netball","swimming","athletics","tennis"])
        age_lbl = f"U{age}" if is_sp and age else f"Gr {age}" if age else ""

        title = f"{c_a(act)} {age_lbl} {tr(r.iloc[4], act)}"
        if sq and sq.lower() not in title.lower():
            if debug:
                skipped.append((r, "Search text filter"))
            continue

        map_url = (
            f"https://www.google.com/maps/search/?api=1&query={ven.replace(' ','+')}+Midstream"
            if ven else ""
        )

        html += f"""
        <div class='card'>
            <div class='title'>{title}</div>
            <div>📅 {tr(i['ds'], act)}</div>
            {f"<div>📍 <a href='{map_url}' target='_blank'>{ven}</a></div>" if ven else ""}
        </div>
        """

    if not res:
        st.info("No upcoming events found. Adjust your filters or search.")

    v1.html(html, height=2600, scrolling=True)

    if debug and skipped:
        st.write("Skipped items and reason:")
        for item, reason in skipped:
            st.write(f"Reason: {reason}, Activity: {item.iloc[3]}, Date: {item.iloc[5]}, Age: {item.iloc[11]}")

st.markdown(
    "<center style='font-size:0.8rem;color:#999;'>"
    "LAERSKOOL MIDSTREAM COLLEGE PRIMARY Digital Hub 2026"
    "</center>",
    unsafe_allow_html=True
)
