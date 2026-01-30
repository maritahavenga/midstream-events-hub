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
        st.markdown("<div style='background:white;padding:20px;border-radius:12px;border:1px solid #eee;margin-bottom:20px;'>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1: 
            s_cat = st.multiselect("Category", ["Sport", "Culture", "Academics"])
        
        with c2:
            if s_cat:
                m = df.iloc[:, 2].str.contains('|'.join(s_cat), case=False, na=False)
                if "Academics" in s_cat: m |= df.iloc[:, 2].str.contains("academic", case=False, na=False)
                raw_opts = sorted(list(set(df[m].iloc[:, 3].str.strip())))
            else:
                raw_opts = sorted(list(set(df.iloc[:, 3].str.strip())))
            
            # --- SLIM FILTER SKOONMAAK ---
            clean_opts = set()
            for o in raw_opts:
                lower_o = o.lower()
                if "athletics" in lower_o: clean_opts.add("Athletics")
                elif "hockey" in lower_o: clean_opts.add("Hockey")
                elif "netball" in lower_o: clean_opts.add("Netball")
                elif "rugby" in lower_o: clean_opts.add("Rugby")
                elif re.search(r'(?i)\b(EAT|Afrikaans EAT)\b', o): clean_opts.add("Afrikaans Eerste Addisionele Taal")
                elif re.search(r'(?i)\b(HT|Afrikaans HT)\b', o): clean_opts.add("Afrikaans Hooftaal")
                else: clean_opts.add(o)
            s_act = st.multiselect("Activity", sorted(list(clean_opts)))
            
        with c3:
            if s_cat and "Sport" in s_cat and len(s_cat) == 1:
                age_list = ["U7", "U8", "U9", "U10", "U11", "U12", "U13"]
            elif s_cat and ("Culture" in s_cat or "Academics" in s_cat) and "Sport" not in s_cat:
                age_list = ["Gr 1", "Gr 2", "Gr 3", "Gr 4", "Gr 5", "Gr 6", "Gr 7"]
            else:
                age_list = ["Gr 1","Gr 2","Gr 3","Gr 4","Gr 5","Gr 6","Gr 7","U7","U8","U9","U10","U11","U12","U13"]
            s_age = st.multiselect("Age Group", age_list) # Opskrif verander na Age Group
            
        sq = st.text_input("Search")
        if st.button("REFRESH HUB", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    tn = set()
    for s in s_age:
        ns = re.findall(r'\d+', s)
        if ns:
            n = int(ns[0])
            tn.add(n)
            if n >= 7: tn.add(n-6)
            elif n <= 7: tn.add(n+6)

    res = []
    for _, r in df.iterrows():
        n, cat_raw = str(r.iloc[3]), str(r.iloc[2])
        
        # Identifiseer hoe hierdie ry in die skoon filter sou lyk
        dn = n
        lower_n = n.lower()
        if "athletics" in lower_n: dn = "Athletics"
        elif "hockey" in lower_n: dn = "Hockey"
        elif "netball" in lower_n: dn = "Netball"
        elif "rugby" in lower_n: dn = "Rugby"
        elif re.search(r'(?i)\b(EAT|Afrikaans EAT)\b', n): dn = "Afrikaans Eerste Addisionele Taal"
        elif re.search(r'(?i)\b(HT|Afrikaans HT)\b', n): dn = "Afrikaans Hooftaal"

        if s_cat and not any(x.lower() in cat_raw.lower() or (x=="Academics" and "academic" in cat_raw.lower()) for x in s_cat): continue
        if s_act and dn not in s_act: continue
        
        rd = cl(r.iloc[5])
        dt = pd.to_datetime(rd, dayfirst=True, errors='coerce')
        ft = "full term" in str(r.iloc[12]).lower()
        
        if tn and not any(x in n.lower() for x in ["swimming", "athletics"]):
            vn = re.findall(r'\d+', cl(r.iloc[11]))
            if not (vn and int(vn[0]) in tn): continue
        
        gv = int(re.search(r'\d+', cl(r.iloc[11])).group()) if re.search(r'\d+', cl(r.iloc[11])) else 99
        res.append({'r':r, 'dt':dt if pd.notnull(dt) else datetime.max.replace(tzinfo=None), 'n':n.lower(), 'g':gv, 'ft':ft, 'dd':dt.strftime('%d %B %Y') if pd.notnull(dt) else rd, 'c':cat_raw})

    res.sort(key=lambda x: (not x['ft'], x['dt'], x['n'], x['g']))
    
    h = "<style>body{font-family:sans-serif;}.card{background:white;padding:15px;border-radius:12px;border-left:8px solid #800000;margin-bottom:12px;box-shadow:0 2px 5px rgba(0,0,0,0.1);}.title{color:#800000;font-size:1.1rem;font-weight:bold;}.venue{color:#008080;font-weight:bold;text-transform:uppercase;}.btn{background:#800000;color:white!important;padding:6px 10px;border-radius:8px;text-decoration:none;font-size:0.7rem;display:inline-block;margin:5px 5px 0 0;}</style>"
    for i in res:
        r, f, ds, cv = i['r'], i['ft'], i['dd'], i['c']
        age = cl(r.iloc[11])
        pre = "U" if "sport" in cv.lower() else "Gr "
        age_d = f"{pre}{age} " if age else ""
        title = f"{tr(str(r.iloc[3]), str(r.iloc[3]))} {age_d}{tr(cl(r.iloc[4]), str(r.iloc[3]))}".strip()
        if sq and sq.lower() not in title.lower(): continue
        
        is_ac = "academic" in cv.lower() or any(x in str(r.iloc[3]).lower() for x in ["afrikaans", "eat", "ht", "math"])
        b1, b2 = ("Document", "Assessment Details") if is_ac else ("Programme", "Team List")
        btns = ""
        if "http" in str(r.iloc[7]).lower(): btns += f"<a href='{r.iloc[7]}' target='_blank' class='btn'>{b1}</a>"
        if "http" in str(r.iloc[8]).lower(): btns += f"<a href='{r.iloc[8]}' target='_blank' class='btn'>{b2}</a>"
        h += f"<div class='card'><div class='title'>{title}</div><div>📅 {'FULL TERM' if f else ds}</div><div class='venue'>📍 {tr(str(r.iloc[6]), str(r.iloc[3])).upper()}</div><div>{btns}</div></div>"
    
    components.html(h, height=2500, scrolling=True)
st.markdown("<center style='font-size:0.7rem;color:#999;'>LMCP Digital Hub 2026</center>", unsafe_allow_html=True)
