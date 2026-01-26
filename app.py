import streamlit as st
import pandas as pd
import urllib.parse as up
import re
from datetime import datetime, timedelta
import pytz
import requests
import io
import time
from streamlit_autorefresh import st_autorefresh

# 1. Page Configuration
st.set_page_config(page_title="LMCP Live Fixtures", layout="centered")
st_autorefresh(interval=120000, key="datarefresh")

# 2. Styling (Maroon & Teal)
st.markdown("""<style>
#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
.stApp{background:#008080}.block-container{padding:1rem;max-width:500px}
.card{background:white!important;padding:18px;border-radius:15px;border-left:12px solid #800000;margin-bottom:15px;box-shadow:0 4px 10px rgba(0,0,0,0.2)}
.t{color:#800000!important;font-weight:bold;font-size:1.15rem;margin:5px 0}
.box{background:#f8f9fa;padding:12px;border-radius:10px;margin:10px 0;border-left:5px solid #008080;color:#333;font-size:0.9rem;white-space: pre-wrap;}
.team-box{background:#fff3f3;padding:10px;border-radius:8px;margin:5px 0;border:1px dashed #800000;color:#800000;font-size:0.85rem;}
.btn-row {display:flex!important; gap:4px!important; justify-content:space-between!important; margin-top:10px!important; width:100%!important; flex-wrap: wrap;}
.btn { flex:1 1 auto!important; background:#800000!important; color:white!important; text-align:center!important; text-decoration:none!important; font-weight:bold!important; font-size:0.65rem!important; padding:10px 5px!important; border-radius:6px!important; display:block!important;}
label { color:white !important; font-weight:bold; }
h2 { color: white !important; text-align: center; text-transform: uppercase; }
.stButton>button { width:100%; background-color:#800000; color:white; border:2px solid #00cccc; border-radius:10px; font-weight:bold;}
</style>
""", unsafe_allow_html=True)

URL_DATA = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?gid=0&single=true&output=csv"

def load_data():
    try:
        SA_TIME = pytz.timezone('Africa/Johannesburg')
        now = datetime.now(SA_TIME).date()
        # Dwing vars data
        response = requests.get(f"{URL_DATA}&cb={int(time.time())}", timeout=10)
        df = pd.read_csv(io.StringIO(response.content.decode('utf-8')))
        
        def parse_dt(x):
            s = str(x).strip()
            if not s or s.lower() == 'nan': return pd.NaT
            # As die jaar kort is, voeg 2026 by
            if '202' not in s: s = f"{s} 2026"
            return pd.to_datetime(s, dayfirst=True, errors='coerce')
        
        # Kolom 3 is Date
        df['dt_fixed'] = df.iloc[:, 3].apply(parse_dt)
        return df, now, datetime.now(SA_TIME)
    except:
        return pd.DataFrame(), datetime.now().date(), datetime.now()

st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", use_container_width=True)
df, today, up_time = load_data()

st.write(f"**App Status:** Connected | **Last Sync:** {up_time.strftime('%H:%M')}")

if st.button("🔄 FORCE REFRESH DATA"):
    st.cache_data.clear()
    st.rerun()

if not df.empty:
    # 1. Wys net toekomstige wedstryde (insluitend vandag)
    f_df = df[df['dt_fixed'].dt.date >= today].sort_values(by='dt_fixed')
    
    # 2. Wys die kaarte sonder enige filters wat dit kan blokkeer
    for i, r in f_df.iterrows():
        # Kolomme: 1=Act, 2=Age, 4=Venue
        sport = str(r.iloc[1])
        age = str(r.iloc[2]) if str(r.iloc[2]).lower() != 'nan' else ""
        date_str = r['dt_fixed'].strftime('%d %B %Y') if pd.notnull(r['dt_fixed']) else "Date TBA"
        venue = str(r.iloc[4])
        
        # Knoppies & Notas (5=Prog, 6=Team, 7=Conf, 8=Info)
        btns_html = ""
        team_txt = ""
        note_txt = ""
        
        for idx, lbl in [(5, "PROGRAMME"), (6, "TEAM"), (7, "CONFIRM"), (8, "INFORMATION")]:
            val = str(r.iloc[idx]).strip()
            if val.lower() == 'nan' or not val: continue
            
            link = re.search(r'(https?://[^\s<>"]+)', val)
            if link:
                btns_html += f'<a href="{link.group(0)}" target="_blank" class="btn">{lbl}</a>'
            else:
                if lbl == "TEAM": team_txt = val
                elif lbl == "INFORMATION": note_txt = val

        st.markdown(f"""
        <div class="card">
            <div style="font-size:0.85rem;color:#333">🗓️ {date_str}</div>
            <div class="t">{sport} {age}</div>
            <div style="font-size:0.85rem;color:#333">📍 {venue}</div>
            {f'<div class="team-box"><b>TEAMS:</b><br>{team_txt}</div>' if team_txt else ""}
            <div class="btn-row">{btns_html}</div>
            {f'<div class="box"><b>Note:</b><br>{note_txt}</div>' if note_txt else ""}
        </div>
        """, unsafe_allow_html=True)
else:
    st.error("Could not connect to the Google Sheet. Please check the URL.")

# Toets-area (Verwyder hierdie as alles werk)
if st.checkbox("Debug: Show Raw Data"):
    st.write(df.head())
