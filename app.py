import streamlit as st
import pandas as pd
import requests
import io
import re
from datetime import datetime
import pytz
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

# 1. Configuration
st.set_page_config(page_title="LMCP Digital Hub", layout="centered")
st_autorefresh(interval=120000, key="datarefresh")

EVENTS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

def clean_val(val):
    v = str(val).replace(".0", "").replace("nan", "").replace("NAN", "").strip()
    return "" if v.lower() in ["n/a", "none", ""] else v

def format_dle_spec(d_val, l_val, e_val):
    """ D=Activity, L=Age (U), E=Team (Attached) """
    act = clean_val(d_val)
    age_raw = clean_val(l_val)   # Column L (Index 11)
    team_raw = clean_val(e_val)  # Column E (Index 4)
    
    # U-prefix logic for numbers and ranges
    age_part = re.sub(r'(\d+)', r'U\1', age_raw) if age_raw else ""

    # Team attachment logic (e.g., U13A)
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

# Header
st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", use_container_width=True)
st.markdown("<div style='background: linear-gradient(90deg, #008080, #006666); color:white; text-align:center; padding:15px; font-size:1.5rem; font-weight:800; border-radius:12px;'>LMCP Digital Hub</div>", unsafe_allow_html=True)

df_raw = load_data(EVENTS_URL)

# 2. Navigation Pane
with st.container():
    st.markdown("<div style='background:white; padding:20px; border-radius:12px; border:1px solid #eee; box-shadow:0 4px 12px rgba(0,0,0,0.05); margin: 15px 0;'>", unsafe_allow_html=True)
    if not df_raw.empty:
        c1, c2 = st.columns(2)
        with c1:
            raw_acts = df_raw.iloc[:, 3].unique().tolist()
            clean_acts = sorted(list(set([str(a).split()[0] if "Athletics" in str(a) else str(a) for a in raw_acts])))
            st.multiselect("Activities", ["All"] + clean_acts, default="All", key="f_act")
        with c2:
            cats = ["All"] + sorted(df_raw.iloc[:, 2].unique().tolist())
            st.multiselect("Category", cats, default="All", key="f_cat")
            
    st.markdown("---")
    search_q = st.text_input("Search", key="f_search", placeholder="Search Activity or Age Group...")
    
    b1, b2 = st.columns([2,1])
    with b1:
        st.radio("View", ["All Upcoming", "Next 7 Days"], horizontal=True, key="f_time")
    with b2:
        if st.button("REFRESH HUB", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

SA_TIME = pytz.timezone('Africa/Johannesburg')
today = datetime.now(SA_TIME).date()

if not df_raw.empty:
    df = df_raw.copy()
    df['dt_fixed'] = pd.to_datetime(df.iloc[:, 5], dayfirst=True, errors='coerce')
    df = df[(df['dt_fixed'].dt.date >= today) | (df['dt_fixed'].isnull())]
    
    if "All" not in st.session_state.f_act:
        df = df[df.iloc[:, 3].apply(lambda x: any(sel in str(x) for sel in st.session_state.f_act))]
    if "All" not in st.session_state.f_cat:
        df = df[df.iloc[:, 2].isin(st.session_state.f_cat)]
    
    search_terms = search_q.lower().split()

    h = """<style>
        body { background:#f8f9fa; font-family: 'Helvetica', sans-serif; }
        .card { background:white; padding:20px; border-radius:15px; border-left:10px solid #800000; margin-bottom:18px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
        .card-title { color:#800000; font-size:1.3rem; font-weight:800; margin-bottom:10px; }
        .info-row { font-size:1rem; color:#444; margin: 8px 0; }
        .teal-link { color:#008080 !important; font-weight:700; text-decoration:underline; }
        .btn-box { display:flex; flex-wrap:wrap; gap:8px; margin-top:15px; }
        .btn { background:#800000 !important; color:white !important; padding:10px 15px; border-radius:8px; text-decoration:none; font-size:0.8rem; font-weight:700; text-transform:uppercase; display:inline-block; border:none; cursor:pointer; }
    </style>"""

    for _, r in df.iterrows():
        title_str = format_dle_spec(r.iloc[3], r.iloc[11], r.iloc[4])
        if search_terms and not any(term in title_str.lower() for term in search_terms):
            continue

        d_str = r['dt_fixed'].strftime('%d %B %Y') if pd.notnull(r['dt_fixed']) else str(r.iloc[5])
        ven_raw = clean_val(r.iloc[6]).upper()
        ven_html = f"<a class='teal-link' href='http://google.com/maps?q={ven_raw.replace(' ', '+')}' target='_blank'>{ven_raw}</a>"
        
        # LINK LOGIC: Program (H/7), Teams (I/8), Info (K/10)
        btns = ""
        link_map = {"PROGRAMME": r.iloc[7], "TEAMS": r.iloc[8], "INFORMATION": r.iloc[10]}
        
        for lbl, val in link_map.items():
            content = str(val).strip()
            if content and content.lower() not in ["nan", "n/a", ""]:
                # As dit 'n skakel is, maak oop. As dit net teks is, wys as knoppie (of jy kan dit as popup hanteer)
                link_url = content if "http" in content.lower() else "#"
                btns += f"<a href='{link_url}' target='_blank' class='btn'>{lbl}</a>"

        h += f"""<div class='card'>
                    <div class='card-title'>{title_str}</div>
                    <div class='info-row'>📅 {d_str}</div>
                    <div class='info-row'>📍 {ven_html}</div>
                    <div class='btn-box'>{btns}</div>
                 </div>"""
    
    components.html(h, height=2500, scrolling=True)

st.markdown("<div style='text-align:center; padding:20px; color:#999; font-size:0.8rem;'>Midstream College Primary · Digital Hub 2026</div>", unsafe_allow_html=True)
