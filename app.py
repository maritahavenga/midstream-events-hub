import streamlit as st
import pandas as pd
import re
from datetime import datetime, timedelta
import pytz
import requests
import io
import urllib.parse
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

# 1. Config & Data
st.set_page_config(page_title="LMCP Event Hub", layout="centered")
st_autorefresh(interval=120000, key="datarefresh")

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=30)
def load_data():
    try:
        r = requests.get(f"{URL}&cb={datetime.now().timestamp()}", timeout=10)
        df = pd.read_csv(io.StringIO(r.content.decode('utf-8')))
        def parse_dt(x):
            s = str(x).strip()
            if not s or s.lower() == 'nan': return pd.NaT
            if '202' not in s: s = f"{s} {datetime.now().year}"
            return pd.to_datetime(s, dayfirst=True, errors='coerce')
        df['dt_fixed'] = df.iloc[:, 3].apply(parse_dt)
        return df
    except: return pd.DataFrame()

df_raw = load_data()
SA_TIME = pytz.timezone('Africa/Johannesburg')
today = datetime.now(SA_TIME).date()

# 2. UI Header
st.markdown("<style>[data-testid='stHeader'] {display: none;} .block-container {padding:0 !important;}</style>", unsafe_allow_html=True)
st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", use_container_width=True)
st.markdown("<div style='background:#008080; color:white; text-align:center; padding:15px; font-size:1.4rem; font-weight:700; border-bottom: 5px solid #800000;'>Laerskool Midstream College Primary Event Hub</div>", unsafe_allow_html=True)

with st.container():
    st.markdown("<div style='background:white; padding:20px; border-radius:0 0 20px 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);'>", unsafe_allow_html=True)
    search_q = st.text_input("🔍 Search (e.g. u7 or Athletics):", placeholder="Type here...").lower().strip()
    
    col1, col2 = st.columns(2)
    with col1:
        cat_f = st.selectbox("Select Category:", ["All", "Sport", "Culture", "Academics"])
    with col2:
        if cat_f != "All" and not df_raw.empty:
            filtered_list = df_raw[df_raw.iloc[:, 0].str.contains(cat_f, case=False, na=False)]
            act_opts = sorted(filtered_list.iloc[:, 1].dropna().unique().tolist())
        else:
            act_opts = sorted(df_raw.iloc[:, 1].dropna().unique().tolist()) if not df_raw.empty else []
        act_f = st.multiselect("Select Activities:", act_opts)
    
    c3, c4 = st.columns([2, 1])
    with c3:
        # "Upcoming" is nou weer die standaard (default)
        view = st.radio("Date Range:", ["Upcoming", "Next 7 Days"], horizontal=True)
    with c4:
        if st.button("🔄 REFRESH DATA"):
            st.cache_data.clear()
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# 3. Logic & Rendering
if not df_raw.empty:
    df = df_raw[df_raw['dt_fixed'].dt.date >= today]
    if view == "Next 7 Days":
        df = df[df['dt_fixed'].dt.date <= today + timedelta(days=7)]
    if cat_f != "All": 
        df = df[df.iloc[:, 0].str.contains(cat_f, case=False, na=False)]
    if act_f: 
        df = df[df.iloc[:, 1].isin(act_f)]
        
    if search_q:
        def match(r):
            pool = str(r.values).lower()
            is_age = re.search(r'u\s?\d+', search_q)
            is_mass = any(x in str(r.iloc[1]).lower() for x in ['athletics', 'swimming', 'atletiek', 'swem', 'gala'])
            return (search_q in pool) or (is_age and is_mass)
        df = df[df.apply(match, axis=1)]

    h = """<style>
    @import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700&display=swap');
    body { background:#008080; font-family:'Source Sans 3', sans-serif; margin:0; padding:15px; }
    .card { background:white; padding:25px; border-radius:22px; border-left:12px solid #800000; margin-bottom:20px; box-shadow:0 6px 15px rgba(0,0,0,0.15); position: relative; }
    .new-badge { position: absolute; top: 15px; right: 15px; background: #ffcc00; color: #800000; padding: 4px 10px; border-radius: 8px; font-weight: bold; font-size: 0.7rem; text-transform: uppercase; animation: flash 1.5s infinite; border: 1px solid #800000; }
    @keyframes flash { 0% { opacity: 1; } 50% { opacity: 0.4; } 100% { opacity: 1; } }
    .card-title { color:#800000; font-size:1.4rem; font-weight:700; margin: 5px 0; }
    .venue { color:#008080; font-weight:600; text-decoration:none; font-size: 0.9rem; }
    .team-box { background:#fff3f3; padding:12px; border-radius:10px; margin:10px 0; border:1px dashed #800000; color:#800000; font-size:0.85rem; }
    .note-box { background:#f8f9fa; padding:12px; border-radius:10px; margin:10px 0; border-left:5px solid #008080; color:#333; font-size:0.85rem; }
    .btn-row { display:flex; flex-wrap:wrap; gap:8px; margin-top:12px; }
    .btn { background:#800000; color:white !important; padding:8px 16px; border-radius:10px; font-weight:600; text-decoration:none; font-size:0.75rem; display:inline-block; }
    </style>"""

    for _, r in df.sort_values('dt_fixed').iterrows():
        sport, age = str(r.iloc[1]), (str(r.iloc[2]) if str(r.iloc[2]).lower() != 'nan' else "")
        dt_fixed = r['dt_fixed']
        dt_s = dt_fixed.strftime('%d %B %Y') if pd.notnull(dt_fixed) else "TBA"
        ven = str(r.iloc[4])
        t_b, b_r, n_b, badge = "", "", "", ""
        
        # --- DOLLAR TRIGGER ONLY ---
        check_text = (str(r.iloc[6]) + " " + str(r.iloc[8])).upper()
        if "$" in check_text or "NEW" in check_text or "NUUT" in check_text:
            badge = "<div class='new-badge'>Recent Update</div>"

        for idx, lbl in [(5, "PROGRAMME"), (6, "TEAM"), (7, "CONFIRM"), (8, "INFORMATION")]:
            val = str(r.iloc[idx]).strip()
            if not val or val.lower() == 'nan': continue
            link_m = re.search(r'(https?://[^\s<>"]+)', val)
            if link_m:
                b_r += f"<a href='{link_m.group(0)}' target='_blank' class='btn'>{lbl}</a> "
            else:
                if lbl == "TEAM": t_b = f"<div class='team-box'><b>TEAMS:</b><br>{val}</div>"
                elif lbl == "INFORMATION":
                    # Verwyder $ uit die vertoon
                    clean = re.sub(r'(?i)new|nuut|\$', '', val).strip()
                    n_b = f"<div class='note-box'><b>Note:</b><br>{clean}</div>"

        m_url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(ven + ' Midstream')}"
        h += f"""<div class="card">
            {badge}
            <div style="color:#666;font-size:0.85rem">🗓️ {dt_s}</div>
            <div class="card-title">{sport} {age}</div>
            <div class="venue"><a href="{m_url}" target="_blank" style="color:#008080;text-decoration:none">📍 {ven}</a></div>
            {t_b}<div class="btn-row">{b_r}</div>{n_b}
        </div>"""
    
    components.html(h + "</div>", height=2000, scrolling=True)

st.markdown("<div style='background:#800000; color:white; text-align:center; padding:15px; font-size:0.8rem;'>Midstream College Primary · info@midstreamprimary.co.za</div>", unsafe_allow_html=True)
