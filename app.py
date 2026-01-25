import streamlit as st
import pandas as pd
import urllib.parse as up
import re
from datetime import datetime
import pytz
import requests
import io
import time
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Events Hub", layout="centered")

# Auto-refresh every 2 minutes
st_autorefresh(interval=120000, key="datarefresh")

st.markdown("""<style>
.stApp{background:#008080}.block-container{padding:1rem;max-width:500px}
.card{background:white!important;padding:18px;border-radius:15px;border-left:12px solid #800000;margin-bottom:15px;box-shadow:0 4px 10px rgba(0,0,0,0.2)}
.t{color:#800000!important;font-weight:bold;font-size:1.15rem;margin:5px 0}.v{color:#800000!important;font-weight:bold;text-decoration:underline}
.box{background:#f8f9fa;padding:12px;border-radius:10px;margin:10px 0;border-left:5px solid #008080;color:#333;font-size:0.9rem;line-height:1.4}
.team-box{background:#fff3f3;padding:10px;border-radius:8px;margin:5px 0;border:1px dashed #800000;color:#800000;font-size:0.85rem}
/* The "No Data" Styling */
.no-data{text-align:center; padding:40px 20px; background:rgba(255,255,255,0.1); border-radius:15px; color:white; border:1px dashed white; margin-top:20px}
.btn-row {display:flex!important; gap:4px!important; justify-content:space-between!important; margin-top:15px!important; width:100%!important;}
.btn {
    flex:1!important; background:#800000!important; color:white!important; 
    text-align:center!important; text-decoration:none!important;
    font-weight:bold!important; font-size:0.65rem!important; padding:12px 2px!important;
    border-radius:6px!important; display:block!important; white-space:nowrap!important;
}
div[data-baseweb="select"] > div { background-color:#800000 !important; border:none !important; }
div[data-baseweb="select"] * { color:white !important; }
label { color:white !important; font-weight:bold; }
.sync-container {margin-top:30px; padding-bottom:50px;}
.stButton>button { width:100%; background-color:#800000; color:white; border:1px solid white; font-size:0.85rem; border-radius:10px; height:50px; font-weight:bold;}
</style>""", unsafe_allow_html=True)

U = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?gid=0&single=true&output=csv"

def load_fresh():
    SA_TIME = pytz.timezone('Africa/Johannesburg')
    now = datetime.now(SA_TIME).date()
    
    response = requests.get(f"{U}&refresh={int(time.time())}")
    response.encoding = 'utf-8' 
    df = pd.read_csv(io.StringIO(response.text))
    
    def parse_dt(x):
        s = str(x).strip()
        if not s or s.lower() == 'nan': return pd.NaT
        if '2026' not in s: s = f"{s} 2026"
        return pd.to_datetime(s, dayfirst=True, errors='coerce')
    
    df['dt_fixed'] = df.iloc[:, 3].apply(parse_dt)
    
    # Filter for future events only
    df = df[df['dt_fixed'].dt.date >= now].copy()
    
    # Standardize Age Groups
    if not df.empty:
        df.iloc[:, 2] = df.iloc[:, 2].astype(str).apply(lambda x: x.replace(" ", "").upper() if x.lower() != 'nan' else "")
    
    return df.sort_values(by='dt_fixed', ascending=True), datetime.now(SA_TIME)

def get_l(val):
    t = str(val).strip()
    m = re.search(r'https?://[^\s<>"]+', t)
    return m.group(0) if m else None

params = st.query_params
if 'cat_sel' not in st.session_state: st.session_state.cat_sel = params.get("type", "All")
if 'act_sel' not in st.session_state: st.session_state.act_sel = params.get_all("act")
if 'age_sel' not in st.session_state: st.session_state.age_sel = params.get_all("age")

try:
    df_raw, update_time = load_fresh() 
    
    st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", use_container_width=True)
    st.markdown("<h2 style='text-align:center;color:white;'>EVENTS HUB 2026</h2>", unsafe_allow_html=True)

    c = st.columns([1, 1, 1])
    with c[0]:
        cat = st.selectbox("Type:", ["All", "Sport", "Culture", "Academics"], key="cat_sel")
    
    f_l = df_raw if cat == "All" else df_raw[df_raw.iloc[:, 0].str.contains(cat, case=False, na=False)]
    
    unique_acts = sorted([x for x in f_l.iloc[:, 1].dropna().unique() if str(x).strip()])
    unique_ages = sorted([x for x in f_l.iloc[:, 2].dropna().unique() if str(x).strip() and str(x) != ""])
    
    with c[1]:
        sel_acts = st.multiselect("Activity:", unique_acts, key="act_sel")
    with c[2]:
        sel_ages = st.multiselect("Age:", unique_ages, key="age_sel")

    st.query_params.from_dict({"type": cat, "act": sel_acts, "age": sel_ages})

    df = f_l
    if sel_acts: df = df[df.iloc[:, 1].isin(sel_acts)]
    if sel_ages:
        df = df[(df.iloc[:, 2].isin(sel_ages)) | (df.iloc[:, 2] == "") | (df.iloc[:, 2].isna())]
    
    # CHECK: Is the filtered list empty?
    if df.empty:
        st.markdown(f'''<div class="no-data">
            <h3>📭 No information currently</h3>
            <p>Try changing your filters or check back later for updates.</p>
        </div>''', unsafe_allow_html=True)
    else:
        for _, r in df.iterrows():
            age_val = str(r.iloc[2]).strip()
            display_title = f"{r.iloc[1]} {age_val}" if age_val else str(r.iloc[1])
            ven, dat = str(r.iloc[4]), r['dt_fixed'].strftime('%d %B %Y')
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

    st.markdown("<div class='sync-container'>", unsafe_allow_html=True)
    if st.button(f"🔄 Sync Live Data ({update_time.strftime('%H:%M:%S')})"):
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

except Exception:
    st.info("Connecting to live data...")
