import streamlit as st, pandas as pd, requests, io, re, pytz
from datetime import datetime
import streamlit.components.v1 as v1
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="LMCP Hub", layout="centered")
st_autorefresh(interval=120000, key="r_token")

# 1. Die Skool Logo
st.markdown("<div style='text-align:center;'><img src='https://www.midstream-college.co.za/wp-content/uploads/2021/04/Midstream-College-Logo.png' width='180'><h2 style='color:#800000;font-family:sans-serif;'>LMCP Digital Hub</h2></div>", unsafe_allow_html=True)

U = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

def cl(v): return str(v).replace(".0", "").replace("nan", "").strip()

def tr(t, a):
    # 2. Skakel Feb om na February (Full Month)
    m_map = {"Jan":"January","Feb":"February","Fev":"February","Mar":"March","Apr":"April","May":"May","Jun":"June","Jul":"July","Aug":"August","Sep":"September","Oct":"October","Nov":"November","Dec":"December"}
    for k, v in m_map.items(): t = re.sub(rf'\b{k}\b', v, t)
    # Algemene vertalings
    d = {"Saal":"Hall","Veld":"Field","Atletiek":"Athletics","Wiskunde":"Math","G":"Girls"}
    for k, v in d.items(): t = re.sub(rf'\b{k}\b', v, t, flags=re.IGNORECASE)
    return t

def c_a(n):
    n = str(n).lower()
    for x in ["athletics","atletiek","hockey","rugby","netball","netbal","tennis"]:
        if x in n: return x.capitalize().replace("Netbal","Netball").replace("Atletiek","Athletics")
    if "eat" in n or "eerste" in n: return "Afrikaans FAL"
    if "ht" in n or "hooftaal" in n: return "Afrikaans HL"
    return n.capitalize()

@st.cache_data(ttl=1)
def ld():
    try:
        r = requests.get(U, timeout=8)
        return pd.read_csv(io.StringIO(r.content.decode('utf-8')), dtype=str).fillna("")
    except: return pd.DataFrame()

df = ld()
if not df.empty:
    st.markdown("<div style='background:#fff;padding:20px;border-radius:15px;border:1px solid #eee;box-shadow:0 4px 15px rgba(0,0,0,0.05);margin-bottom:25px;'>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1: sc = st.multiselect("Category", ["Sport", "Culture", "Academics"])
    with c2:
        m = df.iloc[:, 2].str.contains('|'.join(sc) if sc else ".*", case=False)
        if sc and "Academics" in sc: m |= df.iloc[:, 2].str.contains("academic", case=False)
        sa = st.multiselect("Activity", sorted(list({c_a(o) for o in df[m].iloc[:, 3]})))
    with c3:
        # 3. Slim Ouderdom Logika (U vs Gr)
        ao = ["Gr 1","Gr 2","Gr 3","Gr 4","Gr 5","Gr 6","Gr 7","U7","U8","U9","U10","U11","U12","U13"]
        is_sp = "Sport" in sc or any(x in ["Tennis","Rugby","Hockey","Netball","Athletics"] for x in sa)
        is_ac = "Academics" in sc or any("Afrikaans" in x for x in sa)
        opts = [o for o in ao if "U" in o] if (is_sp and not is_ac) else ([o for o in ao if "Gr" in o] if (is_ac and not is_sp) else ao)
        sg = st.multiselect("Age Group", options=opts, key="stk_v")
    sq = st.text_input("Search Events...")
    if st.button("🔄 Refresh Data"): st.cache_data.clear(); st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    now = datetime.now(pytz.timezone('Africa/Johannesburg')).date()
    tn = set()
    for s in sg:
        v_m = re.findall(r'\d+', s); v = int(v_m[0]) if v_m else 0
        if v: tn.update([v, v+6 if v<=7 else v-6])
    
    res = []
    for _, r in df.iterrows():
        cat, act, age, rd = str(r.iloc[2]).lower(), str(r.iloc[3]), cl(r.iloc[11]), cl(r.iloc[5])
        dt = pd.to_datetime(rd, dayfirst=True, errors='coerce')
        # 4. Filter verlede uit (20 Jan sal verdwyn)
        if pd.notnull(dt) and dt.date() < now: continue
        if sc and not (any(x.lower() in cat for x in sc) or ("Academics" in sc and "academic" in cat)): continue
        if sa and c_a(act) not in sa: continue
        v_m = re.findall(r'\d+', age); v_n = int(v_m[0]) if v_m else -1
        if tn and v_n not in tn: continue
        res.append({'r': r, 'dt': dt if pd.notnull(dt) else datetime(2099, 1, 1), 'ds': rd})
    
    res.sort(key=lambda x: x['dt'])
    h = "<style>.card{background:white;padding:20px;border-radius:12px;border-left:10px solid #800000;margin-bottom:15px;box-shadow:0 4px 12px rgba(0,0,0,0.08);font-family:sans-serif;}.title{color:#800000;font-weight:bold;font-size:1.1rem;margin-bottom:8px;}.btn{background:#800000;color:white!important;padding:8px 16px;border-radius:8px;text-decoration:none;font-size:0.85rem;margin:5px 8px 8px 0;display:inline-block;font-weight:500;}.nt{background:#f4f7f7!important;padding:12px;margin-top:12px;border-radius:8px;font-size:0.9rem;border-left:5px solid #008080;color:#333;display:block;clear:both;}</style>"
    
    for i in res:
        r, ds = i['r'], i['ds']
        cv, act, age, ven = str(r.iloc[2]).lower(), str(r.iloc[3]), cl(r.iloc[11]), cl(r.iloc[6])
        t_l, i_r = cl(r.iloc[8]), cl(r.iloc[10])
        
        # 5. Afrikaans Knoppie Uitsondering
        is_afr = "afrikaans" in act.lower() or "eat" in act.lower() or "ht" in act.lower()
        b1 = "Dokument" if is_afr else "Documents"
        b2 = "Team List" if not ("academic" in cv or is_afr) else ("Assessment" if not is_afr else "Assessering")
        b_info = "Inligting" if is_afr else "Information"
        
        btns_list = []
        if "http" in cl(r.iloc[7]).lower(): btns_list.append(f"<a href='{cl(r.iloc[7])}' target='_blank' class='btn'>{b1}</a>")
        if "http" in t_l.lower(): btns_list.append(f"<a href='{t_l}' target='_blank' class='btn'>{b2}</a>")
        if "http" in i_r.lower(): btns_list.append(f"<a href='{i_r}' target='_blank' class='btn'>{b_info}</a>")
        
        notes = []
        if t_l and "http" not in t_l.lower(): notes.append(f"<b>Teams:</b> {t_l}")
        if i_r and "http" not in i_r.lower(): notes.append(f"<b>Note:</b> {i_r}")
        
        # 6. Kaart-vlak U vs Gr Logika
        clean_act = c_a(act)
        is_sp_card = "sport" in cv or any(x in clean_act for x in ["Tennis","Rugby","Hockey","Netball","Athletics"])
        age_lbl = (("U" if is_sp_card else "Gr ") + age) if age else ""
        ts = f"{clean_act} {age_lbl} {tr(cl(r.iloc[4]), act)}".strip()
        
        if sq and sq.lower() not in ts.lower(): continue
        
        # 7. Regte Google Maps Skakel
        map_url = f"https://www.google.com/maps/search/?api=1&query={ven.replace(' ','+')}+Midstream"
        vh = f"<div style='color:#008080;font-weight:bold;margin-top:8px;'>📍 <a href='{map_url}' target='_blank' style='color:#008080;text-decoration:none;'>{tr(ven, act).upper()}</a></div>" if ven else ""
        
        h += f"<div class='card'><div class='title'>{ts}</div><div style='color:#555;'>📅 {tr(ds, act)}</div>{vh}{f'<div class=nt>{chr(10).join(notes)}</div>' if notes else ''}<div style='margin-top:15px;'>{''.join(btns_list)}</div></div>"
    
    v1.html(h, height=3500, scrolling=True)

st.markdown("<br><center style='font-size:0.8rem;color:#999;'>LMCP Digital Hub 2026</center>", unsafe_allow_html=True)
