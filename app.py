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
st.set_page_config(page_title="LMCP Events Hub", layout="centered")
st_autorefresh(interval=120000, key="datarefresh")

# 2. CSS Styling
st.markdown("""<style>
.stApp{background:#008080}.block-container{padding:1rem;max-width:500px}
.stTabs [data-baseweb="tab-list"] {gap: 8px; background-color: #008080; justify-content: center;}
.stTabs [data-baseweb="tab"] { height: 45px; background-color: #800000; color: white; border-radius: 10px 10px 0px 0px; font-weight: bold; border: 1px solid #00cccc;}
.stTabs [aria-selected="true"] { background-color: #00cccc !important; }
.card{background:white!important;padding:18px;border-radius:15px;border-left:12px solid #800000;margin-bottom:15px;box-shadow:0 4px 10px rgba(0,0,0,0.2)}
.t{color:#800000!important;font-weight:bold;font-size:1.15rem;margin:5px 0}.v{color:#800000!important;font-weight:bold;text-decoration:underline}
.res-box{background:#e6f4ea; padding:10px; border-radius:8px; margin:5px 0; border:1px solid #1e7e34; color: #1e7e34; font-weight:bold; text-align:center;}
.btn-row {display:flex!important; gap:4px!important; justify-content:space-between!important; margin-top:15px!important;}
.btn { flex:1!important; background:#800000!important; color:white!important; text-align:center!important; text-decoration:none!important; font-weight:bold!important; font-size:0.65rem!important; padding:12px 2px!important; border-radius:6px!important; display:block!important; white-space:nowrap!important;}
#back-to-top { position: fixed; bottom: 90px; right: 20px; background-color: #800000; color: white !important; width: 45px; height: 45px; line-height: 45px; text-align: center; border-radius: 50%; z-index: 99999; border: 2px solid white; }
div[data-baseweb="select"] > div { background-color:#800000 !important; border:none !important; }
div[data-baseweb="select"] * { color:white !important; }
label { color:white !important; font-weight:bold; }
.stButton>button { width:100%; background-color:#800000; color:white; border:2px solid #00cccc; font-size:0.9rem; border-radius:10px; height:45px; font-weight:bold; margin-bottom:10px;}
</style>
<div id="top"></div>
<a href="#top" id="back-to-top">↑</a>
""", unsafe_allow_html=True)

# --- DATA URLs ---
# Make sure GID 0 is your Results and 1966566702 is your Upcoming
URL_BASE = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?"
URL_UPCOMING = f"{URL_BASE}gid=1966566702&single=true&output=csv"
URL_RESULTS = f"{URL_BASE}gid=0&single=true&output=csv"

def get_data(url, is_upcoming=True):
    try:
        SA_TIME = pytz.timezone('Africa/Johannesburg')
        now = datetime.now(SA_TIME).date()
        response = requests.get(f"{url}&refresh={int(time.time())}", timeout=10)
        df = pd.read_csv(io.StringIO(response.text))
        
        # SAFETY CHECK: If the sheet is empty or columns are missing
        if df.empty or len(df.columns) < 4:
            return pd.DataFrame(), now, datetime.now(SA_TIME)

        def parse_dt(x):
            s = str(x).strip()
            if not s or s.lower() == 'nan': return pd.NaT
            if '202' not in s: s = f"{s} 2026"
            return pd.to_datetime(s, dayfirst=True, errors='coerce')
        
        df['dt_fixed'] = df.iloc[:, 3].apply(parse_dt)
        if is_upcoming:
            df = df[df['dt_fixed'].dt.date >= now].sort_values(by='dt_fixed')
            if len(df.columns) > 2:
                df.iloc[:, 2] = df.iloc[:, 2].astype(str).apply(lambda x: x.replace(" ", "").upper() if x.lower() != 'nan' else "")
        else:
            df = df.sort_values(by='dt_fixed', ascending=False)
        return df, now, datetime.now(SA_TIME)
    except:
        return pd.DataFrame(), datetime.now().date(), datetime.now()

def get_l(val):
    t = str(val).strip()
    m = re.search(r'https?://[^\s<>"]+', t)
    return m.group(0) if m else None

# --- UI LOGIC ---
st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", use_container_width=True)
tab_up, tab_res = st.tabs(["🗓️ UPCOMING", "🏆 PAST RESULTS"])

with tab_up:
    df_raw, today_date, update_time = get_data(URL_UPCOMING, is_upcoming=True)
    if not df_raw.empty:
        if st.button(f"🔄 REFRESH DATA ({update_time.strftime('%H:%M')})", key="ref_up"):
            st.cache_data.clear()
            st.rerun()

        view_opt = st.radio("View Range:", ["All Upcoming", "Next 7 Days Only"], horizontal=True, key="view_up")
        raw_search = st.text_input("🔍 Search:", placeholder="U13B, Hockey...", key="search_up")
        
        # Search cleanup logic
        s = raw_search.lower()
        s = s.replace("boys", "b").replace("seuns", "b").replace("seun", "b").replace("boy", "b")
        s = s.replace("girls", "g").replace("dogters", "g").replace("dogter", "g").replace("girl", "g")
        s = s.replace("o/", "").replace("u/", "").replace("span", "").replace(" ", "")
        
        c = st.columns([1, 1, 1])
        with c[0]: cat = st.selectbox("Type:", ["All", "Sport", "Culture", "Academics"], key="cat_up")
        
        f_l = df_raw if cat == "All" else df_raw[df_raw.iloc[:, 0].str.contains(cat, case=False, na=False)]
        if view_opt == "Next 7 Days Only":
            f_l = f_l[f_l['dt_fixed'].dt.date <= (today_date + timedelta(days=7))]

        # Safety on dropdowns
        acts = sorted(f_l.iloc[:, 1].dropna().unique()) if not f_l.empty else []
        ages = sorted(f_l.iloc[:, 2].dropna().unique()) if not f_l.empty else []
        
        with c[1]: sel_acts = st.multiselect("Activity:", acts, key="act_up")
        with c[2]: sel_ages = st.multiselect("Age Group:", ages, key="age_up")

        df = f_l
        if sel_acts: df = df[df.iloc[:, 1].isin(sel_acts)]
        if sel_ages: df = df[(df.iloc[:, 2].isin(sel_ages)) | (df.iloc[:, 2] == "") | (df.iloc[:, 2].isna())]
        if s: df = df[df.apply(lambda r: s in str(r).replace("o/", "").replace("u/", "").replace(" ", "").lower(), axis=1)]

        for _, r in df.iterrows():
            age_val = str(r.iloc[2]).strip()
            display_title = f"{r.iloc[1]} {age_val}" if age_val else str(r.iloc[1])
            ven, dat = str(r.iloc[4]), r['dt_fixed'].strftime('%d %B %Y') if pd.notnull(r['dt_fixed']) else "TBA"
            prog_l, team_val = get_l(r.iloc[5]), str(r.iloc[6]).strip()
            team_l, conf_l = get_l(team_val), get_l(r.iloc[7])
            info_val, info_l = str(r.iloc[8]).strip(), get_l(str(r.iloc[8]))
            mu = f"https://www.google.com/maps/search/?api=1&query={up.quote(ven + ' Midstream')}"
            
            bx = f'<div class="box"><b>Note:</b> {info_val}</div>' if (info_val and info_val.lower()!='nan' and not info_l) else ""
            tm_bx = f'<div class="team-box"><b>Team Info:</b> {team_val}</div>' if (team_val and team_val.lower()!='nan' and not team_l) else ""

            btns = '<div class="btn-row">'
            if prog_l: btns += f'<a href="{prog_l}" target="_blank" class="btn">PROGRAMME</a>'
            if team_l: btns += f'<a href="{team_l}" target="_blank" class="btn">TEAM</a>'
            if conf_l: btns += f'<a href="{conf_l}" target="_blank" class="btn">CONFIRM</a>'
            if info_l: btns += f'<a href="{info_l}" target="_blank" class="btn">INFO</a>'
            btns += '</div>'
            
            st.markdown(f'''<div class="card">
                <div style="font-size:0.85rem;color:#333">🗓️ {dat}</div>
                <div class="t">{display_title}</div>
                <div style="font-size:0.85rem;color:#333">📍 <a href="{mu}" target="_blank" class="v">{ven}</a></div>
                {bx}{tm_bx}{btns}</div>''', unsafe_allow_html=True)
    else:
        st.info("Syncing events hub...")

with tab_res:
    df_res_raw, _, update_res = get_data(URL_RESULTS, is_upcoming=False)
    if not df_res_raw.empty:
        search_res = st.text_input("🔍 Search Results:", placeholder="Rugby, U13A...", key="search_res")
        if search_res:
            df_res_raw = df_res_raw[df_res_raw.apply(lambda r: search_res.lower() in str(r).lower(), axis=1)]
        
        for _, r in df_res_raw.iterrows():
            res_val = str(r.iloc[8]).strip() if len(r) > 8 else "Pending"
            dat_res = r['dt_fixed'].strftime('%d %b %Y') if pd.notnull(r['dt_fixed']) else "TBA"
            st.markdown(f'''<div class="card">
                <div style="font-size:0.85rem;">🗓️ {dat_res}</div>
                <div class="t">{r.iloc[1]} {r.iloc[2]}</div>
                <div class="res-box">🏆 RESULT: {res_val}</div>
            </div>''', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="no-data"><h3>🏆 No results yet</h3><p>Ensure your "Results" sheet has headers and data.</p></div>', unsafe_allow_html=True)
