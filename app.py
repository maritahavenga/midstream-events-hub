import streamlit as st
import pandas as pd
import re
from datetime import datetime
import pytz
import requests
import io
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

# 1. Konfigurasie
st.set_page_config(page_title="LMCP Event Hub", layout="centered")
# Outomatiese verfris elke 2 minute
st_autorefresh(interval=120000, key="datarefresh")

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

def fix_drive_link(url):
    u = str(url).strip()
    if "drive.google.com" in u:
        if "id=" in u: f_id = u.split("id=")[-1].split("&")[0]
        elif "/d/" in u: f_id = u.split("/d/")[1].split("/")[0]
        else: return u
        return f"https://drive.google.com/file/d/{f_id}/view?usp=sharing"
    return u

def format_group_final(text):
    if not text or str(text).lower() == 'nan': return ""
    t = str(text).strip().upper()
    nums = re.findall(r'\d+', t)
    age = nums[0] if nums else ""
    gender = ""
    if any(x in t for x in ["G", "DOGTER", "GIRL"]): gender = "Girls"
    elif any(x in t for x in ["B", "SEUN", "BOY"]): gender = "Boys"
    team = ""
    if re.search(r'\bA\b|[0-9]A', t): team = "A"
    elif re.search(r'\bB\b|[0-9]B', t): team = "B"
    elif re.search(r'\bC\b|[0-9]C', t): team = "C"
    if age: return f"U{age}{team} {gender}".strip()
    return t

@st.cache_data(ttl=5)
def load_data():
    try:
        r = requests.get(f"{URL}&cb={datetime.now().timestamp()}", timeout=10)
        df = pd.read_csv(io.StringIO(r.content.decode('utf-8')))
        if df.empty: return pd.DataFrame()
        df['activity_display'] = df.iloc[:, 3].fillna("").astype(str).str.replace("Hokkie", "Hockey", case=False).str.replace("Netbal", "Netball", case=False).str.replace("Rugbi", "Rugby", case=False).str.replace("Atletiek", "Athletics", case=False)
        df['group_display'] = df.iloc[:, 4].apply(format_group_final)
        df['dt_fixed'] = pd.to_datetime(df.iloc[:, 5], dayfirst=True, errors='coerce')
        return df
    except: return pd.DataFrame()

# 2. Styling (Nav Bar aanpassings)
st.markdown("""
<style>
    /* Maak die boonste wit spasie minder maar hou die nav bar funksioneel */
    .block-container {padding-top: 1rem !important; padding-bottom: 0rem !important;}
    
    /* Button styling */
    div.stButton > button {
        background-color: #800000 !important; 
        color: white !important; 
        border-radius: 10px; 
        font-weight: bold; 
        width: 100%; 
        border:none;
        transition: 0.3s;
    }
    div.stButton > button:active {
        transform: scale(0.98);
        background-color: #008080 !important;
    }
</style>
""", unsafe_allow_html=True)

st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", use_container_width=True)
st.markdown("<div style='background:#008080; color:white; text-align:center; padding:15px; font-size:1.4rem; font-weight:700; border-bottom: 5px solid #800000;'>Laerskool Midstream College Primary Event Hub</div>", unsafe_allow_html=True)

# 3. Filters met visuele feedback
with st.container():
    st.markdown("<div style='background:white; padding:20px; border-radius:0 0 20px 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);'>", unsafe_allow_html=True)
    search_q = st.text_input("🔍 Search Events:", placeholder="Search...").lower().strip()
    
    if st.button("🔄 REFRESH DATA"):
        with st.spinner('Updating events...'):
            st.cache_data.clear()
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# 4. Data laai en vertoon
df_raw = load_data()
SA_TIME = pytz.timezone('Africa/Johannesburg')
today = datetime.now(SA_TIME).date()

if not df_raw.empty:
    df = df_raw.copy()
    if 'dt_fixed' in df.columns:
        df = df[(df['dt_fixed'].dt.date >= today) | (df['dt_fixed'].isnull())]
        df = df.sort_values(by=['dt_fixed', 'activity_display'], ascending=[True, True])

    if search_q:
        df = df[df.apply(lambda r: search_q in " ".join(str(v) for v in r.values).lower(), axis=1)]

    h = """<style>
        body { background:#008080; font-family: sans-serif; padding:10px; } 
        .card { background:white; padding:20px; border-radius:15px; border-left:10px solid #800000; margin-bottom:15px; position:relative; box-shadow:0 4px 8px rgba(0,0,0,0.1); } 
        .card-title { color:#800000; font-size:1.25rem; font-weight:bold; margin:0; } 
        .btn { background:#800000 !important; color:white !important; padding:8px 12px; border-radius:8px; text-decoration:none; font-size:0.75rem; display:inline-block; margin-right:5px; margin-top:10px; font-weight:bold; } 
        @keyframes simple-blink { 0% {opacity: 1;} 50% {opacity: 0.1;} 100% {opacity: 1;} }
        .badge-style { position:absolute; top:15px; right:15px; background:#FFD700; color:#800000; padding:4px 8px; border-radius:5px; font-weight:bold; font-size:0.65rem; animation: simple-blink 1s infinite; } 
        .info-row { font-size:0.95rem; color:#008080; margin: 8px 0; font-weight: 500; }
    </style>"""
    
    for _, r in df.iterrows():
        sport_h, age_l = r['activity_display'], r['group_display']
        display_date = r['dt_fixed'].strftime('%d %B %Y') if pd.notnull(r['dt_fixed']) else str(r.iloc[5])
        venue = str(r.iloc[6]).upper()
        
        badge, note = "", ""
        if len(r) > 10 and str(r.iloc[10]).lower() != 'nan' and str(r.iloc[10]).strip() != "":
            info_text = str(r.iloc[10])
            if "$" in info_text: badge = "<div class='badge-style'>RECENT UPDATE</div>"
            if "https://" not in info_text: note = f"<div style='font-size:0.85rem; margin-top:10px; color:#333; border-top:1px solid #eee; padding-top:8px;'><b>Note:</b> {info_text.replace('$', '')}</div>"

        btns = ""
        for i in [7, 8, 10]:
            val = str(r.iloc[i]) if i < len(r) else ""
            if "https://" in val:
                lbl = "PROGRAMME" if i == 7 else ("TEAM LIST" if i == 8 else "INFORMATION")
                btns += f"<a href='{fix_drive_link(val)}' target='_blank' class='btn'>{lbl}</a> "

        h += f"<div class='card'>{badge}<div class='card-title'>{sport_h} {age_l}</div><div class='info-row'>🗓️ {display_date}</div><div class='info-row'>📍 {venue}</div>{btns}{note}</div>"
    
    components.html(h, height=2500, scrolling=True)
