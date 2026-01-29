import streamlit as st
import pandas as pd
import requests
import io
import re
from datetime import datetime
import pytz
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

# 1. Konfigurasie
st.set_page_config(page_title="LMCP Digital Hub", layout="centered")
st_autorefresh(interval=120000, key="datarefresh")

EVENTS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

def clean_val(val):
    v = str(val).replace(".0", "").replace("nan", "").replace("NAN", "").strip()
    return "" if v.lower() in ["n/a", "none", ""] else v

def format_dle_spec(d_val, l_val, e_val):
    act = clean_val(d_val)
    age_raw = clean_val(l_val)
    team_raw = clean_val(e_val)
    
    # Gebruik regex om alle nommers met U te prefix: 10-13 -> U10-U13
    age_part = re.sub(r'(\d+)', r'U\1', age_raw)
    
    # Plak-logika vir Team letter (A, B, C)
    team_parts = team_raw.split(" ", 1)
    first_chunk = team_parts[0]
    rest = f" {team_parts[1]}" if len(team_parts) > 1 else ""
    
    if len(first_chunk) == 1 and first_chunk.isalpha():
        combined_le = f"{age_part}{first_chunk.upper()}{rest}"
    else:
        combined_le = f"{age_part} {team_raw}"

    return f"{act} {combined_le}".replace("  ", " ").strip()

@st.cache_data(ttl=1)
def load_data(url):
    try:
        r = requests.get(f"{url}&cb={datetime.now().timestamp()}", timeout=10)
        df = pd.read_csv(io.StringIO(r.content.decode('utf-8')))
        return df.fillna("")
    except:
        return pd.DataFrame()

# Branding
st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", use_container_width=True)
st.markdown("<div style='background:#008080; color:white; text-align:center; padding:15px; font-size:1.6rem; font-weight:800; border-bottom: 6px solid #800000; border-radius: 10px 10px 0 0;'>LMCP Digital Hub</div>", unsafe_allow_html=True)

df_raw = load_data(EVENTS_URL)

# 2. NAV PANE (Opgeknapte UI)
with st.container():
    st.markdown("<div style='background:#f9f9f9; padding:20px; border-radius:0 0 15px 15px; border:1px solid #ddd; margin-bottom:20px;'>", unsafe_allow_html=True)
    
    if not df_raw.empty:
        c1, c2 = st.columns(2)
        with c1:
            raw_acts = df_raw.iloc[:, 3].unique().tolist()
            clean_acts = sorted(list(set([a.split()[0] if "Athletics" in a else a for a in raw_acts])))
            st.multiselect("Activities", ["All"] + clean_acts, default="All", key="f_act")
        with c2:
            cats = ["All"] + sorted(df_raw.iloc[:, 2].unique().tolist())
            st.multiselect("Categories", cats, default="All", key="f_cat")
            
    st.text_input("🔍 Search Anything", key="f_search", placeholder="Type Tennis, Swem, Academics...")
    
    b1, b2 = st.columns([2,1])
    with b1:
        st.radio("View Range", ["All Upcoming", "Next 7 Days"], horizontal=True, key="f_time")
    with b2:
        if st.button("🔄 REFRESH"):
            st.cache_data.clear()
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

SA_TIME = pytz.timezone('Africa/Johannesburg')
today = datetime.now(SA_TIME).date()

if not df_raw.empty:
    df = df_raw.copy()
    # Maak seker datum is geldig voor ons dit gebruik
    df['dt_fixed'] = pd.to_datetime(df.iloc[:, 5], dayfirst=True, errors='coerce')
    df = df[df['dt_fixed'].notnull()] # Verwyder "17" of ander gemors-nommers
    df = df[df['dt_fixed'].dt.date >= today]
    
    # Filters
    if "All" not in st.session_state.f_act:
        df = df[df.iloc[:, 3].apply(lambda x: any(sel in x for sel in st.session_state.f_act))]
    if "All" not in st.session_state.f_cat:
        df = df[df.iloc[:, 2].isin(st.session_state.f_cat)]
    if st.session_state.f_time == "Next 7 Days":
        df = df[df['dt_fixed'].dt.date <= (today + pd.Timedelta(days=7))]

    search_terms = st.session_state.f_search.lower().split()

    h = """<style>
        body { background:#eef2f3; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; } 
        .card { background:white; padding:20px; border-radius:12px; border-left:8px solid #800000; margin-bottom:15px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); transition: 0.3s; }
        .card:hover { transform: translateY(-3px); box-shadow: 0 6px 20px rgba(0,0,0,0.1); }
        .card-title { color:#800000; font-size:1.3rem; font-weight:700; margin-bottom:12px; border-bottom: 1px solid #eee; padding-bottom: 5px; } 
        .info-row { font-size:1rem; color:#444; margin: 10px 0; display: flex; align-items: center; gap: 8px; }
        .teal-link { color:#008080 !important; text-decoration:none; font-weight:700; border-bottom: 2px solid #008080; }
        .btn { background:#800000 !important; color:white !important; padding:10px 16px; border-radius:6px; text-decoration:none; font-size:0.85rem; display:inline-block; margin-right:8px; margin-top:12px; font-weight:600; text-transform: uppercase; }
    </style>"""

    for _, r in df.iterrows():
        title_str = format_dle_spec(r.iloc[3], r.iloc[11], r.iloc[4])
        
        if search_terms and not any(term in title_str.lower() for term in search_terms):
            continue

        f_date = f"🗓️ {r['dt_fixed'].strftime('%d %B %Y')}"
        ven_raw = clean_val(r.iloc[6]).upper()
        ven_html = f"📍 <a class='teal-link' href='https://www.google.com/maps/search/?api=1&query={ven_raw.replace(' ', '+')}' target='_blank'>{ven_raw}</a>"
        
        btns = ""
        for i, lbl in zip([7, 8, 10], ["PROGRAMME", "TEAM LIST", "INFO"]):
            val = str(r.iloc[i]).strip()
            if "http" in val.lower():
                btns += f"<a href='{val}' target='_blank' class='btn'>{lbl}</a> "

        h += f"<div class='card'><div class='card-title'>{title_str}</div><div class='info-row'>{f_date}</div><div class='info-row'>{ven_html}</div><div>{btns}</div></div>"
    
    components.html(h, height=2500, scrolling=True)

st.markdown("<div style='background:#800000; color:white; text-align:center; padding:15px; font-size:0.9rem; font-weight:600; margin-top:20px; border-radius:0 0 10px 10px;'>Midstream College Primary · 2026 Digital Hub</div>", unsafe_allow_html=True)
