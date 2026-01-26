import streamlit as st
import pandas as pd
import re
from datetime import datetime
import pytz
import requests
import io
import time
import html
from streamlit_autorefresh import st_autorefresh

# 1. Page Configuration
st.set_page_config(page_title="LMCP Live Fixtures", layout="centered")
st_autorefresh(interval=120000, key="datarefresh")

# 2. Styling (Maroon & Teal Contrast)
st.markdown("""
<style>
#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
.stApp{background:#008080}.block-container{padding:1rem;max-width:500px}
.card{background:white!important;padding:18px;border-radius:15px;border-left:12px solid #800000;margin-bottom:15px;box-shadow:0 4px 10px rgba(0,0,0,0.2)}
.t{color:#800000!important;font-weight:bold;font-size:1.2rem;margin:5px 0}
/* Teal Note Box */
.box{background:#f8f9fa;padding:12px;border-radius:10px;margin:10px 0;border-left:5px solid #008080;color:#333;font-size:0.9rem;line-height:1.4;white-space: pre-wrap;}
.team-box{background:#fff3f3;padding:10px;border-radius:8px;margin:5px 0;border:1px dashed #800000;color:#800000;font-size:0.85rem;white-space: pre-wrap;}
.btn-row {display: flex; gap: 6px; justify-content: flex-start; margin-top: 10px; flex-wrap: wrap;}
.btn {background: #800000; color: white !important; text-align: center; text-decoration: none; font-weight: bold; font-size: 0.7rem; padding: 10px 14px; border-radius: 6px; display: inline-block; border: none; margin-bottom: 5px;}
.prog-container {margin-top: 15px; border-top: 1px solid #eee; padding-top: 10px;}
label { color:white !important; font-weight:bold; }
/* Narrower Filter Bars */
.stTextInput, .stSelectbox { width: 50% !important; }
</style>
""", unsafe_allow_html=True)

# 3. Data Loading
URL_DATA = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-"
    "YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub"
    "?gid=0&single=true&output=csv"
)

def load_data():
    try:
        response = requests.get(f"{URL_DATA}&cb={int(time.time())}", timeout=10)
        df = pd.read_csv(io.StringIO(response.content.decode('utf-8')))
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

# 4. Search and Refresh
if st.button("🔄 REFRESH DATA"):
    st.cache_data.clear()
    st.rerun()

search_q = st.text_input("🔍 Search Activity or Age:", placeholder="e.g. u13 hockey").lower()

if not raw_df.empty:
    col1, col2 = st.columns(2)
    with col1:
        view = st.radio("View:", ["Upcoming", "Results"], horizontal=True)
    with col2:
        cat = st.selectbox("Category:", ["All", "Sport", "Culture", "Academics"])

    # Filtering Logic
    if view == "Upcoming":
        df = raw_df[raw_df['dt_fixed'].dt.date >= today].sort_values(by='dt_fixed')
    else:
        df = raw_df[raw_df['dt_fixed'].dt.date < today].sort_values(by='dt_fixed', ascending=False)
    
    if cat != "All":
        df = df[df.iloc[:, 0].str.contains(cat, case=False, na=False)]
    
    if search_q:
        df = df[df.apply(lambda r: search_q in str(r.values).lower(), axis=1)]

    # 5. Display Cards
    for _, r in df.iterrows():
        # Force Age Group back next to Sport
        sport = str(r.iloc[1])
        age_raw = str(r.iloc[2]).strip()
        age = age_raw if (age_raw.lower() != 'nan' and age_raw != "") else ""
        
        date_str = r['dt_fixed'].strftime('%d %B %Y') if pd.notnull(r['dt_fixed']) else "TBA"
        venue = str(r.iloc[4])
        
        prog_html = ""
        other_btns = ""
        team_html = ""
        note_html = ""

        # Process columns 5 to 8
        for idx, lbl in [(5, "PROGRAMME"), (6, "TEAM"), (7, "CONFIRM"), (8, "INFORMATION")]:
            val = str(r.iloc[idx]).strip()
            if val.lower() == 'nan' or not val: continue
            
            link = re.search(r'(https?://[^\s<>"]+)', val)
            if link:
                url = link.group(0)
                btn_tag = f'<a href="{url}" target="_blank" class="btn">{lbl}</a>'
                if lbl == "PROGRAMME": prog_html = f'<div class="prog-container">{btn_tag}</div>'
                else: other_btns += btn_tag
            else:
                if lbl == "TEAM":
                    team_html = f'<div class="team-box"><b>TEAMS:</b><br>{val}</div>'
                elif lbl == "INFORMATION":
                    note_html = f'<div class="box"><b>Note:</b><br>{val}</div>'

        st.markdown(f"""
        <div class="card">
            <div style="font-size:0.85rem;color:#666">🗓️ {date_str}</div>
            <div class="t">{sport} {age}</div>
            <div style="font-size:0.85rem;color:#333">📍 {venue}</div>
            {team_html}
            <div class="btn-row">{other_btns}</div>
            {note_html}
            {prog_html}
        </div>
        """, unsafe_allow_html=True)
else:
    st.error("No data found. Please check your connection.")
