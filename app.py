import streamlit as st
import pandas as pd
import re
from datetime import datetime
import pytz
import requests
import io
import urllib.parse
import streamlit.components.v1 as components # Korrekte manier om dit in te laai
from streamlit_autorefresh import st_autorefresh

# 1. Page Configuration
st.set_page_config(page_title="LMCP Event Hub", layout="centered")
st_autorefresh(interval=120000, key="datarefresh")

# 2. Styling (CSS)
STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700&display=swap');
body { background:#008080; font-family:'Source Sans 3', sans-serif; margin:0; padding:0; }
.navbar { background:white; border-bottom:5px solid #800000; text-align:center; padding:10px 0; }
.navbar img { max-width:100%; max-height:120px; object-fit:contain; }
.header-title { background:#008080; color:white; text-align:center; padding:15px; font-size:1.4rem; font-weight:700; }
.card { background:white; padding:25px; border-radius:22px; border-left:12px solid #800000; margin-bottom:25px; box-shadow:0 6px 18px rgba(0,0,0,0.18); font-family:'Source Sans 3', sans-serif; }
.card-date { color:#666; font-size:0.9rem; margin-bottom: 5px; }
.card-title { color:#800000; font-size:1.5rem; font-weight:700; margin: 5px 0; }
.venue-link { color:#008080; font-weight:600; text-decoration:none; font-size: 0.95rem; }
.team-box { background:#fff3f3; padding:15px; border-radius:12px; margin:15px 0; border:1px dashed #800000; color:#800000; font-size:0.9rem; white-space: pre-wrap; }
.note-box { background:#f8f9fa; padding:15px; border-radius:12px; margin:15px 0; border-left:5px solid #008080; color:#333; font-size:0.9rem; white-space: pre-wrap; }
.btn-row { display:flex; flex-wrap:wrap; gap:10px; margin-top:15px; }
.btn { background:#800000; color:white !important; padding:10px 20px; border-radius:12px; font-weight:600; text-decoration:none; font-size:0.8rem; display:inline-block; }
.prog-container { margin-top:15px; border-top: 1px solid #eee; padding-top:10px; }
.footer { background:#800000; color:white; text-align:center; padding:18px; font-size:0.85rem; margin-top:30px; }
</style>
"""

# 3. Data Logic
URL_DATA = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data():
    try:
        r = requests.get(f"{URL_DATA}&cb={datetime.now().timestamp()}", timeout=10)
        df = pd.read_csv(io.StringIO(r.content.decode('utf-8')))
        def parse_dt(x):
            s = str(x).strip()
            if not s or s.lower() == 'nan': return pd.NaT
            if '202' not in s: s = f"{s} {datetime.now().year}"
            return pd.to_datetime(s, dayfirst=True, errors='coerce')
        df['dt_fixed'] = df.iloc[:, 3].apply(parse_dt)
        return df
    except:
        return pd.DataFrame()

# 4. App UI
st.markdown("<style>[data-testid='stHeader'] {display: none;} .block-container {padding:0 !important;}</style>", unsafe_allow_html=True)

df_raw = load_data()
SA_TIME = pytz.timezone('Africa/Johannesburg')
today = datetime.now(SA_TIME).date()

with st.container():
    st.markdown("<div style='background:white; padding:20px; border-radius:0 0 20px 20px; margin-bottom:10px;'>", unsafe_allow_html=True)
    search_q = st.text_input("🔍 Search Activity or Age Group:", placeholder="e.g. u13 hockey").lower()
    c1, c2 = st.columns(2)
    with c1: view = st.radio("View:", ["Upcoming", "Results"], horizontal=True)
    with c2: 
        cat_options = ["All", "Sport", "Culture", "Academics"]
        cat_filter = st.selectbox("Category:", cat_options)
    
    if st.button("🔄 REFRESH DATA"):
        st.cache_data.clear()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

if not df_raw.empty:
    if view == "Upcoming":
        df = df_raw[df_raw['dt_fixed'].dt.date >= today].sort_values(by='dt_fixed')
    else:
        df = df_raw[df_raw['dt_fixed'].dt.date < today].sort_values(by='dt_fixed', ascending=False)
    
    if cat_filter != "All":
        df = df[df.iloc[:, 0].str.contains(cat_filter, case=False, na=False)]
    if search_q:
        df = df[df.apply(lambda r: search_q in str(r.values).lower(), axis=1)]

    # Bou die finale HTML
    cards_html = f"{STYLE}<div class='navbar'><img src='https://midstream-primary.co.za/wp-content/uploads/2021/09/MCP-1.png'></div><div class='header-title'>Laerskool Midstream College Primary Event Hub</div><div style='padding:15px;'>"
    
    for _, r in df.iterrows():
        sport = str(r.iloc[1])
        age = str(r.iloc[2]) if str(r.iloc[2]).lower() != 'nan' else ""
        date_s = r['dt_fixed'].strftime('%d %B %Y') if pd.notnull(r['dt_fixed']) else "TBA"
        venue = str(r.iloc[4])
        t_box, b_row, n_box, p_row = "", "", "", ""
        
        for idx, lbl in [(5, "PROGRAMME"), (6, "TEAM"), (7, "CONFIRM"), (8, "INFORMATION")]:
            val = str(r.iloc[idx]).strip()
            if val.lower() == 'nan' or not val: continue
            link = re.search(r'(https?://[^\s<>"]+)', val)
            if link:
                url = link.group(0)
                btn = f"<a href='{url}' target='_blank' class='btn'>{lbl}</a>"
                if lbl == "PROGRAMME": p_row = f"<div class='prog-container'><div class='btn-row'>{btn}</div></div>"
                else: b_row += btn + " "
            else:
                if lbl == "TEAM": t_box = f"<div class='team-box'><b>TEAMS:</b><br>{val}</div>"
                elif lbl == "INFORMATION": n_box = f"<div class='note-box'><b>Note:</b><br>{val}</div>"

        maps_url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(venue + ' Midstream')}"
        cards_html += f"""
        <div class="card">
            <div class="card-date">🗓️ {date_s}</div>
            <div class="card-title">{sport} {age}</div>
            <div class="venue-link"><a href="{maps_url}" target="_blank" style="color:#008080; text-decoration:none;">📍 {venue}</a></div>
            {t_box}<div class="btn-row">{b_row}</div>{n_box}{p_row}
        </div>"""
    
    cards_html += "</div><div class='footer'>Midstream College Primary · info@midstreamprimary.co.za</div>"
    
    # Gebruik nou die korrekte inlaai-metode
    components.html(cards_html, height=2500, scrolling=True)
else:
    st.info("No data available.")
