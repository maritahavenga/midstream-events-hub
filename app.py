import streamlit as st, pandas as pd, requests, io, re, pytz
from datetime import datetime

st.set_page_config(page_title="LMCP Hub", layout="centered")

# --- BANNER (Skoon & Stewig) ---
st.markdown("""
    <div style='text-align: center; background-color: #008080; padding: 20px; border-radius: 15px; border-bottom: 8px solid #800000;'>
        <h1 style='color: white; font-family: sans-serif; margin: 0;'>LAERSKOOL MIDSTREAM COLLEGE PRIMARY</h1>
        <h3 style='color: #eee; font-family: sans-serif; font-weight: normal;'>Digital Hub</h3>
    </div>
""", unsafe_allow_html=True)

U = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig+2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

def cl(v): return str(v).replace(".0", "").replace("nan", "").strip()

def tr(t, a):
    t = str(t).replace("-", " ").replace("/", " ")
    m_map = {"Jan":"January","Feb":"February","Fev":"February","Mar":"March","Apr":"April","May":"May","Jun":"June","Jul":"July","Aug":"August","Sep":"September","Oct":"October","Nov":"November","Dec":"December"}
    for k, v in m_map.items(): t = re.sub(rf'\b{k}\b', v, t)
    d = {"Saal":"Hall","Veld":"Field","Atletiek":"Athletics","Wiskunde":"Math","G":"Girls"}
    for k, v in d.items(): t = re.sub(rf'\b{k}\b', v, t, flags=re.IGNORECASE)
    return t

def c_a(n):
    n = str(n).lower()
    if "eat" in n or "eerste" in n: return "Afrikaans Eerste Addisionele Taal"
    if "ht" in n or "hooftaal" in n: return "Afrikaans Hooftaal"
    for x in ["athletics","atletiek","hockey","rugby","netball","netbal","tennis"]:
        if x in n: return x.capitalize().replace("Netbal","Netball").replace("Atletiek","Athletics")
    return n.capitalize()

@st.cache_data(ttl=1)
def ld():
    try:
        r = requests.get(U, timeout=10)
        return pd.read_csv(io.StringIO(r.content.decode('utf-8')), dtype=str).fillna("")
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return pd.DataFrame()

df = ld()

if not df.empty:
    with st.container():
        st.write("")
        c1, c2, c3 = st.columns(3)
        with c1: sc = st.multiselect("Category", ["Sport", "Culture", "Academics"])
        with c2:
            m = df.iloc[:, 2].str.contains('|'.join(sc) if sc else ".*", case=False)
            sa = st.multiselect("Activity", sorted(list({c_a(o) for o in df[m].iloc[:, 3]})))
        with c3:
            ao = ["Gr 1","Gr 2","Gr 3","Gr 4","Gr 5","Gr 6","Gr 7","U7","U8","U9","U10","U11","U12","U13"]
            sg = st.multiselect("Age Group", options=ao)
    
    sq = st.text_input("Search Events...", placeholder="Search here...")
    st.markdown("---")
    res = []
    # Ons gebruik 'Johannesburg' tyd vir vandag
    tz = pytz.timezone('Africa/Johannesburg')
    vandaar = datetime.now(tz).date()

    for _, r in df.iterrows():
        cat, act, age, rd = str(r.iloc[2]).lower(), str(r.iloc[3]), cl(r.iloc[11]), cl(r.iloc[5])
        
        # Probeer datum lees, maar moenie breek as dit faal nie
        dt = pd.to_datetime(rd, dayfirst=True, errors='coerce')
        
        # FILTER: Wys vandag en alles in die toekoms
        if pd.notnull(dt) and dt.date() < vandaar: continue
        
        # Pas filters toe
        if sc and not any(x.lower() in cat for x in sc): continue
        if sa and c_a(act) not in sa: continue
        if sg and not any(str(v) in age for v in sg): continue
        
        res.append({'r': r, 'dt': dt if pd.notnull(dt) else datetime(2099, 1, 1), 'ds': rd})

    # Sorteer datums
    res.sort(key=lambda x: x['dt'])

    if not res:
        st.warning("No upcoming events found for your selection. Try refreshing or changing filters.")
    else:
        for i in res:
            r, ds = i['r'], i['ds']
            act, age, ven = str(r.iloc[3]), cl(r.iloc[11]), cl(r.iloc[6])
            t_l, i_r = cl(r.iloc[8]), cl(r.iloc[10])
            
            # Age Label
            is_sport = any(x in act.lower() for x in ["hockey", "rugby", "tennis", "netball", "athletics"])
            age_lbl = (("U" if is_sport else "Gr ") + age) if age else ""
            display_title = f"{c_a(act)} {age_lbl} {tr(cl(r.iloc[4]), act)}"
            
            if sq and sq.lower() not in display_title.lower(): continue

            # --- DIE KAART ---
            st.markdown(f"### <span style='color:#800000;'>{display_title}</span>", unsafe_allow_html=True)
            st.write(f"📅 **{tr(ds, act)}**")
            
            if ven:
                map_url = f"https://www.google.com/maps/search/?api=1&query={ven.replace(' ','+')}+Midstream"
                st.markdown(f"📍 [**{tr(ven, act).upper()}**]({map_url})")

            # Teal-gevoel Notas
            if (t_l and "http" not in t_l.lower()) or (i_r and "http" not in i_r.lower()):
                with st.expander("📌 View Teams & Notes", expanded=True):
                    if "Hockey" in act and t_l and "http" not in t_l.lower():
                        st.error(f"TEAMS: {t_l}") # Dotted/Rooi gevoel vir Hockey
                    elif t_l and "http" not in t_l.lower():
                        st.info(f"TEAMS: {t_l}")
                    if i_r and "http" not in i_r.lower():
                        st.info(f"NOTE: {i_r}")

            # Knoppies
            is_afr = any(x in act.lower() for x in ["afrikaans", "eerste", "hooftaal"])
            b1, b2, b3 = ("Documents", "Team List", "Information")
            if is_afr: b1, b2, b3 = ("Dokumente", "Assessering", "Inligting")
            
            c_b1, c_b2, c_b3 = st.columns(3)
            if "http" in cl(r.iloc[7]).lower(): c_b1.link_button(b1, cl(r.iloc[7]))
            if "http" in t_l.lower(): c_b2.link_button(b2, t_l)
            if "http" in i_r.lower(): c_b3.link_button(b3, i_r)
            
            st.markdown("---")

st.markdown("<center style='color:gray; font-size:0.8rem;'>LAERSKOOL MIDSTREAM COLLEGE PRIMARY Digital Hub 2026</center>", unsafe_allow_html=True)
