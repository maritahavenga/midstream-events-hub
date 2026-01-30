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
        st.markdown("<div style='background:white;padding:20px;border-radius:12px;border:1px solid #eee;box-shadow:0 4px 12px rgba(0,0,0,0.05);margin-bottom:20px;'>", unsafe_allow_html=True)
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
                elif "netball" in lo: cl_o.add("Netball")
                elif "rugby" in lo: cl_o.add("Rugby")
                elif re.search(r'(?i)\b(EAT|Afrikaans EAT)\b', o): cl_o.add("Afrikaans Eerste Addisionele Taal")
                elif re.search(r'(?i)\b(HT|Afrikaans HT)\b', o): cl_o.add("Afrikaans Hooftaal")
                else: cl_o.add(o)
            s_act = st.multiselect("Activity", sorted(list(cl_o)))
        with c3:
            if s_cat == ["Sport"]: a_l = ["U7","U8","U9","U10","U11","U12","U13"]
            elif s_cat and "Sport" not in str(s_cat): a_l = ["Gr 1","Gr 2","Gr 3","Gr 4","Gr 5","Gr 6","Gr 7"]
            else: a_l = ["Gr 1","Gr 2","Gr 3","Gr 4","Gr 5","Gr 6","Gr 7","U7","U8","U9","U10","U11","U12","U13"]
            s_age = st.multiselect("Age Group", a_l)
        sq = st.text_input("Search")
        if st.button("REFRESH HUB", use_container_width=True): st.cache_data.clear(); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    today = datetime.now(pytz.timezone('Africa/Johannesburg')).date()
    tn = set()
    for s in s_age:
        ns = re.findall(r'\d+', s)
        if ns:
            n_v = int(ns[0])
            tn.add(n_v); tn.add(n_v-6 if n_v>=7 else n_v+6)

    res = []
    for _, r in df.iterrows():
        n, cat = str(r.iloc[3]), str(r.iloc[2]).lower()
        dn = n
        if "athletics" in n.lower(): dn = "Athletics"
        elif "hockey" in n.lower(): dn = "Hockey"
        elif re.search(r'(?i)\b(EAT|Afrikaans EAT)\b', n): dn = "Afrikaans Eerste Addisionele Taal"
        elif re.search(r'(?i)\b(HT|Afrikaans HT)\b', n
