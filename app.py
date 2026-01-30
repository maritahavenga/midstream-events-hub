import streamlit as st
import pandas as pd
import requests, io, re, pytz
from datetime import datetime

st.set_page_config(page_title="LMCP Hub", layout="centered")

# --- BANNER ---
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
    # 1. Tennis Spasie Fix (U13 C -> U13C)
    t = re.sub(r'(U\d+)\s+([A-D])', r'\1\2', t)
    # 2. Afrikaans Vak Vertalings
    if any(x in t for x in ["Afrikaans", "FAL", "HT", "Eerste", "Hooftaal"]):
        t = t.replace("Afrikaans Afrikaans FAL", "Afrikaans Eerste Addisionele Taal")
        t = t.replace("Eerste Addissionele Taal (Afrikaans FAL)", "Afrikaans Eerste Addisionele Taal")
        t = t.replace("Afrikaans FAL", "Afrikaans Eerste Addisionele Taal")
        t = t.replace("HT", "Hooftaal")
    # 3. Girls Vertaling (G, g, dogters, meisies)
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
            
            # --- GOOGLE FORM KALENDER FIX ---
            # Dit hanteer YYYY-MM-DD (Form) en DD/MM/YYYY (Manual)
            dt = pd.to_datetime(date_str, dayfirst=True, errors="coerce")
            
            if pd.notnull(dt) and dt.date() < now: continue
            
            # Formateer vir vertoon: 11 February 2026
            pretty_date = dt.strftime("%-d %B %Y") if pd.notnull(dt) else date_str
            res.append({"r": r, "dt": dt, "ds": pretty_date, "desc": desc})
        except: continue

    res.sort(key=lambda x: x['dt'] if pd.notnull(x['dt']) else datetime(2099,1,1))

    h = """
    <style>
    .card { background: white !important; padding: 20px !important; border-radius: 12px !important; border-left: 10px solid #800000 !important; margin-bottom: 20px !important; box-shadow: 0 4px 10px rgba(0,0,0,0.1) !important; font-family: sans-serif !important; }
    .title { color: #800000 !important; font-weight: bold !important; font-size: 1.2rem !important; margin-bottom: 5px !important; }
    .date { color: #555 !important; font-weight: 600 !important; margin-bottom: 8px !important; }
    .venue { color: #008080 !important; font-weight: bold !important; margin-bottom: 12px !important; }
    .nt-box { background: #f0f7f7 !important; padding: 12px !important; border-radius: 8px !important; border-left: 4px solid #008080 !important; margin-bottom: 8px !important; font-size: 0.9rem !important; color: #333 !important; }
    .btn-row { display: flex !important; gap: 10px !important; margin-top: 15px !important; flex-wrap: wrap !important; }
    .btn { background: #800000 !important; color: white !important; padding: 10px 16px !important; border-radius: 8px !important; text-decoration: none !important; font-size: 0.85rem !important; font-weight: bold !important; display: inline-block !important; }
    </style>
    """

    if not res:
        st.info("Geen opkomende events gevind nie.")
    else:
        for i in res:
            r = i["r"]
            act_raw, age, ven = str(r.iloc[3]), cl(r.iloc[11]), str(r.iloc[6])
            t_l, i_r = cl(r.iloc[8]), cl(r.iloc[10])
            
            act = fix_text(act_raw)
            desc_clean = fix_text(i['desc'])
            
            is_sp = any(x.lower() in act.lower() for x in ["hockey","rugby","netball","swimming","athletics","tennis"])
            prefix = "U" if is_sp else "Gr "
            age_lbl = f"{prefix}{age}" if age else ""
            
            full_title = f"{act} {age_lbl} {desc_clean}".strip()
            if sq and sq.lower() not in full_title.lower(): continue

            # Notas in aparte boksies
            nt_html = ""
            if t_l and "http" not in t_l.lower():
                nt_html += f"<div class='nt-box'><b>Teams:</b><br>{t_l}</div>"
            if i_r and "http" not in i_r.lower():
                nt_html += f"<div class='nt-box'><b>Note:</b><br>{i_r}</div>"

            # Knoppies
            is_afr = any(x in full_title.lower() for x in ["afrikaans", "eerste", "hooftaal"])
            b1, b2, b3 = ("Documents", "Team List", "Information") if not is_afr else ("Dokumente", "Spanlys", "Inligting")
            
            btns = ""
            if "http" in cl(r.iloc[7]): btns += f"<a class='btn' href='{cl(r.iloc[7])}' target='_blank'>{b1}</a>"
            if "http" in t_l: btns += f"<a class='btn' href='{t_l}' target='_blank'>{b2}</a>"
            if "http" in i_r: btns += f"<a class='btn' href='{i_r}' target='_blank'>{b3}</a>"

            # Universele Google Maps skakel
            map_url = f"https://www.google.com/maps/search/?api=1&query={ven.replace(' ','+')}"
            vh = f"<div class='venue'>📍 <a href='{map_url}' target='_blank' style='color:#008080;text-decoration:none;'>{ven.upper()}</a></div>" if ven and ven != "nan" else ""

            h += f"""
            <div class='card'>
                <div class='title'>{full_title}</div>
                <div class='date'>📅 {i['ds']}</div>
                {vh}
                {nt_html}
                <div class='btn-row'>{btns}</div>
            </div>
            """
        import streamlit.components.v1 as components
        components.html(f"<html><body>{h}</body></html>", height=3500, scrolling=True)

st.markdown("<br><center style='font-size:0.8rem;color:#999;'>LAERSKOOL MIDSTREAM COLLEGE PRIMARY Digital Hub 2026</center>", unsafe_allow_html=True)
