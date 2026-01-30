import streamlit as st
import pandas as pd
import requests
import io, re
from datetime import datetime
import pytz
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="LMCP Digital Hub", layout="centered")
st_autorefresh(interval=120000, key="refresh")

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

def cl(v): return str(v).replace(".0", "").replace("nan", "").strip()

def tr(t, a):
    s = str(a).strip()
    if re.search(r'(?i)\bEAT\b', s): t = t.replace(a, "Afrikaans Eerste Addisionele Taal")
    elif re.search(r'(?i)\bHT\b', s): t = t.replace(a, "Afrikaans Hooftaal")
    if any(k in s.lower() for k in ["afrikaans", "eat", "ht"]): return t
    d = {"Saal": "Hall", "Veld": "Field", "Atletiek": "Athletics", "Wiskunde": "Math"}
    for k, v in d.items(): t = re.sub(rf'\b{k}\b', v, t, flags=re.IGNORECASE)
    return t

@st.cache_data(ttl=1)
def ld():
    r = requests.get(f"{URL}&cb={datetime.now().timestamp()}", timeout=10)
    return pd.read_csv(io.StringIO(r.content.decode('utf-8')), dtype=str).fillna("")

df = ld()
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
        with c3: s_age = st.multiselect("Gr / Age", ["Gr 1","Gr 2","Gr 3","Gr 4","Gr 5","Gr 6","Gr 7","U7","U8","U9","U10","U11","U12","U13"])
        sq = st.text_input("Search")
        if st.button("REFRESH HUB", use_container_width=True): st.cache_data.clear(); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    today = datetime.now(pytz.timezone('Africa/Johannesburg')).date()
    tn = set()
    for s in s_age:
        ns = re.findall(r'\d+', s)
        if ns:
            n = int(ns[0])
            tn.add(n); tn.add(n-6 if n>=7 else n+6)

    res = []
    for _, r in df.iterrows():
        n, cat = str(r.iloc[3]), str(r.iloc[2]).lower()
        raw_dt = cl(r.iloc[5])
        dt_obj = pd.to_datetime(raw_dt, dayfirst=True, errors='coerce')
        ft = "full term" in str(r.iloc[12]).lower()
        if not ft and pd.notnull(dt_obj) and dt_obj.date() < today: continue
        if s_cat and not any(x.lower() in cat or (x=="Academics" and "academic" in cat) for x in s_cat): continue
        if s_act and n.strip() not in s_act: continue
        if tn and not any(x in n.lower() for x in ["swimming", "athletics"]):
            vn = re.findall(r'\d+', cl(r.iloc[11]))
            if not (vn and int(vn[0]) in tn): continue
        m = re.search(r'\d+', cl(r.iloc[11]))
        gv = int(m.group()) if m else 99
        if "U" in str(r.iloc[11]).upper() and gv >= 7: gv -= 6
        
        # Formateer datum na "05 February 2026"
        disp_d = dt_obj.strftime('%d %B %Y') if pd.notnull(dt_obj) else raw_dt
        res.append({'r': r, 'dt': dt_obj if pd.notnull(dt_obj) else datetime.max.replace(tzinfo=None), 'n': n.lower(), 'g': gv, 'ft': ft, 'dd': disp_d})

    res.sort(key=lambda x: (not x['ft'], x['dt'], x['n'], x['g']))
    h = "<style>body{font-family:sans-serif;}.card{background:white;padding:20px;border-radius:15px;border-left:10px solid #800000;margin-bottom:18px;box-shadow:0 4px 15px rgba(0,0,0,0.05);}.title{color:#800000;font-size:1.1rem;font-weight:800;margin-bottom:10px;}.venue{color:#008080;font-weight:800;text-transform:uppercase;}.btn{background:#800000;color:white!important;padding:8px 12px;border-radius:8px;text-decoration:none;font-size:0.75rem;font-weight:700;display:inline-block;margin-top:10px;margin-right:5px;}</style>"
    for i in res:
        r, d, f, ds = i['r'], i['dt'], i['ft'], i['dd']
        is_ac = "academic" in str(r.iloc[2]).lower() or any(x in str(r.iloc[3]).lower() for x in ["afrikaans", "eat", "ht", "math"])
        age = cl(r.iloc[11])
        pre = "Gr " if is_ac else "U"
        age_d = f"{pre}{age} " if (age and not (any(x in str(r.iloc[3]).lower() for x in ["swimming", "athletics"]) and not age)) else ""
        title = f"{tr(str(r.iloc[3]), str(r.iloc[3]))} {age_d}{tr(cl(r.iloc[4]), str(r.iloc[3]))}".strip()
        if sq and sq.lower() not in title.lower(): continue
        date_str = "FULL TERM" if f else ds
        b1, b2 = ("Document", "Assessment Details") if is_ac else ("Programme", "Team List")
        btns = ""
        if "http" in str(r.iloc[7]).lower(): btns += f"<a href='
