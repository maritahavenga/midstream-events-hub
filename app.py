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

# Gebruik die presiese skakel vanaf jou foto
U = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?output=csv"

def cl(v): return str(v).replace(".0", "").replace("nan", "").strip()

@st.cache_data(ttl=1)
def ld():
    try:
        # Die tydstempel dwing Google om vars data te gee
        r = requests.get(f"{U}&nocache={datetime.now().timestamp()}", timeout=15)
        if r.status_code == 200:
            df = pd.read_csv(io.StringIO(r.content.decode('utf-8')), dtype=str).fillna("")
            return df
        return pd.DataFrame()
    except:
        return pd.DataFrame()

df = ld()

if not df.empty:
    # --- FILTERS ---
    st.markdown("<div style='background-color:#f9f9f9; padding:20px; border-radius:15px; border:1px solid #eee; margin-bottom:20px;'>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    
    # Kry kolom-indekse (0:Timestamp, 3:Activity, 5:Date, 6:Venue, 11:Age)
    with c1: sc = st.multiselect("Category", sorted(df.iloc[:, 2].unique()) if len(df.columns) > 2 else [])
    with c2: sa = st.multiselect("Activity", sorted(df.iloc[:, 3].unique()) if len(df.columns) > 3 else [])
    with c3: sg = st.multiselect("Age Group", ["Gr 1","Gr 2","Gr 3","Gr 4","Gr 5","Gr 6","Gr 7","U7","U8","U9","U10","U11","U12","U13"])
    
    sq = st.text_input("🔍 Search", placeholder="Type to search...")
    st.markdown("</div>", unsafe_allow_html=True)

    now = datetime.now(pytz.timezone("Africa/Johannesburg")).date()
    res = []

    for _, r in df.iterrows():
        try:
            r_date = str(r.iloc[5]).strip()
            dt = pd.to_datetime(r_date, dayfirst=True, errors="coerce")
            
            # Formateer: 30 Januarie 2026
            pretty_date = dt.strftime("%#d %B %Y") if pd.notnull(dt) else r_date
            res.append({"r": r, "dt": dt, "ds": pretty_date})
        except:
            continue

    res.sort(key=lambda x: x['dt'] if pd.notnull(x['dt']) else datetime(2099,1,1))

    # --- KAARTE ---
    h = "<style>.card { background: white; padding: 20px; border-radius: 12px; border-left: 10px solid #800000; margin-bottom: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); font-family: sans-serif; }</style>"
    
    for i in res:
        r = i["r"]
        # Tennis en Afrikaans fix
        act = str(r.iloc[3]).replace("U13 C", "U13C").replace("Afrikaans FAL", "Afrikaans Eerste Addisionele Taal")
        ven = str(r.iloc[6])
        
        h += f"<div class='card'><b style='color:#800000; font-size:1.2rem;'>{act}</b><br><span style='color:#555;'>📅 {i['ds']}</span><br><b style='color:#008080;'>📍 {ven.upper()}</b></div>"

    import streamlit.components.v1 as components
    components.html(f"<html><body>{h}</body></html>", height=3000, scrolling=True)

else:
    st.info("🔄 Besig om data vanaf Google te trek... Verfris die bladsy as dit langer as 'n minuut neem.")
    if st.button("Force Refresh"):
        st.cache_data.clear()
        st.rerun()

st.markdown("<br><center style='font-size:0.8rem;color:#999;'>LAERSKOOL MIDSTREAM COLLEGE PRIMARY Digital Hub 2026</center>", unsafe_allow_html=True)
