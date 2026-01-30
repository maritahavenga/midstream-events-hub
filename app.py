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

# JOU CSV SKAKEL
U = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?output=csv"

def cl(v): return str(v).replace(".0", "").replace("nan", "").strip()

def fix_text(t):
    t = re.sub(r'(U\d+)\s+([A-D])', r'\1\2', t)
    t = t.replace("Afrikaans FAL", "Afrikaans Eerste Addisionele Taal").replace("HT", "Hooftaal")
    t = re.sub(rf'\b(g|G|dogters|meisies|Dogters|Meisies)\b', 'Girls', t)
    return t

@st.cache_data(ttl=1)
def ld():
    try:
        r = requests.get(f"{U}&ts={datetime.now().timestamp()}", timeout=15)
        df = pd.read_csv(io.StringIO(r.content.decode('utf-8')), dtype=str).fillna("")
        return df
    except: return pd.DataFrame()

df = ld()

if not df.empty:
    # --- FILTERS ---
    st.markdown("<div style='background-color:#f9f9f9; padding:20px; border-radius:15px; border:1px solid #eee; margin-bottom:20px;'>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1: sc = st.multiselect("Category", sorted(df.iloc[:, 2].unique()))
    with c2: sa = st.multiselect("Activity", sorted(df.iloc[:, 3].unique()))
    with c3: sg = st.multiselect("Age Group", ["Gr 1","Gr 2","Gr 3","Gr 4","Gr 5","Gr 6","Gr 7","U7","U8","U9","U10","U11","U12","U13"])
    sq = st.text_input("🔍 Search", placeholder="Type to search...")
    st.markdown("</div>", unsafe_allow_html=True)

    res = []
    for _, r in df.iterrows():
        try:
            r_date = str(r.iloc[5]).strip()
            dt = pd.to_datetime(r_date, dayfirst=True, errors="coerce")
            
            # ONS VERWYDER DIE "BEFORE NOW" FILTER TYDELIK SODAT JY ALLES KAN SIEN
            pretty_date = dt.strftime("%#d %B %Y") if pd.notnull(dt) else r_date
            res.append({"r": r, "dt": dt, "ds": pretty_date})
        except: continue

    res.sort(key=lambda x: x['dt'] if pd.notnull(x['dt']) else datetime(2099,1,1))

    h = """<style>
    .card { background: white; padding: 20px; border-radius: 12px; border-left: 10px solid #800000; margin-bottom: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); font-family: sans-serif; }
    .title { color: #800000; font-weight: bold; font-size: 1.2rem; }
    .date { color: #555; font-weight: 600; margin-bottom: 8px; }
    .venue { color: #008080; font-weight: bold; margin-bottom: 12px; }
    .btn { background: #800000; color: white !important; padding: 10px 16px; border-radius: 8px; text-decoration: none; font-size: 0.85rem; font-weight: bold; display: inline-block; margin-right: 10px; margin-top: 10px; }
    </style>"""

    for i in res:
        r = i["r"]
        act = fix_text(str(r.iloc[3]))
        desc = fix_text(str(r.iloc[4]))
        ven = str(r.iloc[6])
        age = cl(r.iloc[11])
        
        full_title = f"{act} {age} {desc}".strip()
        if sq and sq.lower() not in full_title.lower(): continue
        
        btns = ""
        if "http" in cl(r.iloc[7]): btns += f"<a class='btn' href='{cl(r.iloc[7])}' target='_blank'>Info</a>"
        if "http" in cl(r.iloc[8]): btns += f"<a class='btn' href='{cl(r.iloc[8])}' target='_blank'>Teams</a>"

        h += f"<div class='card'><div class='title'>{full_title}</div><div class='date'>📅 {i['ds']}</div><div class='venue'>📍 {ven.upper()}</div>{btns}</div>"
    
    import streamlit.components.v1 as components
    components.html(f"<html><body>{h}</body></html>", height=3000, scrolling=True)

else:
    st.warning("⚠️ Die app kan die sheet bereik, maar die blad is leeg. Kontroleer jou Google Sheet.")
