import streamlit as st
import pandas as pd
import re
from datetime import datetime
import pytz
import requests
import io
import urllib.parse
from streamlit_autorefresh import st_autorefresh

# 1. Page Config
st.set_page_config(page_title="LMCP Event Hub", layout="centered")
st_autorefresh(interval=120000, key="datarefresh")

# 2. CSS Styling (Stywer margins & Card Fix)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700&display=swap');
html, body, .stApp { background:#008080; font-family:'Source Sans 3', sans-serif; }
#MainMenu, footer, header {visibility:hidden;}

/* Verwyder wit spasie bo-aan die bladsy */
.block-container { max-width:800px; padding-top: 0rem !important; margin-top: -2rem !important; }

/* Sticky Header & Navbar */
.navbar { background:white; border-bottom:5px solid #800000; text-align:center; line-height: 0; }
.navbar img { width:100%; max-height:140px; object-fit:contain; margin:0; }
.header-title { background:#008080; color:white; text-align:center; padding:15px; font-size:1.4rem; font-weight:700; margin-top: -1px; }

/* Filter Box */
.filter-box { background:white; padding:20px; border-radius:0 0 20px 20px; margin-bottom:20px; box-shadow:0 4px 10px rgba(0,0,0,0.1); }

/* Die Kaartjie-raam Fix */
div[data-testid="stVerticalBlock"] > div:has(div.card-frame) {
    background: white !important;
    padding: 25px !important;
    border-radius: 20px !important;
    border-left: 12px solid #800000 !important;
    margin-bottom: 25px !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
}
.card-frame { display: none; }

/* Teks Kleure */
h3 { color: #800000 !important; margin-top: 5px !important; }
.date-label { color: #666; font-size: 0.85rem; font-weight: 600; }
.venue-link { color: #008080; font-weight: 700; text-decoration: none; }
</style>
<div class="navbar"><img src="https://midstream-primary.co.za/wp-content/uploads/2021/09/MCP-1.png"></div>
<div class="header-title">Laerskool Midstream College Primary Event Hub</div>
""", unsafe_allow_html=True)

# 3. Data Loading
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=60)
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

# 4. Filter Section
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

# 5. Display Cards
if not df_raw.empty:
    if view == "Upcoming":
        df = df_raw[df_raw['dt_fixed'].dt.date >= today].sort_values(by='dt_fixed')
    else:
        df = df_raw[df_raw['dt_fixed'].dt.date < today].sort_values(by='dt_fixed', ascending=False)
    
    if cat_filter != "All":
        df = df[df.iloc[:, 0].str.contains(cat_filter, case=False, na=False)]
    if search_q:
        df = df[df.apply(lambda r: search_q in str(r.values).lower(), axis=1)]

    for _, r in df.iterrows():
        with st.container():
            # Hierdie "marker" dwing die CSS om net hierdie boksie wit te maak
            st.markdown('<div class="card-frame"></div>', unsafe_allow_html=True)
            
            # Datum
            date_s = r['dt_fixed'].strftime('%d %B %Y') if pd.notnull(r['dt_fixed']) else "TBA"
            st.markdown(f"<div class='date-label'>🗓️ {date_s}</div>", unsafe_allow_html=True)
            
            # Titel (Sport + Age)
            sport = str(r.iloc[1])
            age = str(r.iloc[2]) if str(r.iloc[2]).lower() != 'nan' else ""
            st.subheader(f"{sport} {age}")
            
            # Venue
            venue = str(r.iloc[4])
            maps_url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(venue + ' Midstream')}"
            st.markdown(f"📍 **[{venue}]({maps_url})**")
            
            # Teams (Grys/Pienk boksie slegs as daar teks is)
            team_val = str(r.iloc[6]).strip()
            if team_val and team_val.lower() != 'nan' and not re.search(r'https?://', team_val):
                st.info(f"**TEAMS:**\n\n{team_val}")
            
            # Knoppies
            cols = st.columns(2) # Gebruik 2 kolomme vir groter knoppies op foon
            btn_count = 0
            for idx, lbl in [(6, "TEAM"), (7, "CONFIRM"), (8, "INFORMATION"), (5, "PROGRAMME")]:
                val = str(r.iloc[idx]).strip()
                link = re.search(r'(https?://[^\s<>"]+)', val)
                if link:
                    with cols[btn_count % 2]:
                        st.link_button(lbl, link.group(0), use_container_width=True)
                    btn_count += 1
            
            # Swem Notas / Inligting
            info_val = str(r.iloc[8]).strip()
            if info_val and info_val.lower() != 'nan' and not re.search(r'https?://', info_val):
                st.warning(f"**Note:**\n\n{info_val}")

st.markdown("""<div style='background:#800000; color:white; text-align:center; padding:20px; font-size:0.85rem; margin-top:50px;'>Midstream College Primary · 012 940 2222</div>""", unsafe_allow_html=True)
