import streamlit as st, pandas as pd, requests, io, re, pytz
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

U = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig-2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

def cl(v): 
    return str(v).replace(".0","").replace("nan","").strip()

def tr(t,a):
    t = str(t).replace("-", " ").replace("/", " ")
    d = {"Saal":"Hall","Veld":"Field","Atletiek":"Athletics","Wiskunde":"Math"}
    for k,v in d.items(): t = re.sub(rf'\b{k}\b', v, t, flags=re.I)
    return t

def c_a(n):
    n = str(n).lower()
    for x in ["hockey","rugby","netball","swimming","athletics","tennis"]:
        if x in n: return x.capitalize()
    if "eerste" in n: return "Afrikaans Eerste Addisionele Taal"
    if "hooftaal" in n: return "Afrikaans Hooftaal"
    return n.capitalize()

@st.cache_data(ttl=60)
def ld():
    r = requests.get(U)
    return pd.read_csv(io.StringIO(r.text), dtype=str).fillna("")

df = ld()

if not df.empty:

    # --- FILTERS ---
    c1,c2,c3 = st.columns(3)
    with c1:
        sc = st.multiselect("Category", ["Sport","Culture","Academics"])
    with c2:
        sa = st.multiselect("Activity", sorted({c_a(x) for x in df.iloc[:,3]}))
    with c3:
        sg = st.multiselect("Age Group", ["Gr 1","Gr 2","Gr 3","Gr 4","Gr 5","Gr 6","Gr 7","U7","U8","U9","U10","U11","U12","U13"])

    sq = st.text_input("Search events")

    now = datetime.now(pytz.timezone("Africa/Johannesburg")).date()
    res = []

    for _, r in df.iterrows():

        cat = str(r.iloc[2]).lower()
        act = str(r.iloc[3])
        age = cl(r.iloc[11])
        rd  = cl(r.iloc[5])

        dt = pd.to_datetime(rd, dayfirst=True, errors="coerce")
        if pd.isnull(dt):
            dt = datetime(2099,1,1)
        elif dt.date() < now:
            continue

        if sc and not any(x.lower() in cat for x in sc):
            continue

        if sa and not any(x.lower() in act.lower() for x in sa):
            continue

        if sg and age:
            if not any(v.replace("Gr ","").replace("U","") in age for v in sg):
                continue

        res.append({"r":r,"dt":dt,"ds":rd})

    res.sort(key=lambda x:x["dt"])

# ⛔ STOP HIER – PLAK DEEL 2 DIREK HIERONDER
 html = """
    <style>
    .card{background:white;padding:20px;border-radius:12px;
    border-left:10px solid #800000;margin-bottom:15px;
    box-shadow:0 4px 12px rgba(0,0,0,0.08);}
    .title{color:#800000;font-weight:bold;font-size:1.1rem;}
    .btn{background:#800000;color:white;padding:8px 14px;
    border-radius:8px;text-decoration:none;margin-right:8px;}
    </style>
    """

    for i in res:
        r = i["r"]
        act = str(r.iloc[3])
        age = cl(r.iloc[11])
        ven = cl(r.iloc[6])

        is_sp = any(x in act.lower() for x in ["hockey","rugby","netball","swimming","athletics"])
        age_lbl = f"U{age}" if is_sp and age else f"Gr {age}" if age else ""

        title = f"{c_a(act)} {age_lbl} {tr(r.iloc[4],act)}"
        if sq and sq.lower() not in title.lower():
            continue

        map_url = f"https://www.google.com/maps/search/?api=1&query={ven.replace(' ','+')}+Midstream" if ven else ""

        html += f"""
        <div class='card'>
        <div class='title'>{title}</div>
        <div>📅 {tr(i['ds'],act)}</div>
        <div><a href='{map_url}' target='_blank'>{ven}</a></div>
        </div>
        """

    v1.html(html, height=2500, scrolling=True)

st.markdown("<center style='font-size:0.8rem;color:#999;'>LMCP Digital Hub 2026</center>", unsafe_allow_html=True)
