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
st.markdown("""
<style>
#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
.stApp{background:#008080}.block-container{padding:1rem;max-width:500px}
/* Maak die filter bars korter/smaller */
div[data-testid="stExpander"], .stSelectbox, .stMultiSelect { max-width: 100%; }
.card{background:white!important;padding:18px;border-radius:15px;border-left:12px solid #800000;margin-bottom:15px;box-shadow:0 4px 10px rgba(0,0,0,0.2)}
.t{color:#800000!important;font-weight:bold;font-size:1.2rem;margin:5px 0}
.box{background:#f8f9fa;padding:12px;border-radius:10px;margin:10px 0;border-left:5px solid #008080;color:#333;font-size:0.9rem;line-height:1.4;white-space: pre-wrap;}
.team-box{background:#fff3f3;padding:10px;border-radius:8px;margin:5px 0;border:1px dashed #800000;color:#800000;font-size:0.85rem;white-space: pre-wrap;}
.btn-row {display: flex; gap: 6px; justify-content: flex-start; margin-top: 10px; flex-wrap: wrap;}
.btn {background: #800000; color: white !important; text-align: center; text-decoration: none; font-weight: bold; font-size: 0.7rem; padding: 10px 14px; border-radius: 6px; display: inline-block; border: none; margin-bottom: 5px;}
.prog-container {margin-top: 15px; border-top: 1px solid #eee; padding-top: 10px;}
label { color:white !important; font-weight:bold; }
/* Maak die input bars smaller */
.stTextInput, .stSelectbox { width: 50% !important; }
</style>
""", unsafe_allow_html=True)

URL_DATA = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data():
    try:
        response = requests.get(f"{URL_DATA}&cb={int(time.time())}", timeout=10)
        df = pd.read_csv(io.StringIO(response.content.decode('utf-8')))
        df.columns = [str(c).strip() for c in df.columns]
        def parse_dt(x):
            s = str(x).strip()
            if not s or s.lower() == 'nan': return pd.NaT
            if '202' not in s: s = f"{s} 2026"
            return pd.to_datetime(s, dayfirst=True, errors='coerce')
        df['dt_fixed'] = df.iloc[:, 3].apply(parse_dt)
        return df
    except:
        return pd.DataFrame()

st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", use_container_width=True)
raw_df = load_data()

SA_TIME = pytz.timezone('Africa/Johannesburg')
today = datetime.now(SA_TIME).date()

# 3. FILTERS (50% wydte kolomme)
if st.button("🔄 REFRESH DATA"):
    st.cache_data.clear()
    st.rerun()

if not raw_df.empty:
    col_a, col_b = st.columns(2)
    with col_a:
        view = st.radio("View:", ["Upcoming", "Results"], horizontal=True)
    with col_b:
        cat = st.selectbox("Category:", ["All", "Sport", "Culture", "Academics"])

    # Pas filters toe
    if view == "Upcoming":
        df = raw_df[raw_df['dt_fixed'].dt.date >= today].sort_values(by='dt_fixed')
    else:
        df = raw_df[raw_df['dt_fixed'].dt.date < today].sort_values(by='dt_fixed', ascending=False)
    
    if cat != "All":
        df = df[df.iloc[:, 0].str.contains(cat, case=False, na=False)]

    search = st.text_input("🔍 Search:", placeholder="e.g. u13 hockey").lower()
    if search:
        df = df[df.apply(lambda r: search in str(r.values).lower(), axis=1)]

    # 4. Wys die kaarte
    for _, r in df.iterrows():
        # Kolomme: 1=Sport, 2=Age Group
        sport_name = str(r.iloc[1])
        age_group = str(r.iloc[2]) if str(r.iloc[2]).lower() != 'nan' else ""
        date_str = r['dt_fixed'].strftime('%d %B %Y') if pd.notnull(r['dt_fixed']) else "TBA"
        venue = str(r.iloc[4])
        
        # Inhoud versamel
        other_btns = []
        prog_link = ""
        team_content = ""
        note_content = ""
        
        # Kyk deur kolomme 5 tot 8 vir skakels of teks
        for idx, lbl in [(5, "PROGRAMME"), (6, "TEAM"), (7, "CONFIRM"), (8, "INFORMATION")]:
            val = str(r.iloc[idx]).strip()
            if val.lower() == 'nan' or not val: continue
            
            link = re.search(r'(https?://[^\s<>"]+)', val)
            if link:
                url = link.group(0)
                if lbl == "PROGRAMME":
                    prog_link = url
                else:
                    other_btns.append(f'<a href="{url}" target="_blank" class="btn">{lbl}</a>')
            else:
                # Dis teks, nie 'n skakel nie
                if lbl == "TEAM": team_content = val
                elif lbl == "INFORMATION": note_content = val

        # Bousele vir die finale Markdown om HTML-foute te vermy
        team_html = f'<div class="team-box"><b>TEAMS:</b><br>{team_content}</div>' if team_content else ""
        btns_html = f'<div class="btn-row">{" ".join(other_btns)}</div>' if other_btns else ""
        note_html = f'<div class="box"><b>Note:</b><br>{note_content}</div>' if note_content else ""
        prog_html = f'<div class="prog-container"><a href="{prog_link}" target="_blank" class="btn">PROGRAMME</a></div>' if prog_link else ""

        st.markdown(f"""
        <div class="card">
            <div style="font-size:0.85rem;color:#666">🗓️ {date_str}</div>
            <div class="t">{sport_name} {age_group}</div>
            <div style="font-size:0.85rem;color:#333">📍 {venue}</div>
            {team_html}
            {btns_html}
            {note_html}
            {prog_html}
        </div>
        """, unsafe_allow_html=True)
else:
    st.error("No data found.")
