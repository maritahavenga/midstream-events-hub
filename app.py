import streamlit as st, pandas as pd, requests, io, re, pytz
from datetime import datetime

st.set_page_config(page_title="LMCP Hub", layout="centered")

# --- BANNER MET VOLLE SKOOLNAAM ---
st.markdown("""
    <div style='text-align: center;'>
        <img src='https://raw.githubusercontent.com/LMCPEventsHub/midstream-events-hub/main/LMCP_RGB%20(1).png' width='160'>
        <h1 style='color: #800000; font-family: sans-serif; margin-top: 10px;'>LAERSKOOL MIDSTREAM COLLEGE PRIMARY</h1>
        <h3 style='color: #008080; font-family: sans-serif; font-weight: normal;'>Digital Hub</h3>
        <hr style='border: 1px solid #eee;'>
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
    with st.expander("🔍 Filter Events", expanded=True):
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
            sg = st.multiselect("Age Group", options=opts)
    
    sq = st.text_input("Search Events...", placeholder="Type here to filter...")
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

    for i in res:
        r, ds = i['r'], i['ds']
        cv, act, age, ven = str(r.iloc[2]).lower(), str(r.iloc[3]), cl(r.iloc[11]), cl(r.iloc[6])
        t_l, i_r = cl(r.iloc[8]), cl(r.iloc[10])

        is_sport_card = "sport" in cv or any(x in c_a(act) for x in ["Tennis","Rugby","Hockey","Netball","Athletics"])
        age_lbl = (("U" if is_sport_card else "Gr ") + age) if age else ""
        title_text = f"{c_a(act)} {age_lbl} {tr(cl(r.iloc[4]), act)}"

        if sq and sq.lower() not in title_text.lower(): continue

        with st.container():
            st.markdown(f"### <span style='color:#800000;'>{title_text}</span>", unsafe_allow_html=True)
            
            c_meta1, c_meta2 = st.columns([1, 1])
            with c_meta1: st.markdown(f"📅 **{tr(ds, act)}**")
            with c_meta2:
                if ven:
                    map_url = f"https://www.google.com/maps/search/?api=1&query={ven.replace(' ','+')}+Midstream"
                    st.markdown(f"📍 [**{tr(ven, act).upper()}**]({map_url})")

            # Hockey Dotted Box
            if "Hockey" in c_a(act) and t_l and "http" not in t_l.lower():
                st.markdown(f"""<div style="border: 2px dotted #800000; padding: 10px; border-radius: 8px; color: #800000; font-weight: bold; margin-bottom: 10px;">Teams: {t_l}</div>""", unsafe_allow_html=True)
            elif t_l and "http" not in t_l.lower():
                st.info(f"**Teams:** {t_l}")

            if i_r and "http" not in i_r.lower():
                st.info(f"**Note:** {i_r}")

            is_afr = any(x in act.lower() for x in ["afrikaans", "eerste", "hooftaal"])
            b1, b2, b_info = ("Documents", "Team List", "Information")
            if is_afr: b1, b2, b_info = "Dokumente", "Assessering", "Inligting"
            elif "academic" in cv: b2 = "Assessment"

            cb1, cb2, cb3 = st.columns(3)
            if "http" in cl(r.iloc[7]).lower(): cb1.link_button(b1, cl(r.iloc[7]), use_container_width=True)
            if "http" in t_l.lower(): cb2.link_button(b2, t_l, use_container_width=True)
            if "http" in i_r.lower(): cb3.link_button(b_info, i_r, use_container_width=True)
            
            st.markdown("---")

st.markdown("<center style='color:gray; font-size:0.8rem;'>LAERSKOOL MIDSTREAM COLLEGE PRIMARY Digital Hub 2026</center>", unsafe_allow_html=True)
