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
    """STRENG DLE: Activity + Age (met U) + Team"""
    act = clean_val(d_val)
    # Maak Athletics skoon as dit ekstra teks het
    if "athletics" in act.lower(): act = "Athletics"
    
    age_raw = clean_val(l_val)   # Kolom L
    team_raw = clean_val(e_val)  # Kolom E
    
    # Age (L) Logika: Altyd 'U' voor getalle
    if "-" in age_raw:
        age_part = re.sub(r'(\d+)', r'U\1', age_raw)
    else:
        nums = re.findall(r'\d+', age_raw)
        age_part = f"U{nums[0]}" if nums else age_raw

    # Team (E) Plak-logika: Enkel letter plak vas
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
st.markdown("<div style='background:#008080; color:white; text-align:center; padding:15px; font-size:1.4rem; font-weight:700; border-bottom: 5px solid #800000;'>Laerskool Midstream College Primary Digital Hub</div>", unsafe_allow_html=True)

df_raw = load_data(EVENTS_URL)

# 2. NAV PANE
with st.container():
    st.markdown("<div style='background:white; padding:20px; border-radius:0 0 15px 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);'>", unsafe_allow_html=True)
    
    # Filters
    if not df_raw.empty:
        c1, c2 = st.columns(2)
        with c1:
            acts = ["All"] + sorted(df_raw.iloc[:, 3].unique().tolist())
            st.multiselect("Select Activities:", acts, default="All", key="f_act")
        with c2:
            cats = ["All"] + sorted(df_raw.iloc[:, 2].unique().tolist())
            st.multiselect("Select Categories (Sport/Culture/Acad):", cats, default="All", key="f_cat")
            
    # Multi-Search: Tik bv. "Tennis Swem"
    search_q = st.text_input("🔍 Multi-Search (e.g. Tennis Swem):", key="f_search").lower().strip()
    
    b1, b2 = st.columns(2)
    with b1:
        st.radio("Timeline:", ["All Upcoming", "Next 7 Days"], horizontal=True, key="f_time")
    with b2:
        if st.button("🔄 REFRESH HUB"):
            st.cache_data.clear()
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

SA_TIME = pytz.timezone('Africa/Johannesburg')
today = datetime.now(SA_TIME).date()

if not df_raw.empty:
    df = df_raw.copy()
    df['dt_fixed'] = pd.to_datetime(df.iloc[:, 5], dayfirst=True, errors='coerce')
    df = df[df['dt_fixed'].dt.date >= today]
    
    # Filter Logika
    if "All" not in st.session_state.f_act:
        df = df[df.iloc[:, 3].isin(st.session_state.f_act)]
    if "All" not in st.session_state.f_cat:
        df = df[df.iloc[:, 2].isin(st.session_state.f_cat)]
    if st.session_state.f_time == "Next 7 Days":
        df = df[df['dt_fixed'].dt.date <= (today + pd.Timedelta(days=7))]

    h = """<style>
        body { background:#008080; font-family: sans-serif; padding:10px; } 
        .card { background:white; padding:20px; border-radius:15px; border-left:10px solid #800000; margin-bottom:15px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); } 
        .card-title { color:#800000; font-size:1.25rem; font-weight:bold; margin-bottom:10px; } 
        .info-row { font-size:0.95rem; color:#333; margin: 8px 0; font-weight: 500; }
        .teal-link { color:#008080 !important; text-decoration:underline; font-weight:800; }
        .btn { background:#800000 !important; color:white !important; padding:8px 12px; border-radius:8px; text-decoration:none; font-size:0.75rem; display:inline-block; margin-right:5px; margin-top:10px; font-weight:bold; } 
    </style>"""

    # Multi-search terme
    search_terms = search_q.split() if search_q else []

    for _, r in df.iterrows():
        title_str = format_dle_spec(r.iloc[3], r.iloc[11], r.iloc[4])
        
        # Kyk of ENIGE van die soekterme in die titel is
        if search_terms and not any(term in title_str.lower() for term in search_terms):
            continue

        f_date = f"🗓️ {r['dt_fixed'].strftime('%d %B %Y')}" if pd.notnull(r['dt_fixed']) else f"🗓️ {r.iloc[5]}"
        ven_raw = clean_val(r.iloc[6]).upper()
        ven_html = f"📍 <a class='teal-link' href='https://www.google.com/maps/search/?api=1&query={ven_raw.replace(' ', '+')}' target='_blank'>{ven_raw}</a>"
        
        btns = ""
        for i, lbl in zip([7, 8, 10], ["PROGRAMME", "TEAM LIST", "INFO"]):
            val = str(r.iloc[i]).strip()
            if "http" in val.lower():
                btns += f"<a href='{val}' target='_blank' class='btn'>{lbl}</a> "

        h += f"<div class='card'><div class='card-title'>{title_str}</div><div class='info-row'>{f_date}</div><div class='info-row'>{ven_html}</div><div>{btns}</div></div>"
    
    components.html(h, height=2500, scrolling=True)

st.markdown("<div style='background:#800000; color:white; text-align:center; padding:15px; font-size:0.8rem;'>Laerskool Midstream College Primary · Digital Hub 2026</div>", unsafe_allow_html=True)
