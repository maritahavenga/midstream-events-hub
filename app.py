import streamlit as st, pandas as pd, requests, io, re, pytz
from datetime import datetime

st.set_page_config(page_title="LMCP Hub", layout="centered")

# --- LUUKSE PYTHON BANNER ---
st.title("LAERSKOOL MIDSTREAM COLLEGE PRIMARY")
st.subheader("Digital Hub")
st.markdown("---")

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
    
    sq = st.text_input("Search...", placeholder="Type here...")
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
        
        # Ouderdom Label
        is_sp_card = "sport" in cv or any(x in c_a(act) for x in ["Tennis","Rugby","Hockey","Netball","Athletics"])
        age_lbl = (("U" if is_sp_card else "Gr ") + age) if age else ""
        title_text = f"{c_a(act)} {age_lbl} {tr(cl(r.iloc[4]), act)}"
        
        if sq and sq.lower() not in title_text.lower(): continue

        # --- DIE KAART ---
        with st.container():
            st.markdown(f"### {title_text}")
            st.write(f"📅 **{tr(ds, act)}**")
            
            if ven:
                map_url = f"https://www.google.com/maps/search/?api=1&query={ven.replace(' ','+')}+Midstream"
                st.markdown(f"📍 [**{tr(ven, act).upper()}**]({map_url})")
            
            # Teal Notas (st.info in Streamlit is Teal)
            t_txt = f"**Teams:** {t_l}" if t_l and "http" not in t_l.lower() else ""
            n_txt = f"**Note:** {i_r}" if i_r and "http" not in i_r.lower() else ""
            
            if t_txt or n_txt:
                with st.chat_message("assistant", avatar="📌"):
                    if "Hockey" in title_text and t_txt:
                        st.warning(t_txt) # Dotted-gevoel boksie vir Hockey
                    if t_txt and not "Hockey" in title_text: st.write(t_txt)
                    if n_txt: st.write(n_txt)

            # Knoppies
            is_afr = "afrikaans" in act.lower() or "eerste" in act.lower() or "hooftaal" in act.lower()
            b1, b_info = ("Dokumente", "Inligting") if is_afr else ("Documents", "Information")
            b2 = "Team List" if not ("academic" in cv or is_afr) else ("Assessment" if not is_afr else "Assessering")
            
            col_b1, col_b2, col_b3 = st.columns([1,1,1])
            if "http" in cl(r.iloc[7]).lower(): col_b1.link_button(b1, cl(r.iloc[7]))
            if "http" in t_l.lower(): col_b2.link_button(b2, t_l)
            if "http" in i_r.lower(): col_b3.link_button(b_info, i_r)
            
            st.markdown("---")

st.markdown("<center style='color:gray;'>LAERSKOOL MIDSTREAM COLLEGE PRIMARY Digital Hub 2026</center>", unsafe_allow_html=True)
