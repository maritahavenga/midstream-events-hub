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

def clean_val(val):
    return str(val).replace(".0", "").replace("nan", "").strip()

def translate_term(text, act_name=""):
    s = str(act_name).strip()
    if re.search(r'(?i)\bEAT\b', s): text = text.replace(act_name, "Afrikaans Eerste Addisionele Taal")
    elif re.search(r'(?i)\bHT\b', s): text = text.replace(act_name, "Afrikaans Hooftaal")
    if any(k in s.lower() for k in ["afrikaans", "eat", "ht"]): return text
    trans = {"Saal": "Hall", "Ouditorium": "Auditorium", "Veld": "Field", "Atletiek": "Athletics", "Wiskunde": "Mathematics", "Wetenskap": "Science"}
    for k, v in trans.items(): text = re.sub(rf'\b{k}\b', v, text, flags=re.IGNORECASE)
    return text

@st.cache_data(ttl=1)
def load_data():
    r = requests.get(f"{URL}&cb={datetime.now().timestamp()}", timeout=10)
    return pd.read_csv(io.StringIO(r.content.decode('utf-8'))).fillna("")

df_raw = load_data()
if not df_raw.empty:
    with st.container():
        st.markdown("<div style='background:white; padding:20px; border-radius:12px; border:1px solid #eee; margin-bottom:20px;'>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1: s_cat = st.multiselect("Category", ["Sport", "Culture", "Academics"])
        with c2:
            # Dinamiese lys: wys slegs aktiwiteite wat by die gekose kategorie pas
            if s_cat:
                m_cat = df_raw.iloc[:, 2].str.contains('|'.join(s_cat), case=False, na=False)
                if "Academics" in s_cat: m_cat |= df_raw.iloc[:, 2].str.contains("academic", case=False, na=False)
                opts = sorted(list(set(df_raw[m_cat].iloc[:, 3].str.strip())))
            else:
                opts = sorted(list(set(df_raw.iloc[:, 3].str.strip())))
            s_act = st.multiselect("Activity", opts)
        with c3:
            age_opts = ["Gr 1", "Gr 2", "Gr 3", "Gr 4", "Gr 5", "Gr 6", "Gr 7", "U7", "U8", "U9", "U10", "U11", "U12", "U13"]
            s_age = st.multiselect("Gr / Age", age_opts)
        sq = st.text_input("Search")
        if st.button("REFRESH HUB", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    today = datetime.now(pytz.timezone('Africa/Johannesburg')).date()
    t_nums = set()
    for s in s_age:
        ns = re.findall(r'\d+', s)
        if ns:
            n = int(ns[0])
            t_nums.add(n)
            if n >= 7: t_nums.add(n - 6)
            elif n <= 7: t_nums.add(n + 6)
