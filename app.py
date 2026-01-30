import streamlit as st
import pandas as pd
import requests, io, re, pytz
from datetime import datetime

st.set_page_config(page_title="LMCP Hub", layout="centered")

# --- BANNER (Netjies en Skoon) ---
st.markdown("""
<div style='text-align:center; padding: 10px;'>
    <img src='https://raw.githubusercontent.com/LMCPEventsHub/midstream-events-hub/main/LMCP_RGB%20(1).png' width='170'>
    <h1 style='color:#800000; font-family:sans-serif; margin-bottom:0;'>LAERSKOOL MIDSTREAM COLLEGE PRIMARY</h1>
    <p style='color:#008080; font-size:1.2rem; margin-top:5px; font-weight:bold;'>Digital Event Hub</p>
</div>
""", unsafe_allow_html=True)

U = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?output=csv"

def cl(v): return str(v).replace(".0", "").replace("nan", "").strip()

@st.cache_data(ttl=1)
def ld():
    try:
        r = requests.get(f"{U}&ts={datetime.now().timestamp()}", timeout=15)
        return pd.read_csv(io.StringIO(r.content.decode('utf-8')), dtype=str).fillna("")
    except: return pd.DataFrame()

df = ld()

if not df.empty:
    # --- FILTER BOKS (Grys agtergrond vir professionele look) ---
    st.markdown("<div style='background-color:#f9f9f9; padding:20px; border-radius:15px; border:1px solid #eee; margin-bottom:20px;'>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1: sc = st.multiselect("Category", ["Sport", "Culture", "Academics"])
    with c2: 
        act_list = sorted(list(df.iloc[:, 3].unique()))
        sa = st.multiselect("Activity", act_list)
    with c3: 
        sg = st.multiselect("Age Group", ["Gr 1","Gr 2","Gr 3","Gr 4","Gr 5","Gr 6","Gr 7","U7","U8","U9","U10","U11","U12","U13"])
    sq = st.text_input("🔍 Search Events", placeholder="Type event name...")
    st.markdown("</div>", unsafe_allow_html=True)
    now = datetime.now(pytz.timezone("Africa/Johannesburg")).date()
    res = []

    for _, r in df.iterrows():
        try:
            cat, act, desc, date_str, ven, age = str(r.iloc[2]), str(r.iloc[3]), str(r.iloc[4]), str(r.iloc[5]), str(r.iloc[6]), cl(r.iloc[11])
            dt = pd.to_datetime(date_str, dayfirst=True, errors="coerce")
            if pd.notnull(dt) and dt.date() < now: continue
            if sc and not any(x.lower() in cat.lower() for x in sc): continue
            if sa and not any(x in act for x in sa): continue
            if sg and not any(v.replace("Gr ","").replace("U","") in age for v in sg): continue
            res.append({"r": r, "dt": dt if pd.notnull(dt) else datetime(2099, 1, 1), "ds": date_str, "desc": desc})
        except: continue

    res.sort(key=lambda x: x['dt'])

    if not res:
        st.info("No upcoming events found.")
    else:
        for i in res:
            r = i["r"]
            act, age, ven = str(r.iloc[3]), cl(r.iloc[11]), str(r.iloc[6])
            t_l, i_r = cl(r.iloc[8]), cl(r.iloc[10])
            
            # U / Gr Label Logika
            is_sp = any(x.lower() in act.lower() for x in ["hockey","rugby","netball","swimming","athletics","tennis"])
            prefix = "U" if is_sp else "Gr "
            age_lbl = f"{prefix}{age}" if age else ""
            
            full_title = f"{act} {age_lbl} {i['desc']}".strip()
            if sq and sq.lower() not in full_title.lower(): continue

            # --- DIE KAART ONTWERP ---
            with st.container():
                # Titel in Maroon
                st.markdown(f"### <span style='color:#800000;'>{full_title}</span>", unsafe_allow_html=True)
                
                # Datum en Venue (Teal ikoon gevoel)
                st.markdown(f"📅 **{i['ds']}**")
                if ven and ven != "nan":
                    map_url = f"http://googleusercontent.com/maps.google.com/search?q={ven.replace(' ','+')}+Midstream"
                    st.markdown(f"📍 <a href='{map_url}' target='_blank' style='color:#008080; font-weight:bold; text-decoration:none;'>{ven.upper()}</a>", unsafe_allow_html=True)

                # Notas & Spanne (Teal agtergrond boksies)
                if t_l and "http" not in t_l.lower():
                    st.info(f"**Teams:** {t_l}")
                if i_r and "http" not in i_r.lower():
                    st.success(f"**Note:** {i_r}") # Success gee 'n ligte groen/teal boksie

                # Knoppies langs mekaar
                is_afr = any(x in act.lower() for x in ["afrikaans", "eerste", "hooftaal"])
                b1, b2, b3 = ("Documents", "Team List", "Information")
                if is_afr: b1, b2, b3 = ("Dokumente", "Spanlys", "Inligting")
                
                col1, col2, col3 = st.columns([1,1,1])
                if "http" in cl(r.iloc[7]): col1.link_button(b1, r.iloc[7], use_container_width=True)
                if "http" in t_l: col2.link_button(b2, t_l, use_container_width=True)
                if "http" in i_r: col3.link_button(b3, i_r, use_container_width=True)
                
                st.markdown("<hr style='border: 0.5px solid #eee;'>", unsafe_allow_html=True)

st.markdown("<br><center style='font-size:0.8rem;color:#999;'>LAERSKOOL MIDSTREAM COLLEGE PRIMARY Digital Hub 2026</center>", unsafe_allow_html=True)
