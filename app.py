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

# Skakel bevestig vanaf jou foto
U = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?output=csv"

def cl(v): return str(v).replace(".0", "").replace("nan", "").strip()

@st.cache_data(ttl=1)
def ld():
    try:
        # Die timestamp dwing Google om vars data te stuur
        r = requests.get(f"{U}&v={datetime.now().timestamp()}", timeout=20)
        if r.status_code == 200:
            df = pd.read_csv(io.StringIO(r.content.decode('utf-8')), dtype=str).fillna("")
            return df
        return pd.DataFrame()
    except:
        return pd.DataFrame()

df = ld()

if not df.empty:
    # --- SLIM KOLOM IDENTIFIKASIE ---
    cols = list(df.columns)
    # Ons soek die regte kolomme selfs as hulle skuif
    idx_act = next((i for i, c in enumerate(cols) if "Activity" in c), 3)
    idx_date = next((i for i, c in enumerate(cols) if "Date" in c), 5)
    idx_ven = next((i for i, c in enumerate(cols) if "Venue" in c), 6)
    idx_cat = next((i for i, c in enumerate(cols) if "Category" in c), 2)
    idx_age = next((i for i, c in enumerate(cols) if "Age" in c or "Grade" in c), 11)

    # --- FILTERS ---
    st.markdown("<div style='background-color:#f9f9f9; padding:20px; border-radius:15px; border:1px solid #eee; margin-bottom:20px;'>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1: sc = st.multiselect("Category", sorted(df.iloc[:, idx_cat].unique()))
    with c2: sa = st.multiselect("Activity", sorted(df.iloc[:, idx_act].unique()))
    with c3: sg = st.multiselect("Age Group", ["Gr 1","Gr 2","Gr 3","Gr 4","Gr 5","Gr 6","Gr 7","U7","U8","U9","U10","U11","U12","U13"])
    sq = st.text_input("🔍 Search Events", placeholder="Type to search...")
    st.markdown("</div>", unsafe_allow_html=True)

    now = datetime.now(pytz.timezone("Africa/Johannesburg")).date()
    res = []

    for _, r in df.iterrows():
        try:
            r_date = str(r.iloc[idx_date]).strip()
            dt = pd.to_datetime(r_date, dayfirst=True, errors="coerce")
            
            # Filter slegs toekomstige events
            if pd.notnull(dt) and dt.date() < now: continue
            
            pretty_date = dt.strftime("%#d %B %Y") if pd.notnull(dt) else r_date
            res.append({"r": r, "dt": dt, "ds": pretty_date})
        except: continue

    res.sort(key=lambda x: x['dt'] if pd.notnull(x['dt']) else datetime(2099,1,1))

    # --- STYLE & KAARTE ---
    h = "<style>.card { background: white; padding: 20px; border-radius: 12px; border-left: 10px solid #800000; margin-bottom: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); font-family: sans-serif; }</style>"
    
    for i in res:
        r = i["r"]
        act = str(r.iloc[idx_act]).replace("U13 C", "U13C").replace("Afrikaans FAL", "Afrikaans Eerste Addisionele Taal")
        ven = str(r.iloc[idx_ven])
        age = cl(r.iloc[idx_age])
        
        # Soek-filter
        if sq and sq.lower() not in (act + ven + age).lower(): continue

        h += f"""
        <div class='card'>
            <div style='color:#800000; font-weight:bold; font-size:1.2rem;'>{act} {age}</div>
            <div style='color:#555; margin-top:5px;'>📅 {i['ds']}</div>
            <div style='color:#008080; font-weight:bold; margin-top:5px;'>📍 {ven.upper()}</div>
        </div>
        """
    import streamlit.components.v1 as components
    components.html(f"<html><body>{h}</body></html>", height=3000, scrolling=True)

else:
    st.info("🔄 Besig om data vanaf Google te trek... Verfris asseblief die bladsy oor 30 sekondes.")
    if st.button("Manual Force Refresh"):
        st.cache_data.clear()
        st.rerun()

st.markdown("<br><center style='font-size:0.8rem;color:#999;'>LAERSKOOL MIDSTREAM COLLEGE PRIMARY Digital Hub 2026</center>", unsafe_allow_html=True)
