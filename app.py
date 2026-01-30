import streamlit as st
import pandas as pd
import requests
import io, re
from datetime import datetime
import pytz
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="LMCP Hub", layout="centered")
st_autorefresh(interval=120000, key="refresh")

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

def cl(v): return str(v).replace(".0", "").replace("nan", "").strip()

def tr(t, a):
    s = str(a).strip()
    if re.search(r'(?i)\b(EAT|Afrikaans Eerste Addisionele Taal)\b', s): t = t.replace(a, "Afrikaans Eerste Addisionele Taal")
    elif re.search(r'(?i)\b(HT|Afrikaans Hooftaal)\b', s): t = t.replace(a, "Afrikaans Hooftaal")
    if any(k in s.lower() for k in ["afrikaans", "eat", "ht"]): return t
    d = {"Saal": "Hall", "Veld": "Field", "Atletiek": "Athletics", "Wiskunde": "Math"}
    for k, v in d.items(): t = re.sub(rf'\b{k}\b', v, t, flags=re.IGNORECASE)
    return t

@st.cache_data(ttl=10)
def ld():
    r = requests.get(f"{URL}&cb={datetime.now().timestamp()}", timeout=5)
    return pd.read_csv(io.StringIO(r.content.decode('utf-8')), dtype=str).fillna("")

df = ld()
if not df.empty:
    with st.container():
        st.markdown("<div style='background:white;padding:20px;border-radius:12px;border:1px solid #eee;box-shadow:0 4px 12px rgba(0,0,0,0.05);'>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1: s_cat = st.multiselect("Category", ["Sport", "Culture", "Academics"])
        with c2:
            m = df.iloc[:, 2].str.contains('|'.join(s_cat), case=False) if s_cat else df.iloc[:, 2].notnull()
            o_raw = sorted(list(set(df[m].iloc[:, 3].str.strip())))
            cl_o = set()
            for o in o_raw:
                lo = o.lower()
                if "athletics" in lo: cl_o.add("Athletics")
                elif "hockey" in lo: cl_o.add("Hockey")
                elif re.search(r'(?i)\b(EAT|Afrikaans EAT)\b', o): cl_o.add("Afrikaans Eerste Addisionele Taal")
                elif re.search(r'(?i)\b(HT|Afrikaans HT)\b', o): cl_o.add("Afrikaans Hooftaal")
                else: cl_o.add(o)
            s_act = st.multiselect("Activity", sorted(list(cl_o)))
        with c3:
            a_l = ["U7","U8","U9","U10","U11","U12","U13"] if s_cat == ["Sport"] else ["Gr 1","Gr 2","Gr 3","Gr 4","Gr 5","Gr 6","Gr 7"]
            if not s_cat or len(s_cat) > 1: a_l = ["Gr 1","Gr 2","Gr 3","Gr 4","Gr 5","Gr 6","Gr 7","U7","U8","U9","U10","U11","U12","U13"]
            s_age = st.multiselect("Age Group", a_l)
        sq = st.text_input("Search")
        if st.button("REFRESH HUB", use_container_width=True): st.cache_data.clear(); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    today = datetime.now(pytz.timezone('Africa/Johannesburg')).date()
    tn = set()
    for s in s_age:
        ns = re.findall(r'\d+', s)
        if ns:
            nv = int(ns[0])
            tn.add(nv); tn.add(nv-6 if nv>=7 else nv+6)

    res = []
    for _, r in df.iterrows():
        n, cat = str(r.iloc[3]), str(r.iloc[2]).lower()
        dn = n
        if "athletics" in n.lower(): dn = "Athletics"
        elif "hockey" in n.lower(): dn = "Hockey"
        elif re.search(r'(?i)\b(EAT|Afrikaans EAT|HT|Afrikaans HT)\b', n):
            dn = "Afrikaans Eerste Addisionele Taal" if "eat" in n.lower() else "Afrikaans Hooftaal"
        if (s_cat and not any(x.lower() in cat or (x=="Academics" and "academic" in cat) for x in s_cat)) or (s_act and dn not in s_act): continue
        dt = pd.to_datetime(cl(r.iloc[5]), dayfirst=True, errors='coerce')
        ft = "full term" in str(r.iloc[12]).lower()
        if (not ft and pd.notnull(dt) and dt.date() < today) or (tn and not any(x in n.lower() for x in ["swimming", "athletics"]) and not (re.findall(r'\d+', cl(r.iloc[11])) and int(re.findall(r'\d+', cl(r.iloc[11]))[0]) in tn)): continue
        res.append({'r':r, 'dt':dt if pd.notnull(dt) else datetime.max.replace(tzinfo=None), 'n':n.lower(), 'ft':ft, 'dd':dt.strftime('%d %B %Y') if pd.notnull(dt) else cl(r.iloc[5])})

    res.sort(key=lambda x: (not x['ft'], x['dt'], x['n']))
    h = "<style>@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');body{font-family:'Inter',sans-serif;}.card{background:white;padding:18px;border-radius:15px;border-left:10px solid #800000;margin-bottom:15px;box-shadow:0 4px 15px rgba(0,0,0,0.05);}.title{color:#800000;font-size:1.1rem;font-weight:800;}.v-row{font-size:0.85rem;color:#008080;font-weight:700;margin-top:6px;text-transform:uppercase;}.v-link{color:#008080;text-decoration:none;}.btn{background:#800000;color:white!important;padding:8px 12px;border-radius:8px;text-decoration:none;font-size:0.75rem;font-weight:700;display:inline-block;margin-top:10px;margin-right:6px;}</style>"
    for i in res:
        r, f, ds = i['r'], i['ft'], i['dd']
        cat_v, act, age = str(r.iloc[2]).lower(), str(r.iloc
