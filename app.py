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
st.set_page_config(page_title="LMCP Events & Results", layout="centered")
st_autorefresh(interval=120000, key="datarefresh")

# 2. Styling
st.markdown("""<style>
.stApp{background:#008080}.block-container{padding:1rem;max-width:500px}
.stTabs [data-baseweb="tab-list"] {gap: 8px; background-color: #008080; justify-content: center;}
.stTabs [data-baseweb="tab"] { height: 45px; background-color: #800000; color: white; border-radius: 10px 10px 0px 0px; font-weight: bold; border: 1px solid #00cccc;}
.stTabs [aria-selected="true"] { background-color: #00cccc !important; }
.card{background:white!important;padding:18px;border-radius:15px;border-left:12px solid #800000;margin-bottom:15px;box-shadow:0 4px 10px rgba(0,0,0,0.2)}
.t{color:#800000!important;font-weight:bold;font-size:1.15rem;margin:5px 0}.v{color:#800000!important;font-weight:bold;text-decoration:underline}
.box{background:#f8f9fa;padding:12px;border-radius:10px;margin:10px 0;border-left:5px solid #008080;color:#333;font-size:0.9rem;line-height:1.4}
.team-box{background:#fff3f3;padding:10px;border-radius:8px;margin:5px 0;border:1px dashed #800000;color:#800000;font-size:0.85rem}
.res-box{background:#e6f4ea; padding:10px; border-radius:8px; margin:5px 0; border:1px solid #1e7e34; color: #1e7e34; font-weight:bold; text-align:center;}
.btn-row {display:flex!important; gap:4px!important; justify-content:space-between!important; margin-top:15px!important; width:100%!important;}
.btn { flex:1!important; background:#800000!important; color:white!important; text-align:center!important; text-decoration:none!important; font-weight:bold!important; font-size:0.65rem!important; padding:12px 2px!important; border-radius:6px!important; display:block!important; white-space:nowrap!important;}
.res-btn { background:#1e7e34!important; border: 2px solid #ffffff !important; }
#back-to-top { position: fixed; bottom: 90px; right: 20px; background-color: #800000; color: white !important; width: 45px; height: 45px; line-height: 45px; text-align: center; border-radius: 50%; z-index: 99999; border: 2px solid white; }
h2 { color: white !important; text-align: center; margin-top: -10px; text-transform: uppercase; }
div[data-baseweb="select"] > div { background-color:#800000 !important; border:none !important; }
div[data-baseweb="select"] * { color:white !important; }
label { color:white !important; font-weight:bold; }
.stButton>button { width:100%; background-color:#800000; color:white; border:2px solid #00cccc; font-size:0.9rem; border-radius:10px; height:45px; font-weight:bold; margin-bottom:10px;}
</style>
<div id="top"></div>
<a href="#top" id="back-to-top">↑</a>
""", unsafe_allow_html=True)

URL_DATA = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?gid=0&single=true&output=csv"

def load_all_data():
    try:
        SA_TIME = pytz.timezone('Africa/Johannesburg')
        now = datetime.now(SA_TIME).date()
        response = requests.get(f"{URL_DATA}&refresh={int(time.time())}", timeout=10)
        df = pd.read_csv(io.StringIO(response.text))
        def parse_dt(x):
            s = str(x).strip()
            if not s or s.lower() == 'nan': return pd.NaT
            if '202' not in s: s = f"{s} 2026"
            return pd.to_datetime(s, dayfirst=True, errors='coerce')
        df['dt_fixed'] = df.iloc[:, 3].apply(parse_dt)
        return df, now, datetime.now(SA_TIME)
    except:
        return pd.DataFrame(), datetime.now().date(), datetime.now()

def get_l(val):
    t = str(val).strip()
    m = re.search(r'https?://[^\s<>"]+', t)
    return m.group(0) if m else None

def smart_filter(df, query):
    if not query: return df
    q = query.lower().strip()
    translations = {"hokkie": "hockey", "atletiek": "athletics", "swem": "swimming", "muurbal": "squash", "seuns": "b", "meisies": "g"}
    for k, v in translations.items(): q = q.replace(k, v)
    
    terms = q.split()
    for term in terms:
        clean = term.replace("o/","").replace("u/","").replace(" ","")
        if not clean: continue
        if clean in ['b', 'g']:
            mask = df.iloc[:, 2].astype(str).str.lower().str.contains(clean, na=False)
        else:
            mask = df.apply(lambda r: clean in str(r).lower().replace("o/","").replace("u/","").replace(" ",""), axis=1)
        df = df[mask]
    return df

st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", use_container_width=True)
df_all, today_date, update_time = load_all_data()

tab_up, tab_res = st.tabs(["🗓️ UPCOMING", "🏆 RESULTS"])

with tab_up:
    st.markdown("<h2>Upcoming Fixtures</h2>", unsafe_allow_html=True)
    if not df_all.empty:
        df_up_raw = df_all[df_all['dt_fixed'].dt.date >= today_date].sort_values(by='dt_fixed')
        if st.button(f"🔄 REFRESH ({update_time.strftime('%H:%M')})", key="ref_up"):
            st.cache_data.clear()
            st.rerun()

        view_opt = st.radio("View:", ["All", "Next 7 Days"], horizontal=True, key="v_up")
        raw_s = st.text_input("🔍 Search:", placeholder="e.g. u13 hockey", key="search_up")
        
        c = st.columns([1, 1, 1])
        with c[0]: cat = st.selectbox("Type:", ["All", "Sport", "Culture", "Academics"], key="c_up")
        f_df = df_up_raw if cat == "All" else df_up_raw[df_up_raw.iloc[:, 0].str.contains(cat, case=False, na=False)]
        if view_opt == "Next 7 Days": f_df = f_df[f_df['dt_fixed'].dt.date <= (today_date + timedelta(days=7))]
        
        with c[1]: sel_acts = st.multiselect("Activity:", sorted(f_df.iloc[:, 1].dropna().unique()), key="a_up")
        with c[2]: sel_ages = st.multiselect("Age Group:", sorted(f_df.iloc[:, 2].dropna().unique()), key="ag_up")

        df = f_df
        if sel_acts: df = df[df.iloc[:, 1].isin(sel_acts)]
        if sel_ages: df = df[df.iloc[:, 2].isin(sel_ages)]
        df = smart_filter(df, raw_s)

        if not df.empty:
            for _, r in df.iterrows():
                age_val = str(r.iloc[2]).strip()
                title = f"{r.iloc[1]} {age_val}" if (age_val.lower() != 'nan') else str(r.iloc[1])
                dat = r['dt_fixed'].strftime('%d %B %Y') if pd.notnull(r['dt_fixed']) else "TBA"
                ven = str(r.iloc[4])
                prog_l, team_val = get_l(r.iloc[5]), str(r.iloc[6]).strip()
                team_l, conf_l = get_l(team_val), get_l(r.iloc[7])
                info_val, info_l = str(r.iloc[8]).strip(), get_l(str(r.iloc[8]))
                mu = f"https://www.google.com/maps/search/?api=1&query={up.quote(ven + ' Midstream')}"
                bx = f'<div class="box"><b>Note:</b> {info_val}</div>' if (info_val.lower()!='nan' and not info_l) else ""
                tm_bx = f'<div class="team-box"><b>Team:</b> {team_val}</div>' if (team_val.lower()!='nan' and not team_l) else ""
                
                btns = '<div class="btn-row">'
                if prog_l: btns += f'<a href="{prog_l}" target="_blank" class="btn">PROGRAMME</a>'
                if team_l: btns += f'<a href="{team_l}" target="_blank" class="btn">TEAM</a>'
                if conf_l: btns += f'<a href="{conf_l}" target="_blank" class="btn">CONFIRM</a>'
                if info_l: btns += f'<a href="{info_l}" target="_blank" class="btn">INFO</a>'
                btns += '</div>'
                st.markdown(f'<div class="card"><div style="font-size:0.85rem;color:#333">🗓️ {dat}</div><div class="t">{title}</div><div style="font-size:0.85rem;color:#333">📍 <a href="{mu}" target="_blank" class="v">{ven}</a></div>{bx}{tm_bx}{btns}</div>', unsafe_allow_html=True)

with tab_res:
    st.markdown("<h2>Match Results</h2>", unsafe_allow_html=True)
    if not df_all.empty:
        df_past = df_all[df_all['dt_fixed'].dt.date < today_date].sort_values(by='dt_fixed', ascending=False)
        raw_res_s = st.text_input("🔍 Search History:", placeholder="Search...", key="search_res")
        df_res = smart_filter(df_past, raw_res_s)
        if not df_res.empty:
            for _, r in df_res.iterrows():
                res_raw = str(r.iloc[9]).strip() if len(r) > 9 else ""
                res_link = get_l(res_raw)
                dat_res = r['dt_fixed'].strftime('%d %b %Y') if pd.notnull(r['dt_fixed']) else "TBA"
                age_res = str(r.iloc[2]).strip()
                title_res = f"{r.iloc[1]} {age_res}" if (age_res.lower() != 'nan') else str(r.iloc[1])
                res_disp = f'<div class="btn-row"><a href="{res_link}" target="_blank" class="btn res-btn" style="background:#1e7e34!important;">🏆 VIEW RESULTS</a></div>' if res_link else (f'<div class="res-box">🏆 RESULT: {res_raw}</div>' if (res_raw.lower() != 'nan' and res_raw != "") else '<div class="res-box" style="background:#f8f9fa; border-color:#ccc; color:#666;">🏆 Result Pending</div>')
                st.markdown(f'<div class="card"><div style="font-size:0.85rem; color:#666;">🗓️ {dat_res} | 📍 {r.iloc[4]}</div><div class="t">{title_res}</div>{res_disp}</div>', unsafe_allow_html=True)
