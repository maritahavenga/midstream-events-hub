import streamlit as st, pandas as pd, requests, io, re, pytz
from datetime import datetime
import streamlit.components.v1 as v1
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="LMCP Hub", layout="centered")
st_autorefresh(interval=120000, key="r_token")

# --- BANNER MET LOGO EN VOLLE SKOOLNAAM ---
st.markdown("""
    <div style='background-color: #008080; padding: 25px; border-radius: 15px; text-align: center; margin-bottom: 25px; border-bottom: 8px solid #800000;'>
        <img src='https://raw.githubusercontent.com/LMCPEventsHub/midstream-events-hub/main/LMCP_RGB%20(1).png' width='160' style='margin-bottom:10px;'>
        <h1 style='color: white; font-family: sans-serif; margin: 0; font-size: 1.5rem;'>LAERSKOOL MIDSTREAM COLLEGE PRIMARY</h1>
        <p style='color: #eee; font-family: sans-serif; font-size: 1.2rem; margin: 5px 0 0 0;'>Digital Hub</p>
    </div>
""", unsafe_allow_html=True)

U = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig+2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

def cl(v): return str(v).replace(".0", "").replace("nan", "").strip()

def tr(t, a):
    t = t.replace("-", " ").replace("/", " ")
    m_map = {"Jan":"January","Feb":"February","Fev":"February","Mar":"March","Apr":"April","May":"May","Jun":"June","Jul":"July","Aug":"August","Sep":"September","Oct":"October","Nov":"November","Dec":"December"}
    for k, v in m_map.items(): t = re.sub(rf'\b{k}\b', v, t)
    d = {"Saal":"Hall","Veld":"Field","Atletiek":"Athletics","Wiskunde":"Math","G":"Girls"}
    for k, v in d.items(): t = re.sub(rf'\b{k}\b', v, t, flags=re.IGNORECASE)
    return t

def c_a(n):
    n = str(n).lower()
    for x in ["athletics","atletiek","hockey","rugby","netball","netbal","tennis"]:
        if x in n: return x.capitalize().replace("Netbal","Netball").replace("Atletiek","Athletics")
    if "eat" in n or "eerste" in n: return "Afrikaans Eerste Addisionele Taal"
    if "ht" in n or "hooftaal" in n: return "Afrikaans Hooftaal"
    return n.capitalize()

@st.cache_data(ttl=1)
def ld():
    try:
        r = requests.get(U, timeout=8)
        return pd.read_csv(io.StringIO(r.content.decode('utf-8')), dtype=str).fillna("")
    except: return pd.DataFrame()

df = ld()
if not df.empty:
    st.markdown("<div style='background:#ffffff;padding:20px;border-radius:15px;border:1px solid #eeeeee;box-shadow:0 4px 15px rgba(0,0,0,0.05);margin-bottom:25px;'>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1: sc = st.multiselect("Category", ["Sport", "Culture", "Academics"])
    with c2:
        m = df.iloc[:, 2].str.contains('|'.join(sc) if sc else ".*", case=False)
        if sc and "Academics" in sc: m |= df.iloc[:, 2].str.contains("academic", case=False)
        sa = st.multiselect("Activity", sorted(list({c_a(o) for o in df[m].iloc[:, 3]})))
    with c3:
        ao = ["Gr 1","Gr 2","Gr 3","Gr 4","Gr 5","Gr 6","Gr 7","U7","U8","U9","U10","U11","U12","U13"]
        is_sp = "Sport" in sc or any(x in ["Tennis","Rugby","Hockey","Netball","Athletics"] for x in sa)
        is_ac = "Academics" in sc or any("Afrikaans" in x for x in sa)
        opts = [o for o in ao if "U" in o] if (is_sp and not is_ac) else ([o for o in ao if "Gr" in o] if (is_ac and not is_sp) else ao)
        sg = st.multiselect("Age Group", options=opts, key="stk_v")
    sq = st.text_input("Search Events...", placeholder="Type to filter results...")
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
        if pd.notnull(dt) and dt.date() < now: continue
        if sc and not (any(x.lower() in cat for x in sc) or ("Academics" in sc and "academic" in cat)): continue
        if sa and c_a(act) not in sa: continue
        v_m = re.findall(r'\d+', age); v_n = int(v_m[0]) if v_m else -1
        if tn and v_n not in tn: continue
        res.append({'r': r, 'dt': dt if pd.notnull(dt) else datetime(2099, 1, 1), 'ds': rd})
    
    res.sort(key=lambda x: x['dt'])

    h = """<style>
    .card{background:white!important;padding:20px;border-radius:12px;border-left:10px solid #800000;margin-bottom:15px;box-shadow: 0 4px 12px rgba(0,0,0,0.08);font-family:sans-serif;}
    .title{color:#800000!important;font-weight:bold;font-size:1.15rem;margin-bottom:8px;}
    .venue{color:#008080!important;font-weight:bold;margin-top:8px;text-transform:uppercase;letter-spacing:0.5px;}
    .btn{background:#800000;color:white!important;padding:8px 16px;border-radius:8px;text-decoration:none;font-size:0.85rem;margin:8px 8px 0 0;display:inline-block;font-weight:500;}
    .nt-box{background:#e0f2f1;padding:12px;margin-top:10px;border-radius:8px;font-size:0.95rem;color:#333;border-left:5px solid #800000;line-height:1.4;}
    .hockey-team{border: 2px dotted #800000; background:#ffffff; padding:10px; margin-bottom:10px; border-radius:8px; font-weight:bold; color:#800000;}
    </style>"""
    
    for i in res:
        r, ds = i['r'], i['ds']
        cv, act, age, ven = str(r.iloc[2]).lower(), str(r.iloc[3]), cl(r.iloc[11]), cl(r.iloc[6])
        t_l, i_r = cl(r.iloc[8]), cl(r.iloc[10])
        is_afr = "afrikaans" in act.lower() or "eerste" in act.lower() or "hooftaal" in act.lower()
        is_hockey = "hockey" in act.lower()
        
        b1, b_info = ("Dokumente", "Inligting") if is_afr else ("Documents", "Information")
        b2 = "Team List" if not ("academic" in cv or is_afr) else ("Assessment" if not is_afr else "Assessering")
        
        btns = "".join([f"<a href='{cl(r.iloc[j])}' target='_blank' class='btn'>{b1 if j==7 else (b2 if j==8 else b_info)}</a>" for j in [7, 8, 10] if "http" in cl(r.iloc[j]).lower()])
        t_txt = f"<div class='hockey-team'>Teams: {t_l}</div>" if is_hockey and t_l and "http" not in t_l.lower() else (f"<b>Teams:</b><br>{t_l}<br><br>" if t_l and "http" not in t_l.lower() else "")
        n_txt = f"<b>Note:</b><br>{i_r}" if i_r and "http" not in i_r.lower() else ""
        content = f"<div class='nt-box'>{t_txt}{n_txt}</div>" if t_txt or n_txt else ""
        
        age_lbl = (("U" if ("sport" in cv or any(x in c_a(act) for x in ["Tennis","Rugby","Hockey","Netball","Athletics"])) else "Gr ") + age) if age else ""
        ts = f"{c_a(act)} {age_lbl} {tr(cl(r.iloc[4]), act)}".strip()
        if sq and sq.lower() not in ts.lower(): continue
        
        map_url = f"https://www.google.com/maps/search/?api=1&query={ven.replace(' ','+')}+Midstream"
        vh = f"<div class='venue'>📍 <a href='{map_url}' target='_blank' style='color:#008080;text-decoration:none;'>{tr(ven, act).upper()}</a></div>" if ven else ""
        
        h += f"<div class='card'><div class='title'>{ts}</div><div style='color:#555;'>📅 {tr(ds, act)}</div>{vh}{content}<div style='margin-top:10px;'>{btns}</div></div>"
    
    # Gebruik 'height=3000' om seker te maak alle kaarte pas in die boks
    v1.html(h, height=3000, scrolling=True)

st.markdown("<br><center style='font-size:0.8rem;color:#999;'>LAERSKOOL MIDSTREAM COLLEGE PRIMARY Digital Hub 2026</center>", unsafe_allow_html=True)
