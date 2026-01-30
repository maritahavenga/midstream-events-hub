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
    t = re.sub(r'(U\d+)\s+([A-D])', r'\1\2', t) # Tennis U13C
    t = t.replace("Afrikaans FAL", "Afrikaans Eerste Addisionele Taal").replace("HT", "Hooftaal")
    t = re.sub(rf'\b(g|G|dogters|meisies|Dogters|Meisies)\b', 'Girls', t)
    return t

@st.cache_data(ttl=1)
def ld():
    try:
        r = requests.get(f"{U}&nocache={datetime.now().timestamp()}", timeout=15)
        df = pd.read_csv(io.StringIO(r.content.decode('utf-8')), dtype=str).fillna("")
        return df
    except: return pd.DataFrame()

df = ld()

if not df.empty:
    # --- KOLOM-MAPERING GEBASEER OP JOU LYS ---
    # Ons gebruik die name wat jy verskaf het om foute te voorkom
    try:
        # Hierdie is die name soos in jou Excel
        C_CAT = "Category"
        C_ACT = "Activity/Subject Name"
        C_DESC = "Team / Assessment"
        C_DATE = "Date / Due Date"
        C_VEN = "Venue"
        C_DOC = "Programme / Document Link"
        C_TEAM = "TeamConfirm"
        C_INFO = "Information"
        C_AGE = "Age Group (9,10) / Grade (1,2,3)"

        st.markdown("<div style='background-color:#f9f9f9; padding:20px; border-radius:15px; border:1px solid #eee; margin-bottom:20px;'>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1: sc = st.multiselect("Category", sorted(df[C_CAT].unique()))
        with c2: sa = st.multiselect("Activity", sorted(df[C_ACT].unique()))
        with c3: sg = st.multiselect("Age Group", ["Gr 1","Gr 2","Gr 3","Gr 4","Gr 5","Gr 6","Gr 7","U7","U8","U9","U10","U11","U12","U13"])
        sq = st.text_input("🔍 Search Events", placeholder="Type to search...")
        st.markdown("</div>", unsafe_allow_html=True)

        now = datetime.now(pytz.timezone("Africa/Johannesburg")).date()
        res = []

        for _, r in df.iterrows():
            try:
                r_date = str(r[C_DATE]).strip()
                dt = pd.to_datetime(r_date, dayfirst=True, errors="coerce")
                
                # Filter slegs vandag en toekoms
                if pd.notnull(dt) and dt.date() < now: continue
                
                pretty_date = dt.strftime("%-d %B %Y") if pd.notnull(dt) else r_date
                res.append({"r": r, "dt": dt, "ds": pretty_date})
            except: continue

        res.sort(key=lambda x: x['dt'] if pd.notnull(x['dt']) else datetime(2099,1,1))

        h = """<style>
        .card { background: white; padding: 20px; border-radius: 12px; border-left: 10px solid #800000; margin-bottom: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); font-family: sans-serif; }
        .title { color: #800000; font-weight: bold; font-size: 1.2rem; }
        .date { color: #555; font-weight: 600; margin-bottom: 8px; }
        .venue { color: #008080; font-weight: bold; margin-bottom: 12px; }
        .nt-box { background: #f0f7f7; padding: 10px; border-radius: 8px; border-left: 4px solid #008080; margin-bottom: 8px; font-size: 0.9rem; color: #333; }
        .btn { background: #800000; color: white !important; padding: 10px 16px; border-radius: 8px; text-decoration: none; font-size: 0.85rem; font-weight: bold; display: inline-block; margin-right: 10px; margin-top: 10px; }
        </style>"""

        if not res:
            st.info("Geen opkomende events gevind nie.")
        else:
            for i in res:
                r = i["r"]
                act = fix_text(str(r[C_ACT]))
                desc = fix_text(str(r[C_DESC]))
                ven = str(r[C_VEN])
                age = cl(r[C_AGE])
                
                is_sp = any(x.lower() in act.lower() for x in ["hockey","rugby","netball","swimming","athletics","tennis"])
                age_lbl = f"{('U' if is_sp else 'Gr ')}{age}" if age else ""
                full_title = f"{act} {age_lbl} {desc}".strip()
                
                if sq and sq.lower() not in full_title.lower(): continue

                t_l, i_r = cl(r[C_TEAM]), cl(r[C_INFO])
                nt_html = ""
                if t_l and "http" not in t_l.lower(): nt_html += f"<div class='nt-box'><b>Note:</b> {t_l}</div>"
                if i_r and "http" not in i_r.lower(): nt_html += f"<div class='nt-box'><b>Info:</b> {i_r}</div>"

                btns = ""
                if "http" in cl(r[C_DOC]): btns += f"<a class='btn' href='{cl(r[C_DOC])}' target='_blank'>Info</a>"
                if "http" in t_l: btns += f"<a class='btn' href='{t_l}' target='_blank'>Teams</a>"
                if "http" in i_r: btns += f"<a class='btn' href='{i_r}' target='_blank'>Information</a>"

                map_url = f"http://googleusercontent.com/maps.google.com/search?q={ven.replace(' ','+')}"
                vh = f"<div class='venue'>📍 <a href='{map_url}' target='_blank' style='color:#008080;text-decoration:none;'>{ven.upper()}</a></div>" if ven and ven != "nan" else ""

                h += f"<div class='card'><div class='title'>{full_title}</div><div class='date'>📅 {i['ds']}</div>{vh}{nt_html}<div>{btns}</div></div>"
            
            import streamlit.components.v1 as components
            components.html(f"<html><body>{h}</body></html>", height=3500, scrolling=True)

    except Exception as e:
        st.error(f"Kolom-fout: Maak seker die opskrifte in Excel is presies reg. Fout: {e}")

else:
    st.warning("🔄 Data word gelaai... Verfris die bladsy oor 'n paar sekondes.")

st.markdown("<br><center style='font-size:0.8rem;color:#999;'>LAERSKOOL MIDSTREAM COLLEGE PRIMARY Digital Hub 2026</center>", unsafe_allow_html=True)
