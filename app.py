import streamlit as st
import pandas as pd
import requests, io, re, pytz
from datetime import datetime

st.set_page_config(page_title="LMCP Hub", layout="centered")

st.markdown("""
<div style='text-align:center; padding: 10px;'>
    <img src='https://raw.githubusercontent.com/LMCPEventsHub/midstream-events-hub/main/LMCP_RGB%20(1).png' width='180'>
    <h1 style='color:#800000; font-family:sans-serif; margin-bottom:0;'>LAERSKOOL MIDSTREAM COLLEGE PRIMARY</h1>
    <p style='color:#008080; font-size:1.2rem; margin-top:5px; font-weight:bold;'>Digital Event Hub</p>
</div>
""", unsafe_allow_html=True)

U = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?output=csv"

def cl(v): return str(v).replace(".0", "").replace("nan", "").strip()

def fix_text(t):
    t = re.sub(r'(U\d+)\s+([A-D])', r'\1\2', t)
    if any(x in t for x in ["Afrikaans", "FAL", "HT", "Eerste"]):
        t = t.replace("Afrikaans Afrikaans FAL", "Afrikaans Eerste Addisionele Taal")
        t = t.replace("Afrikaans FAL", "Afrikaans Eerste Addisionele Taal")
        t = t.replace("HT", "Hooftaal")
    t = re.sub(rf'\b(g|G|dogters|meisies|Dogters|Meisies)\b', 'Girls', t)
    return t

@st.cache_data(ttl=1)
def ld():
    try:
        r = requests.get(f"{U}&ts={datetime.now().timestamp()}", timeout=15)
        return pd.read_csv(io.StringIO(r.content.decode('utf-8')), dtype=str).fillna("")
    except: return pd.DataFrame()

df = ld()

if not df.empty:
    # KOLOMME VOLGENS JOU LYS (0-gebaseer)
    # 2:Cat, 3:Act, 4:Team/Assess(Desc), 5:Date, 6:Ven, 7:Doc, 8:TeamLink, 10:Info, 11:Age
    C_CAT, C_ACT, C_DESC, C_DATE, C_VEN, C_DOC, C_TEAM, C_INFO, C_AGE = 2, 3, 4, 5, 6, 7, 8, 10, 11

    st.markdown("<div style='background-color:#f9f9f9; padding:20px; border-radius:15px; border:1px solid #eee; margin-bottom:20px;'>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1: sc = st.multiselect("Category", ["Sport", "Culture", "Academics"])
    with c2: 
        act_list = sorted(list(df.iloc[:, C_ACT].unique()))
        sa = st.multiselect("Activity", act_list)
    with c3: 
        sg = st.multiselect("Age Group", ["Gr 1","Gr 2","Gr 3","Gr 4","Gr 5","Gr 6","Gr 7","U7","U8","U9","U10","U11","U12","U13"])
    sq = st.text_input("🔍 Search Events", placeholder="Type to search...")
    st.markdown("</div>", unsafe_allow_html=True)

    # VANDAG SE DATUM (SA TYD)
    now = datetime.now(pytz.timezone("Africa/Johannesburg")).date()
    res = []

    for _, r in df.iterrows():
        try:
            r_date = str(r.iloc[C_DATE]).strip()
            if not r_date or r_date == "": continue
            
            # Slim leser wat nie omgee oor die formaat nie
            dt = pd.to_datetime(r_date, dayfirst=True, errors="coerce")
            
            # VERWYDER TYDELIK DIE DATUM-FILTER OM TE SIEN OF DATA WYS
            # if pd.notnull(dt) and dt.date() < now: continue
            
            # FILTERS (as gebruiker kies)
            if sc and not any(x.lower() in str(r.iloc[C_CAT]).lower() for x in sc): continue
            if sa and not any(x in str(r.iloc[C_ACT]) for x in sa): continue
            if sg and not any(v.replace("Gr ","").replace("U","") in cl(r.iloc[C_AGE]) for v in sg): continue

            # Formateer vir vertoon
            pretty_date = dt.strftime("%d %B %Y") if pd.notnull(dt) else r_date
            res.append({"r": r, "dt": dt, "ds": pretty_date})
        except: continue

    # Sorteer
    res.sort(key=lambda x: x['dt'] if pd.notnull(x['dt']) else datetime(2099,1,1))

    h = """<style>
    .card { background: white; padding: 20px; border-radius: 12px; border-left: 10px solid #800000; margin-bottom: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); font-family: sans-serif; }
    .title { color: #800000; font-weight: bold; font-size: 1.1rem; }
    .date { color: #555; font-weight: 600; font-size: 0.9rem; }
    .venue { color: #008080; font-weight: bold; font-size: 0.9rem; margin-top: 5px; }
    .nt-box { background: #f0f7f7; padding: 10px; border-radius: 8px; border-left: 3px solid #008080; margin-top: 10px; font-size: 0.85rem; }
    .btn { background: #800000; color: white !important; padding: 8px 12px; border-radius: 6px; text-decoration: none; font-size: 0.8rem; font-weight: bold; display: inline-block; margin-right: 8px; margin-top: 10px; }
    </style>"""

    if not res:
        st.warning("⚠️ Data gelaai, maar geen rye pas by die filters nie. Maak seker daar is data in die sheet.")
    else:
        for i in res:
            r = i["r"]
            act = fix_text(str(r.iloc[C_ACT]))
            desc = fix_text(str(r.iloc[C_DESC]))
            ven = str(r.iloc[C_VEN])
            age = cl(r.iloc[C_AGE])
            t_l, i_r = cl(r.iloc[C_TEAM]), cl(r.iloc[C_INFO])

            is_sp = any(x.lower() in act.lower() for x in ["hockey","rugby","netball","swimming","athletics","tennis"])
            age_lbl = f"{('U' if is_sp else 'Gr ')}{age}" if age else ""
            full_title = f"{act} {age_lbl} {desc}".strip()
            
            if sq and sq.lower() not in full_title.lower(): continue

            nt_html = ""
            if t_l and "http" not in t_l.lower(): nt_html += f"<div class='nt-box'><b>Teams:</b><br>{t_l}</div>"
            if i_r and "http" not in i_r.lower(): nt_html += f"<div class='nt-box'><b>Note:</b><br>{i_r}</div>"

            # Knoppies
            is_afr = any(x in full_title.lower() for x in ["afrikaans", "eerste", "hooftaal"])
            b1, b2 = ("Documents", "Team List") if not is_afr else ("Dokumente", "Spanlys")
            
            btns = ""
            if "http" in cl(r.iloc[C_DOC]): btns += f"<a class='btn' href='{cl(r.iloc[C_DOC])}' target='_blank'>{b1}</a>"
            if "http" in t_l: btns += f"<a class='btn' href='{t_l}' target='_blank'>{b2}</a>"
            if "http" in i_r: btns += f"<a class='btn' href='{i_r}' target='_blank'>Info</a>"

            map_url = f"https://www.google.com/maps/search/?api=1&query={ven.replace(' ','+')}"
            vh = f"<div class='venue'>📍 <a href='{map_url}' target='_blank' style='color:#008080;text-decoration:none;'>{ven.upper()}</a></div>" if ven and ven != "nan" else ""

            h += f"<div class='card'><div class='title'>{full_title}</div><div class='date'>📅 {i['ds']}</div>{vh}{nt_html}<div>{btns}</div></div>"
        
        import streamlit.components.v1 as components
        components.html(f"<html><body>{h}</body></html>", height=3500, scrolling=True)

st.markdown("<br><center style='font-size:0.8rem;color:#999;'>LAERSKOOL MIDSTREAM COLLEGE PRIMARY Digital Hub 2026</center>", unsafe_allow_html=True)
