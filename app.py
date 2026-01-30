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
<h1 style='color:#800000;margin-bottom:0;font-family:sans-serif;'>LAERSKOOL MIDSTREAM COLLEGE PRIMARY</h1>
<p style='color:#008080;font-size:1.2rem;margin-top:5px;font-family:sans-serif;'>Digital Hub</p>
</div>
""", unsafe_allow_html=True)

# JOU SPESIFIEKE SKAKEL
U = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig-2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

def cl(v): return str(v).replace(".0","").replace("nan","").strip()

def tr(t,a):
    t = str(t).replace("-", " ").replace("/", " ")
    t = t.replace("swimming", "Swimming").replace("gala", "Gala")
    d = {"Saal":"Hall","Veld":"Field","Atletiek":"Athletics","Wiskunde":"Math"}
    for k,v in d.items(): t = re.sub(rf"\b{k}\b", v, t, flags=re.I)
    return t

def c_a(n):
    n = str(n).lower()
    for x in ["hockey","rugby","netball","swimming","athletics","tennis"]:
        if x in n: return x.capitalize()
    if "eerste" in n: return "Afrikaans Eerste Addisionele Taal"
    if "hooftaal" in n: return "Afrikaans Hooftaal"
    return n.capitalize()

@st.cache_data(ttl=1)
def ld():
    try:
        # Ons voeg 'n tydstempel by die skakel om Google te dwing om nuwe data te gee
        r = requests.get(f"{U}&cache_bust={datetime.now().timestamp()}", timeout=10)
        return pd.read_csv(io.StringIO(r.content.decode('utf-8')), dtype=str).fillna("")
    except: return pd.DataFrame()

df = ld()
if not df.empty:
    st.markdown("<div style='background:#fff;padding:20px;border-radius:15px;border:1px solid #eee;box-shadow:0 4px 15px rgba(0,0,0,0.05);margin-bottom:25px;'>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1: sc = st.multiselect("Category", ["Sport", "Culture", "Academics"])
    with c2: sa = st.multiselect("Activity", sorted({c_a(x) for x in df.iloc[:,3]}))
    with c3: sg = st.multiselect("Age Group", ["Gr 1","Gr 2","Gr 3","Gr 4","Gr 5","Gr 6","Gr 7","U7","U8","U9","U10","U11","U12","U13"])
    sq = st.text_input("Search events", placeholder="Type to search...")
    if st.button("🔄 Force Refresh Data"): 
        st.cache_data.clear()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    # Vandag se datum (30 Jan 2026)
    now = datetime.now(pytz.timezone("Africa/Johannesburg")).date()
    res = []

    for _, r in df.iterrows():
        cat, act, age, rd = str(r.iloc[2]).lower(), str(r.iloc[3]), cl(r.iloc[11]), cl(r.iloc[5])
        
        # DATE PARSING (DD/MM/YYYY)
        dt = pd.to_datetime(rd, dayfirst=True, errors="coerce")
        
        # WYS ALLES VAN VANDAG AF VORENTOE (insluitend vandag)
        if pd.notnull(dt) and dt.date() < now: continue
        
        # FILTERS
        if sc and not any(x.lower() in cat for x in sc): continue
        if sa and not any(x.lower() in act.lower() for x in sa): continue
        if sg and age:
            if not any(v.replace("Gr ","").replace("U","") in age for v in sg): continue

        res.append({"r":r,"dt":dt if pd.notnull(dt) else datetime(2099,1,1),"ds":rd})

    res.sort(key=lambda x:x["dt"])

    html = """<style>
    .card{background:white;padding:20px;border-radius:12px;border-left:10px solid #800000;margin-bottom:15px;box-shadow:0 4px 12px rgba(0,0,0,0.08);font-family:sans-serif;}
    .title{color:#800000;font-weight:bold;font-size:1.15rem;margin-bottom:6px;}
    .venue{color:#008080;font-weight:bold;margin-top:8px;}
    .btn{background:#800000;color:white!important;padding:8px 15px;border-radius:6px;text-decoration:none;font-size:0.8rem;margin-right:10px;display:inline-block;}
    </style>"""

    if not res:
        st.info("No upcoming events found. Note: Events before today are automatically hidden.")
    else:
        for i in res:
            r = i["r"]
            act, age, ven = str(r.iloc[3]), cl(r.iloc[11]), cl(r.iloc[6])
            cat_raw = str(r.iloc[2]).lower()
            
            # --- U / GR LOGIKA ---
            is_sp = "sport" in cat_raw or any(x in act.lower() for x in ["hockey","rugby","netball","swimming","athletics","tennis"])
            is_ac = "academic" in cat_raw or any(x in act.lower() for x in ["afrikaans","wiskunde","math","atp"])
            prefix = "U" if is_sp else ("Gr " if is_ac else "")
            age_lbl = f"{prefix}{age}" if age else ""

            title = f"{c_a(act)} {age_lbl} {tr(r.iloc[4], act)}"
            if sq and sq.lower() not in title.lower(): continue

            b_html = ""
            if "http" in cl(r.iloc[7]): b_html += f"<a class='btn' href='{cl(r.iloc[7])}' target='_blank'>Documents</a>"
            if "http" in cl(r.iloc[8]): b_html += f"<a class='btn' href='{cl(r.iloc[8])}' target='_blank'>Team List</a>"
            if "http" in cl(r.iloc[10]): b_html += f"<a class='btn' href='{cl(r.iloc[10])}' target='_blank'>Info</a>"

            map_url = f"https://www.google.com/maps/search/?api=1&query={ven.replace(' ','+')}+Midstream" if ven else "#"

            html += f"""
            <div class='card'>
                <div class='title'>{title}</div>
                <div style='color:#555;'>📅 {tr(i['ds'], act)}</div>
                {f"<div class='venue'>📍 <a href='{map_url}' target='_blank' style='color:#008080;text-decoration:none;'>{tr(ven,act).upper()}</a></div>" if ven else ""}
                <div style='margin-top:15px;'>{b_html}</div>
            </div>
            """
        v1.html(html, height=3000, scrolling=True)

st.markdown("<center style='font-size:0.8rem;color:#999;'>LAERSKOOL MIDSTREAM COLLEGE PRIMARY Digital Hub 2026</center>", unsafe_allow_html=True)
