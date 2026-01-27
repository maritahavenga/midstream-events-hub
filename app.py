import streamlit as st
import pandas as pd
import re
from datetime import datetime
import pytz
import requests
import io
import urllib.parse
from streamlit_autorefresh import st_autorefresh

# 1. Page Configuration
st.set_page_config(page_title="LMCP Event Hub", layout="centered")
st_autorefresh(interval=120000, key="datarefresh")

# 2. Styling (The Look You Love)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700&display=swap');
html, body, .stApp { background:#008080; font-family:'Source Sans 3', sans-serif; }
#MainMenu, footer, header {visibility:hidden;}

/* Fix the Top Banner/Logo Spacing */
.block-container { max-width:820px; padding: 0 !important; margin: 0 auto; }
[data-testid="stHeader"] {display: none;}

.navbar { background:white; border-bottom:5px solid #800000; text-align:center; line-height: 0; }
.navbar img { width:100%; max-height:140px; object-fit:contain; }
.header-title { background:#008080; color:white; text-align:center; padding:15px; font-size:1.4rem; font-weight:700; margin-top:-2px; }

/* Filter Box */
.filter-box { background:white; padding:20px; border-radius:0 0 20px 20px; margin-bottom:20px; box-shadow:0 6px 18px rgba(0,0,0,0.18); }

/* Card Styling */
.card { background:white; padding:25px; border-radius:22px; border-left:12px solid #800000; margin-bottom:25px; box-shadow:0 6px 18px rgba(0,0,0,0.18); text-align: left; }
.card-date { color:#666; font-size:0.9rem; margin-bottom: 5px; }
.card-title { color:#800000; font-size:1.5rem; font-weight:700; margin: 5px 0; line-height: 1.2; }
.venue-link { color:#008080; font-weight:600; text-decoration:none; font-size: 0.95rem; }

/* Team & Note Boxes */
.team-box { background:#fff3f3; padding:15px; border-radius:12px; margin:15px 0; border:1px dashed #800000; color:#800000; font-size:0.9rem; white-space: pre-wrap; }
.note-box { background:#f8f9fa; padding:15px; border-radius:12px; margin:15px 0; border-left:5px solid #008080; color:#333; font-size:0.9rem; white-space: pre-wrap; }

/* Buttons */
.btn-row { display:flex; flex-wrap:wrap; gap:10px; margin-top:15px; }
.btn { background:#800000; color:white !important; padding:10px 20px; border-radius:12px; font-weight:600; text-decoration:none; font-size:0.8rem; display:inline-block; border: none; }
.prog-container { margin-top:15px; border-top: 1px solid #eee; padding-top:10px; }

label { color: #333 !important; font-weight: bold; }
</style>
<div class="navbar"><img src="https://midstream-primary.co.za/wp-content/uploads/2021/09/MCP-1.png"></div>
<div class="header-title">Laerskool Midstream College Primary Event Hub</div>
""", unsafe_allow_html=True)

# 3. Data Loading
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?gid=0&single=true&output=csv"

def load_data():
    try:
        r = requests.get(f"{DATA_URL}&cb={datetime.now().timestamp()}", timeout=10)
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

df_raw = load_data()
SA_TIME = pytz.timezone('Africa/Johannesburg')
today = datetime.now(SA_TIME).date()

# 4. Filters
with st.container():
    st.markdown('<div class="filter-box">', unsafe_allow_html=True)
    search_q = st.text_input("🔍 Search Activity or Age Group:", placeholder="e.g. u13 hockey").lower()
    
    col1, col2 = st.columns(2)
    with col1:
        view = st.radio("View:", ["Upcoming", "Results"], horizontal=True)
    with col2:
        cat_options = ["All", "Sport", "Culture", "Academics"]
        cat_filter = st.selectbox("Category:", cat_options)
    
    if st.button("🔄 REFRESH DATA"):
        st.cache_data.clear()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# 5. Build and Inject Final HTML
if not df_raw.empty:
    if view == "Upcoming":
        df = df_raw[df_raw['dt_fixed'].dt.date >= today].sort_values(by='dt_fixed')
    else:
        df = df_raw[df_raw['dt_fixed'].dt.date < today].sort_values(by='dt_fixed', ascending=False)
    
    if cat_filter != "All":
        df = df[df.iloc[:, 0].str.contains(cat_filter, case=False, na=False)]
    if search_q:
        df = df[df.apply(lambda r: search_q in str(r.values).lower(), axis=1)]

    # We build ONE long HTML string to prevent Streamlit from "escaping" parts of it
    all_cards_html = ""
    for _, r in df.iterrows():
        sport = str(r.iloc[1])
        age = str(r.iloc[2]) if str(r.iloc[2]).lower() != 'nan' else ""
        date_str = r['dt_fixed'].strftime('%d %B %Y') if pd.notnull(r['dt_fixed']) else "TBA"
        venue = str(r.iloc[4])
        
        t_box = ""
        b_row = ""
        n_box = ""
        p_row = ""
        
        # Mapping: 5=Prog, 6=Team, 7=Confirm, 8=Info
        for idx, lbl in [(5, "PROGRAMME"), (6, "TEAM"), (7, "CONFIRM"), (8, "INFORMATION")]:
            val = str(r.iloc[idx]).strip()
            if val.lower() == 'nan' or not val: continue
            
            link = re.search(r'(https?://[^\s<>"]+)', val)
            if link:
                url = link.group(0)
                btn = f'<a href="{url}" target="_blank" class="btn">{lbl}</a>'
                if lbl == "PROGRAMME": p_row = f'<div class="prog-container"><div class="btn-row">{btn}</div></div>'
                else: b_row += btn + " "
            else:
                if lbl == "TEAM": t_box = f'<div class="team-box"><b>TEAMS:</b><br>{val}</div>'
                elif lbl == "INFORMATION": n_box = f'<div class="note-box"><b>Note:</b><br>{val}</div>'

        maps_url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(venue + ' Midstream')}"

        all_cards_html += f"""
        <div class="card">
            <div class="card-date">🗓️ {date_str}</div>
            <div class="card-title">{sport} {age}</div>
            <div class="venue-link"><a href="{maps_url}" target="_blank" style="color:#008080; text-decoration:none;">📍 {venue}</a></div>
            {t_box}
            <div class="btn-row">{b_row}</div>
            {n_box}
            {p_row}
        </div>
        """
    
    st.markdown(all_cards_html, unsafe_allow_html=True)

st.markdown("""<div style='background:#800000; color:white; text-align:center; padding:18px; font-size:0.85rem; margin-top:50px;'>Midstream College Primary · info@midstreamprimary.co.za · 012 940 2222</div>""", unsafe_allow_html=True)
