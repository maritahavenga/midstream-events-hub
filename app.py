import streamlit as st
import pandas as pd
import requests, io, re, pytz
from datetime import datetime, timedelta
import streamlit.components.v1 as v1

st.set_page_config(page_title="LMCP Hub", layout="centered")

# --- BANNER ---
st.markdown("""
<div style='text-align:center;margin-bottom:20px;'>
<img src='https://raw.githubusercontent.com/LMCPEventsHub/midstream-events-hub/main/LMCP_RGB%20(1).png' width='180'>
<h1 style='color:#800000;margin-bottom:0;font-family:sans-serif;'>LAERSKOOL MIDSTREAM COLLEGE PRIMARY</h1>
<p style='color:#008080;font-size:1.2rem;margin-top:5px;font-family:sans-serif;'>Digital Hub</p>
</div>
""", unsafe_allow_html=True)

U = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig-2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

# --- DATA LOAD ---
@st.cache_data(ttl=1)
def load_data():
    try:
        # Ons dwing Google om die varsste data te stuur
        response = requests.get(f"{U}&ts={datetime.now().timestamp()}", timeout=15)
        if response.status_code == 200:
            return pd.read_csv(io.StringIO(response.content.decode('utf-8')), dtype=str).fillna("")
        else:
            st.error(f"Google Sheet fout: Status {response.status_code}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Konneksie Fout: {e}")
        return pd.DataFrame()

df = load_data()

# --- AS DATA LAAI ---
if not df.empty:
    # 🔄 Refresh Knoppie heel bo-aan
    if st.button("🔄 REFRESH DATA"):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    
    # Filters
    c1, c2, c3 = st.columns(3)
    with c1: sc = st.multiselect("Category", ["Sport", "Culture", "Academics"])
    with c2: 
        activities = sorted(list(df.iloc[:, 3].unique()))
        sa = st.multiselect("Activity", activities)
    with c3: 
        sg = st.multiselect("Age Group", ["Gr 1","Gr 2","Gr 3","Gr 4","Gr 5","Gr 6","Gr 7","U7","U8","U9","U10","U11","U12","U13"])

    now = datetime.now(pytz.timezone("Africa/Johannesburg")).date()
    res = []

    for _, r in df.iterrows():
        try:
            cat, act, age, rd = str(r.iloc[2]).lower(), str(r.iloc[3]), str(r.iloc[11]), str(r.iloc[5])
            dt = pd.to_datetime(rd, dayfirst=True, errors="coerce")
            
            # Filter slegs as dit 'n geldige datum is en dit is in die verlede (voor gister)
            if pd.notnull(dt) and dt.date() < (now - timedelta(days=1)): continue
            
            # Kategorie filter
            if sc and not any(x.lower() in cat for x in sc): continue
            # Aktiwiteit filter
            if sa and not any(x in act for x in sa): continue
            # Ouderdom filter
            if sg and not any(v.replace("Gr ","").replace("U","") in age for v in sg): continue

            res.append({"r": r, "dt": dt if pd.notnull(dt) else datetime(2099, 1, 1), "ds": rd})
        except:
            continue

    res.sort(key=lambda x: x["dt"])

    # --- HTML KAARTE ---
    html_content = """<style>
    .card{background:white;padding:20px;border-radius:12px;border-left:10px solid #800000;margin-bottom:15px;box-shadow:0 4px 12px rgba(0,0,0,0.08);font-family:sans-serif;}
    .title{color:#800000;font-weight:bold;font-size:1.1rem;}
    .venue{color:#008080;font-weight:bold;margin-top:5px;}
    .btn{background:#800000;color:white!important;padding:8px 12px;border-radius:6px;text-decoration:none;font-size:0.8rem;margin-right:8px;display:inline-block;margin-top:10px;}
    </style>"""

    if not res:
        st.info("Geen data gevind vir vandag of die toekoms nie. Gaan asseblief die datums in die Google Sheet na.")
    else:
        for i in res:
            r = i["r"]
            act, age, ven = str(r.iloc[3]), str(r.iloc[11]), str(r.iloc[6])
            
            # U / Gr Label
            prefix = "U" if any(x in act.lower() for x in ["hockey","rugby","netball","swimming","athletics","tennis"]) else "Gr "
            age_lbl = f"{prefix}{age}" if age else ""
            
            title = f"{act} {age_lbl}".strip()
            
            # Knoppies
            b_html = ""
            if "http" in str(r.iloc[7]): b_html += f"<a class='btn' href='{r.iloc[7]}' target='_blank'>Documents</a>"
            if "http" in str(r.iloc[8]): b_html += f"<a class='btn' href='{r.iloc[8]}' target='_blank'>Teams</a>"
            if "http" in str(r.iloc[10]): b_html += f"<a class='btn' href='{r.iloc[10]}' target='_blank'>Info</a>"

            map_url = f"http://googleusercontent.com/maps.google.com/search?q={ven.replace(' ','+')}+Midstream" if ven else "#"

            html_content += f"""
            <div class='card'>
                <div class='title'>{title}</div>
                <div>📅 {i['ds']}</div>
                {f"<div class='venue'>📍 <a href='{map_url}' target='_blank' style='color:#008080;'>{ven.upper()}</a></div>" if ven else ""}
                <div>{b_html}</div>
            </div>
            """
        
        v1.html(html_content, height=2500, scrolling=True)

else:
    st.warning("⚠️ Die data kon nie van Google gelaai word nie. Maak seker die skakel is korrek gepubliseer as CSV.")

st.markdown("<center style='font-size:0.8rem;color:#999;'>LAERSKOOL MIDSTREAM COLLEGE PRIMARY Digital Hub 2026</center>", unsafe_allow_html=True)
