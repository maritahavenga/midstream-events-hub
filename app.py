import streamlit as st
import pandas as pd
import requests
import io, re
from datetime import datetime
import pytz
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="LMCP Hub", layout="centered")
st_autorefresh(interval=120000, key="r")
U = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

def cl(v): return str(v).replace(".0", "").replace("nan", "").strip()
def tr(t, a):
    s = str(a).strip()
    if re.search(r'(?i)\b(EAT|Afrikaans EAT)\b', s): t = t.replace(a, "Afrikaans Eerste Addisionele Taal")
    elif re.search(r'(?i)\b(HT|Afrikaans HT)\b', s): t = t.replace(a, "Afrikaans Hooftaal")
    if any(k in s.lower() for k in ["afrikaans", "eat", "ht"]): return t
    d = {"Saal": "Hall", "Veld": "Field", "Atletiek": "Athletics", "Wiskunde": "Math"}
    for k, v in d.items(): t = re.sub(rf'\b{k}\b', v, t, flags=re.IGNORECASE)
    return t

@st.cache_data(ttl=10)
def ld():
    r = requests.get(f"{U}&cb={datetime.now().timestamp()}", timeout=5)
    return pd.read_csv(io.StringIO(r.content.decode('utf-8')), dtype=str).fillna("")

df = ld()
if not df.empty:
    st.markdown("<div style='background:white;padding:20px;border-radius:12px;border:1px solid #eee;'>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1: sc = st.multiselect("Category", ["Sport", "Culture", "Academics"])
    with c2:
        m = df.iloc[:, 2].str.contains('|'.join(sc) if sc else ".*", case=False)
        if sc and "Academics" in sc: m |= df.iloc[:, 2].str.contains("academic", case=False)
        orw = sorted(list(set(df[m].iloc[:, 3].str.strip())))
        clo = set()
        for o in orw:
            lo = o.lower()
            if "athletics" in lo: clo.add("Athletics")
            elif "hockey" in lo: clo.add("Hockey")
            elif "eat" in lo: clo.add("Afrikaans Eerste Addisionele Taal")
            elif "ht" in lo: clo.add("Afrikaans Hooftaal")
            else: clo.add(o)
        sa = st.multiselect("Activity", sorted(list(clo)))
    with c3:
        al = ["U7","U8","U9","U10","U11","U12","U13"] if sc == ["Sport"] else ["Gr 1","Gr 2","Gr 3","Gr 4","Gr 5","Gr 6","Gr 7"]
        if not sc or len(sc) > 1: al = ["Gr 1","Gr 2","Gr 3","Gr 4","Gr 5","Gr 6","Gr 7","U7","U8","U9","U10","U11","U12","U13"]
        sg = st.multiselect("Age Group", al)
    sq = st.text_input("Search")
    st.markdown("</div>", unsafe_allow_html=True)

    today = datetime.now(pytz.timezone('Africa/Johannesburg')).date()
    tn = set()
    for s in sg:
        ns = re.findall(r'\d+', s)
        if ns:
            nv = int(ns[0])
            tn.add(nv)
            tn.add(nv-6 if nv>=7 else nv+6)

    res = []
    for _, r in df.iterrows():
        n, cat = str(r.iloc[3]), str(r.iloc[2]).lower()
        dn = "Athletics" if "athletics" in n.lower() else ("Hockey" if "hockey" in n.lower() else n)
        if "eat" in n.lower(): dn = "Afrikaans Eerste Addisionele Taal"
        elif "ht" in n.lower(): dn = "Afrikaans Hooftaal"
        
        c_m = True
        if sc:
            c_m = any(x.lower() in cat for x in sc)
            if "Academics" in sc and "academic" in cat: c_m = True
        
        if not c_m or (sa and dn not in sa): continue
        dt = pd.to_datetime(cl(r.iloc[5]), dayfirst=True, errors='coerce')
        ft = "full term" in str(r.iloc[12]).lower()
        if (not ft and pd.notnull(dt) and dt.date() < today): continue
        if tn and not any(x in n.lower() for x in ["swimming", "athletics"]):
            v_num = re.findall(r'\d+', cl(r.iloc[11]))
            if not (v_num and int(v_num[0]) in tn): continue
        res.append({'r':r, 'dt':dt if pd.notnull(dt) else datetime.max.replace(tzinfo=None), 'n':n.lower(), 'ft':ft, 'dd':dt.strftime('%d %B %Y') if pd.notnull(dt) else cl(r.iloc[5])})

    res.sort(key=lambda x: (not x['ft'], x['dt'], x['n']))
    h = "<style>body{font-family:sans-serif;}.card{background:white;padding:15px;border-radius:12px;border-left:8px solid #800000;margin-bottom:12px;box-shadow:0 2px 5px rgba(0,0,0,0.1);}.title{color:#800000;font-size:1.1rem;font-weight:bold;}.v-link{color:#008080;text-decoration:none;font-weight:bold;text-transform:uppercase;}.btn{background:#800000;color:white!important;padding:6px 10px;border-radius:6px;text-decoration:none;font-size:0.7rem;display:inline-block;margin:5px 5px 0 0;}</style>"
    for i in res:
        r, f, ds = i['r'], i['ft'], i['dd']
        cat_v, act, age = str(r.iloc[2]).lower(), str(r.iloc[3]), cl(r.iloc[11])
        title = f"{tr(act, act)} {('U' if 'sport' in cat_v else 'Gr ')+age+' ' if age else ''}{tr(cl(r.iloc[4]), act)}".strip()
        if sq and sq.lower() not in title.lower(): continue
        v_val, v_h = cl(r.iloc[6]), ""
        if v_val: v_h = f"<div style='margin-top:5px;'>📍 <a href='https://www.google.com/maps/search/?api=1&query={v_val.replace(' ','+')}+Midstream' target='_blank' class='v-link'>{tr(v_val, act).upper()}</a></div>"
        is_af = "afrikaans" in act.lower()
        is_ac = "academic" in cat_v or any(x in act.lower() for x in ["math", "science", "wiskunde"])
        b1 = "Dokumente" if is_af else ("Document" if is_ac else "Programme")
        btns = "".join([f"<a href='{r.
