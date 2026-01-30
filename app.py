import streamlit as st
import pandas as pd
import requests
import io, re
from datetime import datetime
import pytz
import streamlit.components.v1 as v1
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="LMCP Hub", layout="centered")
st_autorefresh(interval=120000, key="r")

U="https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

def cl(v): return str(v).replace(".0","").replace("nan","").strip()

def tr(t, a):
    r = str(a).strip()
    t = t.replace(" G ", " Girls ").replace(" G", " Girls")
    if re.search(r'(?i)\b(EAT|HT|Hooftaal|Eerste)\b', r):
        return "Afrikaans " + ("Eerste Addisionele Taal" if "eat" in r.lower() or "eerste" in r.lower() else "Hooftaal")
    d = {"Saal":"Hall","Veld":"Field","Atletiek":"Athletics","Wiskunde":"Math"}
    for k, v in d.items(): t = re.sub(rf'\b{k}\b', v, t, flags=re.IGNORECASE)
    return t

def clean_act(n):
    n = n.lower()
    if "athletics" in n or "atletiek" in n: return "Athletics"
    if "hockey" in n: return "Hockey"
    if "rugby" in n: return "Rugby"
    if "netball" in n or "netbal" in n: return "Netball"
    if "tennis" in n: return "Tennis"
    if "eat" in n or "eerste" in n: return "Afrikaans Eerste Addisionele Taal"
    if "ht" in n or "hooftaal" in n: return "Afrikaans Hooftaal"
    return n.capitalize()

@st.cache_data(ttl=10)
def ld():
    r = requests.get(f"{U}&cb={datetime.now().timestamp()}", timeout=5)
    return pd.read_csv(io.StringIO(r.content.decode('utf-8')), dtype=str).fillna("")

df = ld()

if not df.empty:
    st.markdown("<div style='background:white;padding:15px;border-radius:10px;border:1px solid #eee;'>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    
    with c1: 
        sc = st.multiselect("Category", ["Sport", "Culture", "Academics"])
    
    with c2:
        m = df.iloc[:, 2].str.contains('|'.join(sc) if sc else ".*", case=False)
        if sc and "Academics" in sc: m |= df.iloc[:, 2].str.contains("academic", case=False)
        acts = sorted(list({clean_act(str(o)) for o in df[m].iloc[:, 3].str.strip()}))
        sa = st.multiselect("Activity", acts)
    
    with c3:
        ao = ["Gr 1","Gr 2","Gr 3","Gr 4","Gr 5","Gr 6","Gr 7","U7","U8","U9","U10","U11","U12","U13"]
        if sc == ["Sport"]: do = [o for o in ao if "U" in o]
        elif sc and "Sport" not in str(sc): do = [o for o in ao if "Gr" in o]
        else: do = ao
        sg = st.multiselect("Age Group", options=do, key="stk_stable")

    sq = st.text_input("Search")
    st.markdown("</div>", unsafe_allow_html=True)

    ty = datetime.now(pytz.timezone('Africa/Johannesburg')).date()
    tn = set()
    for s in sg:
        ns = re.findall(r'\d+', s)
        if ns:
            v = int(ns[0])
            tn.update([v, v+6 if v<=7 else v-6])

    res = []
    for _, r in df.iterrows():
        n, cat, av, rd = str(r.iloc[3]), str(r.iloc[2]).lower(), cl(r.iloc[11]), cl(r.iloc[5])
        dt = pd.to_datetime(rd, dayfirst=True, errors='coerce')
        
        cm = (any(x.lower() in cat for x in sc) or ("Academics" in sc and "academic" in cat)) if sc else True
        if not cm or (sa and clean_act(n) not in sa): continue
        
        vn = re.findall(r'\d+', av)
        if tn and vn and int(vn[0]) not in tn: continue
        
        ft = "full term" in str(r.iloc[12]).lower()
        if not ft and pd.notnull(dt) and dt.date() < ty: continue
        
        res.append({'r': r, 'dt': dt if pd.notnull(dt) else datetime.max.replace(tzinfo=None), 'dd': dt.strftime('%d %B %Y') if pd.notnull(dt) else rd})

    res.sort(key=lambda x: x['dt'])

    h = "<style>.card{background:white;padding:12px;border-radius:10px;border-left:8px solid #800000;margin-bottom:10px;box-shadow:0 2px 5px rgba(0,0,0,0.1);font-family:sans-serif;}.title{color:#800000;font-weight:bold;margin-bottom:5px;}.btn{background:#800000;color:white!important;padding:5px 10px;border-radius:6px;text-decoration:none;font-size:0.75rem;display:inline-block;margin:5px 5px 0 0;}.nt{background:#f0f7f7;padding:8px;margin-top:5px;border-radius:6px;font-size:0.8rem;}</style>"
    
    for i in res:
