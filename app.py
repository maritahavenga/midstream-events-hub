import streamlit as st
import pandas as pd
import requests
import io
import re
from datetime import datetime
import pytz
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="LMCP Digital Hub", layout="centered")
st_autorefresh(interval=120000, key="datarefresh")

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

def clean(v): return str(v).replace(".0", "").replace("nan", "").strip()

def trans(text, act):
    s = str(act).strip()
    if re.search(r'(?i)\bEAT\b', s): text = text.replace(act, "Afrikaans Eerste Addisionele Taal")
    elif re.search(r'(?i)\bHT\b', s): text = text.replace(act, "Afrikaans Hooftaal")
    if any(k in s.lower() for k in ["afrikaans", "eat", "ht"]): return text
    d = {"Saal": "Hall", "Veld": "Field", "Atletiek": "Athletics", "Wiskunde": "Math"}
    for k, v in d.items(): text = re.sub(rf'\b{k}\b', v, text, flags=re.IGNORECASE)
    return text

@st.cache_data(ttl=1)
def load():
    r = requests.get(f"{URL}&cb={datetime.now().timestamp()}", timeout=10)
    return pd.read_csv(io.StringIO(r.content.decode('utf-8'))).fillna("")

df = load()
if not df.empty:
    with st.container():
        st.markdown("<div style='background:white;padding:20px;border-radius:12px;border:1px solid #eee;margin-bottom:20px;'>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1: s_cat = st.multiselect("Category", ["Sport", "Culture", "Academics"])
        with c2:
            o = sorted(list(set(df.iloc[:, 3].str.strip())))
            if s_cat:
                m = df.iloc[:, 2].str.contains('|'.join(s_cat), case=False, na=False)
                if "Academics" in s_cat: m |= df.iloc[:, 2].str.contains("academic", case=False, na=False)
                o = sorted(list(set(df[m].iloc[:, 3].str.strip())))
            s_act = st.multiselect("Activity", o)
        with c3:
            age_o = ["Gr 1", "Gr 2", "Gr 3", "Gr 4", "Gr 5", "Gr 6", "Gr 7", "U7", "U8", "U9", "U10", "U11", "U12", "U13"]
            s_age = st.multiselect("Gr / Age", age_o)
        sq = st.text_input("Search")
        if st.button("REFRESH HUB", use_container_width=True): st.cache_data.clear(); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    today = datetime.now(pytz.timezone('Africa/Johannesburg')).date()
    t_n = set()
    for s in s_age:
        ns = re.findall(r'\d+', s)
        if ns:
            n = int(ns[0])
            t_n.add(n)
            if n >= 7: t_n.add(n-6)
            elif n <= 7: t_n.add(n+6)

    filtered = []
    for _, r in df.iterrows():
        n, cat = str(r.iloc[3]), str(r.iloc[2]).lower()
        dt = pd.to_datetime(str(r.iloc[5]), dayfirst=True, errors='coerce')
        ft = "full term" in str(r.iloc[12]).lower()
        if not ft and pd.notnull(dt) and dt.date() < today: continue
        if s_cat and not any(s.lower
