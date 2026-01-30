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
            nv = int(ns[0]); tn.add(nv); tn.add(nv-6 if nv>=7 else nv+6)

    res = []
    for _, r in df.iterrows():
        n
