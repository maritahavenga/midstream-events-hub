import streamlit as st
import pandas as pd
import re
from datetime import datetime, timedelta
import pytz
import requests
import io
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

# 1. Konfigurasie
st.set_page_config(page_title="LMCP Digital Hub", layout="centered")
st_autorefresh(interval=120000, key="datarefresh")

EVENTS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

def fix_drive_link(url):
    u = str(url).strip()
    if u.lower() in ["n/a", "na", "nan", "", "none"]: return ""
    if "drive.google.com" in u:
        if "id=" in u: f_id = u.split("id=")[-1].split("&")[0]
        elif "/d/" in u: f_id = u.split("/d/")[1].split("/")[0]
        else: return u
        return f"https://drive.google.com/file/d/{f_id}/view?usp=sharing"
    return u

def format_group_final(text):
    if not text or str(text).lower() in ["nan", "n/a", "na", ""]: return ""
    t = str(text).strip().upper()
    gender = "Girls" if any(x in t for x in ["G", "DOGTER", "GIRL"]) else ("Boys" if any(x in t for x in ["B", "SEUN", "BOY"]) else "")
    
    # Span-identifikasie (soek spesifiek vir A, B of C as losstaande letters)
    team = ""
    if re.search(r'\bA\b', t): team = "A"
    elif re.search(r'\bB\b', t): team = "B"
    elif re.search(r'\bC\b', t): team = "C"
    
    nums = re.findall(r'\d+', t)
    if not nums: return t
    age_part = f"U{nums[0]}-U{nums[1]}" if len(nums) >= 2 else f"U{nums[0]}"
    
    return f"{age_part}{team} {gender}".strip()

@st.cache_data(ttl=2)
def load_data(url):
    try:
        r = requests.get(f"{url}&cb={datetime.now().timestamp()}", timeout=10)
        df = pd.read_csv(io.StringIO(r.content.decode('utf-8')))
        if df.empty: return pd.DataFrame()
        df = df.replace(['N/A', 'n/a', 'NA', 'na', 'nan'], '', regex=True)
        
        # --- VERBETERDE SLIM FILTER ---
        # Ons kombineer Datum (5), Aktiwiteit (3) en Groep (4) om te keer dat A en B mekaar uitgooi.
        df['unique_id'] = df.iloc[:, 5].astype(str) + df.iloc[:, 3].astype(str) + df.iloc[:, 4].astype(str)
        df = df.drop_duplicates(subset=['unique_id'], keep='last')
        return df
    except: return pd.DataFrame()

# Branding
st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", use_container_width=True)
st.markdown("<div style='background:#008080; color:white; text-align:center; padding:15px; font-size:1.4rem; font-weight:700; border-bottom: 5px solid #800000;'>Laerskool Midstream College Primary Digital Hub</div>", unsafe_allow_html=True)

df_raw = load_data(EVENTS_URL)
SA_TIME = pytz.timezone('Africa/Johannesburg')
today = datetime.now(SA_TIME).date()

with st.container():
    st.markdown("<div style='background:white; padding:20px; border-radius:0 0 15px 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);'>", unsafe_allow_html=True)
    view_opt = st.radio("Show Events:", ["All Upcoming", "Next 7 Days"], horizontal=True)
    search_q = st.text_input("🔍 Search Events:", placeholder="Search anything...").lower().strip()
    if st.button("🔄 REFRESH HUB"):
        st.cache_data.clear()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

if not df_raw.empty:
    df = df_raw.copy()
    df['activity_display'] = df.iloc[:, 3].fillna("").astype(str).str.replace("Hokkie", "Hockey", case=False).str.replace("Netbal", "Netball", case=False).str.replace("Atletiek", "Athletics", case=False).str.replace("Rugbi", "Rugby", case=False)
    df['group_display'] = df.iloc[:, 4].apply(format_group_final)
    df['dt_fixed'] = pd.to_datetime(df.iloc[:, 5], dayfirst=True, errors='coerce')
    
    df = df[(df['dt_fixed'].dt.date >= today) | (df['dt_fixed'].isnull())]
    if view_opt == "Next 7 Days":
        df = df[df['dt_fixed'].dt.date <= (today + timedelta(days=7))]
    df = df.sort_values(by=['dt_fixed', 'activity_display'], ascending=[True, True])

    if search_q:
        df = df[df.apply(lambda r: search_q in " ".join(str(v) for v in r.values).lower(), axis=1)]

    h = """<style>
        body { background:#008080; font-family: sans-serif; padding:10px; } 
        .card { background:white; padding:20px; border-radius:15px; border-left:10px solid #800000; margin-bottom:15px; position:relative; box-shadow:0 4px 8px rgba(0,0,0,0.1); } 
        .card-title { color:#800000; font-size:1.25rem; font-weight:bold; margin-bottom:10px; } 
        .info-row { font-size:1rem; color:#333; margin: 8px 0; font-weight: 500; }
        .teal-link { color:#008080 !important; text-decoration:underline; font-weight:800; display: inline-block; }
        .btn { background:#800000 !important; color:white !important; padding:8px 12px; border-radius:8px; text-decoration:none; font-size:0.75rem; display:inline-block; margin-right:5px; margin-top:10px; font-weight:bold; } 
        .badge-style { position:absolute; top:15px; right:15px; background:#FFD700; color:#800000; padding:4px 8px; border-radius:5px; font-weight:bold; font-size:0.65rem; animation: blinker 1.2s linear infinite; } 
        @keyframes blinker { 50% { opacity: 0.2; } }
    </style>"""
    
    for _, r in df.iterrows():
        ven_raw = str(r.iloc[6]).strip().upper()
        prog_url = fix_drive_link(str(r.iloc[7]))
        
        if ven_raw in ["", "TBC", "N/A"]: ven_html = "📍 VENUE TBC"
        elif "SEE PROGRAMME" in ven_raw and prog_url:
            ven_html = f"📍 <a class='teal-link' href='{prog_url}' target='_blank'>SEE PROGRAMME</a>"
        else:
            m_q = f"Midstream+College+{ven_raw.replace(' ', '+')}" if "CORNWALL" not in ven_raw else ven_raw.replace(' ', '+')
            ven_html = f"📍 <a class='teal-link' href='https://www.google.com/maps/search/?api=1&query={m_q}' target='_blank'>{ven_raw}</a>"

        f_date = r['dt_fixed'].strftime('%d %B %Y') if pd.notnull(r['dt_fixed']) else str(r.iloc[5])
        badge = "<div class='badge-style'>UPDATE</div>" if "$" in str(r.iloc[10]) else ""
        btns = ""
        for i, lbl in zip([7, 8, 10], ["PROGRAMME", "TEAM LIST", "INFO"]):
            val = str(r.iloc[i]).strip()
            if "http" in val.lower(): btns += f"<a href='{fix_drive_link(val)}' target='_blank' class='btn'>{lbl}</a> "

        h += f"<div class='card'>{badge}<div class='card-title'>{r['activity_display']} {r['group_display']}</div><div class='info-row'>🗓️ {f_date}</div><div class='info-row'>{ven_html}</div><div style='display:block;'>{btns}</div></div>"
    
    components.html(h, height=2000, scrolling=True)

st.markdown("<div style='background:#800000; color:white; text-align:center; padding:15px; font-size:0.8rem;'>Laerskool Midstream College Primary · Digital Hub 2026</div>", unsafe_allow_html=True)
