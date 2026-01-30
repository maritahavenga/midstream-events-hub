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
    if re.search(r'(?i)\b(EAT|Afrikaans Eerste Addisionele Taal)\b', s): 
        t = t.replace(a, "Afrikaans Eerste Addisionele Taal")
    elif re.search(r'(?i)\b(HT|Afrikaans Hooftaal)\b', s): 
        t = t.replace(a, "Afrikaans Hooftaal")
    if any(k in s.lower() for k in ["afrikaans", "eat", "ht"]): return t
    d = {"Saal": "Hall", "Veld": "Field", "Atletiek": "Athletics", "Wiskunde": "Math"}
    for k, v in d.items(): t = re.sub(rf'\b{k}\b', v, t, flags=re.IGNORECASE)
    return t

@st.cache_data(ttl=10)
def ld():
    try:
        r = requests.get(f"{URL}&cb={datetime.now().timestamp()}", timeout=5)
        return pd.read_csv(io.StringIO(r.content.decode('utf-8')), dtype=str).fillna("")
    except: return pd.DataFrame()

df = ld()
if not df.empty:
    with st.container():
        st.markdown("<div style='background:white;padding:20px;border-radius:12px;border:1px solid #eee;box-shadow:0 4px 12px rgba(0,0,0,0.05);margin-bottom:20px;'>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1: s_cat = st.multiselect("Category", ["Sport", "Culture", "Academics"])
        with c2:
            if s_cat:
                m = df.iloc[:, 2].str.contains('|'.join(s_cat), case=False, na=False)
                if "Academics" in s_cat: m |= df.iloc[:, 2].str.contains("academic", case=False, na=False)
                raw_opts = sorted(list(set(df[m].iloc[:, 3].str.strip())))
            else:
                raw_opts = sorted(list(set(df.iloc[:, 3].str.strip())))
            clean_opts = set()
            for o in raw_opts:
                lo = o.lower()
                if "athletics" in lo: clean_opts.add("Athletics")
                elif "hockey" in lo: clean_opts.add("Hockey")
                elif "netball" in lo: clean_opts.add("Netball")
                elif "rugby" in lo: clean_opts.add("Rugby")
                elif re.search(r'(?i)\b(EAT|Afrikaans EAT)\b', o): clean_opts.add("Afrikaans Eerste Addisionele Taal")
                elif re.search(r'(?i)\b(HT|Afrikaans HT)\b', o): clean_opts.add("Afrikaans Hooftaal")
                else: clean_opts.add(o)
            s_act = st.multiselect("Activity", sorted(list(clean_opts)))
        with c3:
            if s_cat and "Sport" in s_cat and len(s_cat) == 1: age_list = ["U7", "U8", "U9", "U10", "U11", "U12", "U13"]
            elif s_cat and ("Culture" in s_cat or "Academics" in s_cat) and "Sport" not in s_cat: age_list = ["Gr 1", "Gr 2", "Gr 3", "Gr 4", "Gr 5", "Gr 6", "Gr 7"]
            else: age_list = ["Gr 1","Gr 2","Gr 3","Gr 4","Gr 5","Gr 6","Gr 7","U7","U8","U9","U10","U11","U12","U13"]
            s_age = st.multiselect("Age Group", age_list)
        sq = st.text_input("Search")
        if st.button("REFRESH HUB", use_container_width=True): st.cache_data.clear(); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # --- DATUM FILTER: NET VANDAG EN TOEKOMS ---
    sa_tz = pytz.timezone('Africa/Johannesburg')
    today_dt = datetime.now(sa_tz).date()

    res = []
    for _, r in df.iterrows():
        n, cat_raw = str(r.iloc[3]), str(r.iloc[2])
        # Skoon filter-logika
        dn = n
        if "athletics" in n.lower(): dn = "Athletics"
        elif "hockey" in n.lower(): dn = "Hockey"
        elif "netball" in n.lower(): dn = "Netball"
        elif "rugby" in n.lower(): dn = "Rugby"
        elif re.search(r'(?i)\b(EAT|Afrikaans EAT)\b', n): dn = "Afrikaans Eerste Addisionele Taal"
        elif re.search(r'(?i)\b(HT|Afrikaans HT)\b', n): dn = "Afrikaans Hooftaal"

        if s_cat and not any(x.lower() in cat_raw.lower() or (x=="Academics" and "academic" in cat_raw.lower()) for x in s_cat): continue
        if s_act and dn not in s_act: continue
        
        rd = cl(r.iloc[5])
        dt = pd.to_datetime(rd, dayfirst=True, errors='coerce')
        ft = "full term" in str(r.iloc[12]).lower()
        
        # --- STRENG DATUM CHECK ---
        if not ft and pd.notnull(dt) and dt.date() < today_dt: continue
        
        if tn and not any(x in n.lower() for x in ["swimming", "athletics"]):
            vn = re.findall(r'\d+', cl(r.iloc[11]))
            if not (vn and int(vn[0]) in tn): continue
        
        gv = int(re.search(r'\d+', cl(r.iloc[11])).group()) if re.search(r'\d+', cl(r.iloc[11])) else 99
        res.append({'r':r, 'dt':dt if pd.notnull(dt) else datetime.max.replace(tzinfo=None), 'n':n.lower(), 'g':gv, 'ft':ft, 'dd':dt.strftime('%d %B %Y') if pd.notnull(dt) else rd, 'c':cat_raw})

    res.sort(key=lambda x: (not x['ft'], x['dt'], x['n'], x['g']))
    
    # --- CSS LOOK & FEEL
