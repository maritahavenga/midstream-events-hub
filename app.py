import streamlit as st
import pandas as pd
import requests
import io
from datetime import datetime
import pytz
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

# 1. Konfigurasie
st.set_page_config(page_title="LMCP Digital Hub", layout="centered")
st_autorefresh(interval=120000, key="datarefresh")

EVENTS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

def clean_val(val):
    """Verwyder .0 en ander Excel-geraas."""
    v = str(val).replace(".0", "").replace("nan", "").replace("NAN", "").strip()
    return "" if v.lower() == "n/a" else v

@st.cache_data(ttl=2)
def load_data(url):
    try:
        r = requests.get(f"{url}&cb={datetime.now().timestamp()}", timeout=10)
        df = pd.read_csv(io.StringIO(r.content.decode('utf-8')))
        return df.fillna("")
    except:
        return pd.DataFrame()

# Branding
st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", use_container_width=True)
st.markdown("<div style='background:#008080; color:white; text-align:center; padding:15px; font-size:1.4rem; font-weight:700; border-bottom: 5px solid #800000;'>Laerskool Midstream College Primary Digital Hub</div>", unsafe_allow_html=True)

df_raw = load_data(EVENTS_URL)
SA_TIME = pytz.timezone('Africa/Johannesburg')
today = datetime.now(SA_TIME).date()

if not df_raw.empty:
    df = df_raw.copy()
    
    # TREK DATA STRENG VOLGENS KOLOMME
    # Kolom D (3) = Activity
    # Kolom E (4) = Age Group
    # Kolom L (11) = Team
    
    h = """<style>
        body { background:#008080; font-family: sans-serif; padding:10px; } 
        .card { background:white; padding:20px; border-radius:15px; border-left:10px solid #800000; margin-bottom:15px; position:relative; box-shadow:0 4px 8px rgba(0,0,0,0.1); } 
        .card-title { color:#800000; font-size:1.25rem; font-weight:bold; margin-bottom:10px; } 
        .info-row { font-size:0.95rem; color:#333; margin: 8px 0; font-weight: 500; }
        .teal-link { color:#008080 !important; text-decoration:underline; font-weight:800; }
        .btn { background:#800000 !important; color:white !important; padding:8px 12px; border-radius:8px; text-decoration:none; font-size:0.75rem; display:inline-block; margin-right:5px; margin-top:10px; font-weight:bold; } 
        .badge { position:absolute; top:15px; right:15px; background:#FFD700; color:#800000; padding:4px 8px; border-radius:5px; font-weight:bold; font-size:0.65rem; animation: blinker 1.2s linear infinite; } 
        @keyframes blinker { 50% { opacity: 0.3; } }
    </style>"""

    # Verwerk datums vir sortering
    df['dt_fixed'] = pd.to_datetime(df.iloc[:, 5], dayfirst=True, errors='coerce')
    df = df[df['dt_fixed'].dt.date >= today]
    df = df.sort_values(by=['dt_fixed', df.columns[3]])

    for _, r in df.iterrows():
        # Bou die titel: [Activity] [Age] [Team]
        act = clean_val(r.iloc[3])
        age = clean_val(r.iloc[4])
        team = clean_val(r.iloc[11])
        
        # Voeg slegs 'U' by as die Age 'n skoon nommer is
        display_age = f"U{age}" if age.isdigit() else age
        
        final_title = f"{act} {display_age} {team}".replace("  ", " ").strip()
        
        f_date = f"🗓️ {r['dt_fixed'].strftime('%d %B %Y')}"
        ven_raw = clean_val(r.iloc[6]).upper()
        
        # Venue Skakel
        m_q = f"Midstream+College+{ven_raw.replace(' ', '+')}"
        ven_html = f"📍 <a class='teal-link' href='https://www.google.com/maps/search/?api=1&query={m_q}' target='_blank'>{ven_raw}</a>"

        badge = "<div class='badge'>UPDATE</div>" if "$" in str(r.iloc[10]) else ""
        
        # Knoppies (7=Prog, 8=Team, 10=Info)
        btns = ""
        for i, lbl in zip([7, 8, 10], ["PROGRAMME", "TEAM LIST", "INFO"]):
            val = str(r.iloc[i]).strip()
            if "http" in val.lower():
                btns += f"<a href='{val}' target='_blank' class='btn'>{lbl}</a> "

        h += f"<div class='card'>{badge}<div class='card-title'>{final_title}</div><div class='info-row'>{f_date}</div><div class='info-row'>{ven_html}</div><div>{btns}</div></div>"
    
    components.html(h, height=2500, scrolling=True)

st.markdown("<div style='background:#800000; color:white; text-align:center; padding:15px; font-size:0.8rem;'>Laerskool Midstream College Primary · Digital Hub 2026</div>", unsafe_allow_html=True)
