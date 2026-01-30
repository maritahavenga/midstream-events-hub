import streamlit as st
import pandas as pd
import requests
import io
import re
import pytz
from datetime import datetime

st.set_page_config(page_title="LMCP Hub", layout="centered")

# --- BANNER (SUIWER STREAMLIT VIR STABILITEIT) ---
st.image("https://raw.githubusercontent.com/LMCPEventsHub/midstream-events-hub/main/LMCP_RGB%20(1).png", width=160)
st.title("LAERSKOOL MIDSTREAM COLLEGE PRIMARY")
st.subheader("Digital Event Hub")
st.markdown("---")

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
        r = requests.get(U, timeout=15)
        return pd.read_csv(io.StringIO(r.content.decode('utf-8')), dtype=str).fillna("")
    except:
        return pd.DataFrame()

df = ld()

if not df.empty:
    with st.expander("🔍 Filter Events", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1: sc = st.multiselect("Category", ["Sport", "Culture", "Academics"])
        with c2:
            m = df.iloc[:, 2].str.contains('|'.join(sc) if sc else ".*", case=False)
            sa = st.multiselect("Activity", sorted(list({c_a(o) for o in df[m].iloc[:, 3]})))
        with c3:
            ao = ["Gr 1","Gr 2","Gr 3","Gr 4","Gr 5","Gr 6","Gr 7","U7","U8","U9","U10","U11","U12","U13"]
            sg = st.multiselect("Age Group", options=ao)
    
    sq = st.text_input("Search Events...", placeholder="Type to search...")
    res = []
    tz = pytz.timezone('Africa/Johannesburg')
    today = datetime.now(tz).date()

    for _, r in df.iterrows():
        cat, act, age, rd = str(r.iloc[2]).lower(), str(r.iloc[3]), cl(r.iloc[11]), cl(r.iloc[5])
        dt = pd.to_datetime(rd, dayfirst=True, errors='coerce')
        
        # Wys slegs vandag en toekoms
        if pd.notnull(dt) and dt.date() < today: continue
        
        # Pas filters toe
        if sc and not any(x.lower() in cat for x in sc): continue
        if sa and c_a(act) not in sa: continue
        if sg and not any(str(v) in age for v in sg): continue
        
        res.append({'r': r, 'dt': dt if pd.notnull(dt) else datetime(2099, 1, 1), 'ds': rd})

    res.sort(key=lambda x: x['dt'])

    if not res:
        st.info("No upcoming events found. Please check your filters.")
    else:
        for i in res:
            r, ds = i['r'], i['ds']
            act, age, ven = str(r.iloc[3]), cl(r.iloc[11]), cl(r.iloc[6])
            t_l, i_r = cl(r.iloc[8]), cl(r.iloc[10])
            
            is_sport = any(x in act.lower() for x in ["hockey", "rugby", "tennis", "netball", "athletics"])
            age_lbl = (("U" if is_sport else "Gr ") + age) if age else ""
            title = f"{c_a(act)} {age_lbl} {tr(cl(r.iloc[4]), act)}"
            
            if sq and sq.lower() not in title.lower(): continue

            # --- DIE KAART (Skoon Python-Uitleg) ---
            with st.container():
                st.subheader(title)
                st.write(f"📅 **{tr(ds, act)}**")
                
                if ven:
                    map_url = f"http://google.com/maps/search/{ven.replace(' ','+')}+Midstream"
                    st.markdown(f"📍 [**{tr(ven, act).upper()}**]({map_url})")

                # Notas & Spanne (In Teal-gevoel boksies)
                if (t_l and "http" not in t_l.lower()) or (i_r and "http" not in i_r.lower()):
                    if "Hockey" in act and t_l:
                        st.warning(f"TEAMS: {t_l}") # Dotted boksie alternatief
                    elif t_l:
                        st.info(f"TEAMS: {t_l}")
                    
                    if i_r:
                        st.info(f"NOTE: {i_r}")

                # Knoppies
                is_afr = any(x in act.lower() for x in ["afrikaans", "eerste", "hooftaal"])
                b1, b2, b3 = ("Documents", "Team List", "Information")
                if is_afr: b1, b2, b3 = ("Dokumente", "Assessering", "Inligting")
                
                cb1, cb2, cb3 = st.columns(3)
                if "http" in cl(r.iloc[7]).lower(): cb1.link_button(b1, cl(r.iloc[7]), use_container_width=True)
                if "http" in t_l.lower(): cb2.link_button(b2, t_l, use_container_width=True)
                if "http" in i_r.lower(): cb3.link_button(b3, i_r, use_container_width=True)
                
                st.markdown("---")

st.markdown("<br><center style='color:gray; font-size:0.8rem;'>LAERSKOOL MIDSTREAM COLLEGE PRIMARY Digital Hub 2026</center>", unsafe_allow_html=True)
