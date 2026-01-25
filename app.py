import streamlit as st
import pandas as pd
import urllib.parse as up
import re
from datetime import datetime
import pytz
import requests
import io

st.set_page_config(page_title="Events Hub", layout="centered")

st.markdown("""<style>
.stApp{background:#008080}.block-container{padding:1rem;max-width:500px}
.card{background:white!important;padding:18px;border-radius:15px;border-left:12px solid #800000;margin-bottom:15px;box-shadow:0 4px 10px rgba(0,0,0,0.2)}
.t{color:#800000!important;font-weight:bold;font-size:1.15rem;margin:5px 0}.v{color:#800000!important;font-weight:bold;text-decoration:underline}
.box{background:#f8f9fa;padding:12px;border-radius:10px;margin:10px 0;border-left:5px solid #008080;color:#333;font-size:0.9rem;line-height:1.4}
.team-box{background:#fff3f3;padding:10px;border-radius:8px;margin:5px 0;border:1px dashed #800000;color:#800000;font-size:0.85rem}
.btn-row {display: flex!important; gap: 4px!important; justify-content: space-between!important; margin-top: 15px!important; width: 100%!important;}
.btn {
    flex: 1!important; background: #800000!important; color: white!important; 
    text-align: center!important; text-decoration: none!important;
    font-weight: bold!important; font-size: 0.65rem!important; padding: 12px 2px!important;
    border-radius: 6px!important; display: block!important; white-space: nowrap!important;
}
div[data-baseweb="select"] > div { background-color: #800000 !important; border: none !important; }
div[data-baseweb="select"] * { color: white !important; }
label { color: white !important; font-weight: bold; }
.update-ts { text-align: center; color: white; font-size: 0.7rem; margin-top: 20px; opacity: 0.8; }
.cal-svg { width: 16px; height: 16px; vertical-align: middle; margin-right: 6px; fill: #555; }
</style>""", unsafe_allow_html=True)

CAL_SVG = '<svg class="cal-svg" viewBox="0 0 24 24"><path d="M19,4H18V2H16V4H8V2H6V4H5C3.89,4 3,4.9 3,6V20C3,21.1 3.89,22 5,22H19C20.1,22 21,21.1 21,20V6C21,4.9 20.1,4 19,4M19,20H5V9H19V20M5,7V6H19V7H5Z"/></svg>'

U = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=10) 
def load():
    response = requests.get(U)
    response.encoding = 'utf-8' 
    df = pd.read_csv(io.StringIO(response.text))
    def parse_dt(x):
        s = str(x).strip()
        if not s or s.lower() == 'nan': return pd.NaT
        if '2026' not in s: s = f"{s} 2026"
        return pd.to_datetime(s, dayfirst=True, errors='coerce')
    # Column D is now the Date
    df['dt_fixed'] = df.iloc[:, 3].apply(parse_dt)
    return df.sort_values(by='dt_fixed', ascending=True), datetime.now(pytz.timezone('Africa/Johannesburg'))

def get_l(val):
    t = str(val).strip()
    m = re.search(r'https?://[^\s<>"]+', t)
    return m.group(0) if m else None

if 'cat_sel' not in st.session_state: st.session_state.cat_sel = "All"
if 'act_sel' not in st.session_state: st.session_state.act_sel = []
if 'age_sel' not in st.session_state: st.session_state.age_sel = []

try:
    df_raw, update_time = load()
    
    # 3-Way Filtering: Category, Activity, and Age Group
    c = st.columns([1, 1, 1])
    with c[0]:
        cat = st.selectbox("Type:", ["All", "Sport", "Culture", "Academics"], key="cat_sel")
    
    f_l = df_raw if cat == "All" else df_raw[df_raw.iloc[:, 0].str.contains(cat, case=False, na=False)]
    
    # Activity List (Column B)
    acts = sorted(list(set(f_l.iloc[:, 1].dropna().astype(str).tolist())))
    with c[1]:
        sel_acts = st.multiselect("Activity:", acts, key="act_sel")
        
    # Age Group List (Column C)
    ages = sorted(list(set(f_l.iloc[:, 2].dropna().astype(str).tolist())))
    with c[2]:
        sel_ages = st.multiselect("Age:", ages, key="age_sel")

    # Apply all filters
    df = f_l
    if sel_acts:
        df = df[df.iloc[:, 1].isin(sel_acts)]
    if sel_ages:
        df = df[df.iloc[:, 2].isin(sel_ages)]
    
    for _, r in df.iterrows():
        # Adjust indices because of the new Age Group column
        title = f"{r.iloc[1]} {r.iloc[2]}" # Combined Activity + Age Group
        ven = str(r.iloc[4])
        dat = r['dt_fixed'].strftime('%d %B %Y') if pd.notnull(r['dt_fixed']) else str(r.iloc[3])
        
        prog_l, team_val = get_l(r.iloc[5]), str(r.iloc[6]).strip()
        team_l, conf_l = get_l(team_val), get_l(r.iloc[7])
        info_val = str(r.iloc[8]).strip()
        info_l = get_l(info_val)
        
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
            <div style="font-size:0.85rem;color:#333">{CAL_SVG} {dat}</div>
            <div class="t">{title}</div>
            <div style="font-size:0.85rem;color:#333">📍 <a href="{mu}" target="_blank" class="v">{ven}</a></div>
            {bx}{tm_bx}{btns}</div>''', unsafe_allow_html=True)

    st.markdown(f'<div class="update-ts">Live Data Updated: {update_time.strftime("%d %b %H:%M")}</div>', unsafe_allow_html=True)
except Exception:
    st.info("Refreshing...")
