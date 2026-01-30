import streamlit as st, pandas as pd, requests, io, re, pytz
from datetime import datetime
import streamlit.components.v1 as v1
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="LMCP Hub", layout="centered")
st_autorefresh(interval=120000, key="r_token")

U = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

def cl(v): return str(v).replace(".0", "").replace("nan", "").strip()

def tr(t, a):
    r = str(a).strip(); t = re.sub(r'\bG\b', 'Girls', t)
    if re.search(r'(?i)\b(EAT|HT|Hooftaal|Eerste)\b', r): 
        return "Afrikaans " + ("Eerste Addisionele Taal" if "eat" in r.lower() or "eerste" in r.lower() else "Hooftaal")
    d = {"Saal": "Hall", "Veld": "Field", "Atletiek": "Athletics", "Wiskunde": "Math"}
    for k, v in d.items(): t = re.sub(rf'\b{k}\b', v, t, flags=re.IGNORECASE)
    return t

def c_a(n):
    n = str(n).lower()
    for x in ["athletics", "atletiek", "hockey", "rugby", "netball", "netbal", "tennis"]:
        if x in n: return x.capitalize().replace("Netbal", "Netball").replace("Atletiek", "Athletics")
    if any(k in n for k in ["eat","ht","hooftaal","eerste"]): return "Afrikaans " + ("EAT" if "eat" in n else "HT")
    return n.capitalize()

@st.cache_data(ttl=10)
def ld():
    try:
        r = requests.get(U, timeout=8)
        return pd.read_csv(io.StringIO(r.content.decode('utf-8')), dtype=str).fillna("")
    except: return pd.DataFrame()

df = ld()
if not df.empty:
    st.markdown("<div style='background:#fff;padding:15px;border-radius:12px;border:1px solid #eee;box-shadow:0 4px 10px rgba(0,0,0,0.05);'>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1: sc = st.multiselect("Category", ["Sport", "Culture", "Academics"])
    with c2:
        m = df.iloc[:, 2].str.contains('|'.join(sc) if sc else ".*", case=False)
        if sc and "Academics" in sc: m |= df.iloc[:, 2].str.contains("academic", case=False)
        sa = st.multiselect("Activity", sorted(list({c_a(o) for o in df[m].iloc[:, 3]})))
    with c3:
        ao = ["Gr 1","Gr 2","Gr 3","Gr 4","Gr 5","Gr 6","Gr 7","U7","U8","U9","U10","U11","U12","U13"]
        opts = [o for o in ao if "U" in o] if sc==["Sport"] else ([o for o in ao if "Gr" in o] if sc and "Sport" not in str(sc) else ao)
        sg = st.multiselect("Age Group", options=opts, key="stk_v")
    sq = st.text_input("Search Events...")
    if st.button("🔄 Refresh Data"): st.cache_data.clear(); st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    tn = set()
    for s in sg:
        v_m = re.findall(r'\d+', s); v = int(v_m[0]) if v_m else 0
        if v: tn.update([v, v+6 if v<=7 else v-6])
    
    res = []
    for _, r in df.iterrows():
        cat, act, age, rd = str(r.iloc[2]).lower(), str(r.iloc[3]), cl(r.iloc[11]), cl(r.iloc[5])
        dt = pd.to_datetime(rd, dayfirst=True, errors='coerce')
        if sc and not (any(x.lower() in cat for x in sc) or ("Academics" in sc and "academic" in cat)): continue
        if sa and c_a(act) not in sa: continue
        v_m = re.findall(r'\d+', age); v_n = int(v_m[0]) if v_m else -1
        if tn and v_n not in tn: continue
        res.append({'r': r, 'dt': dt if pd.notnull(dt) else datetime(2099, 1, 1), 'ds': rd})
    
    res.sort(key=lambda x: x['dt'])
    
    # CSS vir die kaarte en die nota-boksie
    h = """<style>
    .card{background:white;padding:18px;border-radius:12px;border-left:10px solid #800000;margin-bottom:15px;box-shadow:0 4px 10px rgba(0,0,0,0.08);font-family:sans-serif;}
    .title{color:#800000;font-weight:bold;font-size:1.1rem;margin-bottom:8px;}
    .btn{background:#800000;color:white!important;padding:8px 15px;border-radius:8px;text-decoration:none;font-size:0.8rem;margin:5px 8px 0 0;display:inline-block;font-weight:500;}
    .nt{background:#f1f6f6!important;padding:12px;margin-top:12px;border-radius:8px;font-size:0.9rem;border-left:4px solid #008080;color:#333;display:block;clear:both;}
    </style>"""
    
    for i in res:
        r, ds = i['r'], i['ds']
        cv, act, age, ven, info_raw = str(r.iloc[2]).lower(), str(r.iloc[3]), cl(r.iloc[11]), cl(r.iloc[6]), cl(r.iloc[10])
        
        # Bepaal knoppie name
        ia, ic = "afrikaans" in act.lower() or "eat" in act.lower(), "academic" in cv or any(x in act.lower() for x in ["math", "science"])
        b1 = "Dokumente" if ia else ("Document" if ic else "Programme")
        b2 = "Assessment" if ic or ia else "Team List"
        
        # Genereer knoppies vanaf kolomme 7, 8 en 10 (as 10 'n link bevat)
        btns_list = []
        if "http" in cl(r.iloc[7]).lower(): btns_list.append(f"<a href='{cl(r.iloc[7])}' target='_blank' class='btn'>{b1}</a>")
        if "http" in cl(r.iloc[8]).lower(): btns_list.append(f"<a href='{cl(r.iloc[8])}' target='_blank' class='btn'>{b2}</a>")
        if "http" in info_raw.lower(): btns_list.append(f"<a href='{info_raw}' target='_blank' class='btn'>Information</a>")
        btns = "".join(btns_list)
        
        # Vertoon teks notas (haal link uit teks as dit daar is)
        clean_note = re.sub(r'http\S+', '', info_raw).strip()
        nt = f"<div class='nt'><b>Note:</b><br>{clean_note}</div>" if clean_note else ""
        
        al = (("U" if "sport" in cv else "Gr ") + age) if age else ""
        ts = f"{tr(act,act)} {al} {tr(cl(r.iloc[4]),act)}".strip()
        
        if sq and sq.lower() not in ts.lower(): continue
        
        vh = f"<div style='color:#008080;font-weight:bold;margin-top:8px;'>📍 <a href='http://googleusercontent.com/maps.google.com/search?q={ven.replace(' ','+')}+Midstream' target='_blank' style='color:#008080;text-decoration:none;'>{tr(ven, act).upper()}</a></div>" if ven else ""
        
        h += f"<div class='card'><div class='title'>{ts}</div><div style='color:#555;'>📅 {ds}</div>{vh}{nt}<div style='margin-top:12px;'>{btns}</div></div>"
    
    v1.html(h, height=3500, scrolling=True)

st.markdown("<center style='font-size:0.7rem;color:#999;'>LMCP Digital Hub 2026</center>", unsafe_allow_html=True)
