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

# 2. Styling (Suiwer Midstream Maroen)
st.markdown("""
<style>
#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
.stApp{background:#008080}.block-container{padding:1rem;max-width:500px}
.card{background:white;padding:18px;border-radius:15px;border-left:12px solid #800000;margin-bottom:15px;box-shadow:0 4px 10px rgba(0,0,0,0.2)}
.t{color:#800000;font-weight:bold;font-size:1.2rem;margin:5px 0}
.box{background:#f8f9fa;padding:12px;border-radius:8px;margin:10px 0;border-left:5px solid #800000;color:#333;font-size:0.85rem;}
.team-box{border:2px dashed #800000; padding:10px; border-radius:8px; margin:10px 0; background:#fff9f9; color:#800000; font-weight:bold; font-size:0.85rem;}
.btn-row {display:flex; gap:6px; justify-content:flex-start; margin-top:10px; flex-wrap: wrap;}
.btn {background:#800000; color:white!important; text-align:center; text-decoration:none; font-weight:bold; font-size:0.75rem; padding:8px 12px; border-radius:6px; display:inline-block; border:none;}
label { color:white !important; font-weight:bold; }
h2 { color: white !important; text-align: center; text-transform: uppercase;}
.stButton>button { width:100%; background-color:#800000; color:white; border:none; border-radius:10px; font-weight:bold;}
</style>
""", unsafe_allow_html=True)

URL_DATA = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?gid=0&single=true&output=csv"

def load_live_data():
    try:
        SA_TIME = pytz.timezone('Africa/Johannesburg')
        now = datetime.now(SA_TIME).date()
        # Dwing vars data met 'n unieke tyd-stempel
        response = requests.get(f"{URL_DATA}&nocache={time.time()}", timeout=10)
        df = pd.read_csv(io.StringIO(response.content.decode('utf-8')))
        def parse_dt(x):
            s = str(x).strip()
            if not s or s.lower() == 'nan': return pd.NaT
            if '202' not in s: s = f"{s} 2026"
            return pd.to_datetime(s, dayfirst=True, errors='coerce')
        # Kolom 3 = Date
        df['dt_fixed'] = df.iloc[:, 3].apply(parse_dt)
        return df[df['dt_fixed'].dt.date >= now].sort_values(by='dt_fixed'), now, datetime.now(SA_TIME)
    except:
        return pd.DataFrame(), datetime.now().date(), datetime.now()

st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", use_container_width=True)
df_live, today_date, update_time = load_live_data()

# WEERGAWE NOMMER VIR TOETSING
st.write(f"**App Version: 3.0** | Updated: {update_time.strftime('%H:%M')}")

if st.button("🔄 DRUK HIER VIR VARS DATA"):
    st.cache_data.clear()
    st.rerun()

if not df_live.empty:
    # FILTERS
    view_range = st.radio("View:", ["All", "Next 7 Days"], horizontal=True)
    category_sel = st.selectbox("Category:", ["All", "Sport", "Culture", "Academics"])
    
    f_df = df_live
    if view_range == "Next 7 Days":
        f_df = f_df[f_df['dt_fixed'].dt.date <= (today_date + timedelta(days=7))]
    if category_sel != "All":
        f_df = f_df[f_df.iloc[:, 0].str.contains(category_sel, case=False, na=False)]

    for _, r in f_df.iterrows():
        # Kolomme volgens jou lys: 1=Act, 2=Age, 4=Venue
        act_val = str(r.iloc[1])
        age_val = str(r.iloc[2]) if str(r.iloc[2]).lower() != 'nan' else ""
        date_val = r['dt_fixed'].strftime('%d %B %Y') if pd.notnull(r['dt_fixed']) else "TBA"
        venue_val = str(r.iloc[4])
        
        # Knoppies & Tekste (5=Prog, 6=Team, 7=Conf, 8=Info)
        buttons = []
        team_note = ""
        other_notes = []
        
        for idx, lbl in [(5, "PROGRAMME"), (6, "TEAM"), (7, "CONFIRM"), (8, "INFORMATION")]:
            cell = str(r.iloc[idx]).strip()
            if cell.lower() == 'nan' or not cell: continue
            
            # Soek vir enige skakel
            link = re.search(r'(https?://[^\s<>"]+)', cell)
            if link:
                buttons.append(f'<a href="{link.group(0)}" target="_blank" class="btn">{lbl}</a>')
                # As daar teks saam met die skakel is, hou dit vir notas
                txt = cell.replace(link.group(0), "").strip()
                if txt and lbl != "TEAM": other_notes.append(txt)
            else:
                if lbl == "TEAM": team_note = cell
                else: other_notes.append(cell)
        
        # Results (Kolom 9)
        res = str(r.iloc[9]).strip() if len(r) > 9 else ""
        if res.lower() != 'nan' and res: other_notes.append(f"Result: {res}")

        # HTML Vertoning
        st.markdown(f"""
        <div class="card">
            <div style="color:#666; font-size:0.8rem;">🗓️ {date_val}</div>
            <div class="t">{act_val} {age_val}</div>
            <div style="color:#333; font-size:0.85rem;">📍 {venue_val}</div>
            {f'<div class="team-box"><b>TEAMS:</b><br>{team_note}</div>' if team_note else ""}
            <div class="btn-row">{"".join(buttons)}</div>
            {f'<div class="box"><b>Note:</b><br>{"<br>".join(other_notes)}</div>' if other_notes else ""}
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("Geen fixtures gevind nie.")
