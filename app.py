import streamlit as st
import pandas as pd
import re
from datetime import datetime
import pytz
import requests
import io
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

# 1. Instellings & Data Bron
st.set_page_config(page_title="LMCP Event Hub", layout="centered")
st_autorefresh(interval=120000, key="datarefresh")

# Jou CSV Publieke Skakel
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?gid=0&single=true&output=csv"

def fix_drive_link(url):
    """Sorg dat Google Drive skakels direk oopmaak"""
    if "drive.google.com" in str(url) and "id=" in str(url):
        file_id = str(url).split("id=")[-1].split("&")[0]
        return f"https://drive.google.com/file/d/{file_id}/view"
    return str(url)

def clean_text(text, is_group=False, is_category=False):
    if not text or str(text).lower() == 'nan': return ""
    t = str(text).strip()
    if is_category:
        low_c = t.lower()
        if "acad" in low_c: return "Academics"
        if "sport" in low_c: return "Sport"
        if "cult" in low_c or "kult" in low_c: return "Culture"
    if is_group:
        nums = re.findall(r'\d+', t)
        if nums:
            age_num = nums[0]
            suffix = " Girls" if "girl" in t.lower() else (" Boys" if "boy" in t.lower() else "")
            return f"U{age_num}{suffix}"
    return t.capitalize() if t.isupper() else t

@st.cache_data(ttl=10)
def load_data():
    try:
        # Voeg 'n tydstempel by om Google se "cache" te breek
        r = requests.get(f"{URL}&cb={datetime.now().timestamp()}", timeout=10)
        df = pd.read_csv(io.StringIO(r.content.decode('utf-8')))
        if df.empty or len(df.columns) < 4: return pd.DataFrame()
        
        # Maak basiese teks skoon
        df.iloc[:, 0] = df.iloc[:, 0].apply(lambda x: clean_text(x, is_category=True))
        df.iloc[:, 1] = df.iloc[:, 1].apply(lambda x: clean_text(x))
        df.iloc[:, 2] = df.iloc[:, 2].apply(lambda x: clean_text(x, is_group=True))
        
        # Probeer datum omskakel maar moenie crash as dit faal nie
        def parse_dt(x):
            s = str(x).strip()
            if not s or s.lower() == 'nan': return pd.NaT
            try:
                if '202' not in s: s = f"{s} {datetime.now().year}"
                return pd.to_datetime(s, dayfirst=True, errors='coerce')
            except: return pd.NaT
        
        df['dt_fixed'] = df.iloc[:, 3].apply(parse_dt)
        return df
    except:
        return pd.DataFrame()

df_raw = load_data()
SA_TIME = pytz.timezone('Africa/Johannesburg')
today = datetime.now(SA_TIME).date()

# 2. Visuele Styl (CSS)
st.markdown("<style>[data-testid='stHeader'] {display: none;} .block-container {padding:0 !important;} div.stButton > button {background-color: #800000 !important; color: white !important; border-radius: 10px; border: none; width: 100%; font-weight: bold; height: 3em;}</style>", unsafe_allow_html=True)
st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", use_container_width=True)
st.markdown("<div style='background:#008080; color:white; text-align:center; padding:15px; font-size:1.4rem; font-weight:700; border-bottom: 5px solid #800000;'>Laerskool Midstream College Primary Event Hub</div>", unsafe_allow_html=True)

# 3. Filters en Soek
with st.container():
    st.markdown("<div style='background:white; padding:20px; border-radius:0 0 20px 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);'>", unsafe_allow_html=True)
    search_q = st.text_input("🔍 Search (e.g. Rugby or U10):", placeholder="Type here...").lower().strip()
    col1, col2 = st.columns(2)
    with col1:
        cat_f = st.selectbox("Category:", ["All", "Sport", "Culture", "Academics"])
    with col2:
        act_opts = sorted(df_raw.iloc[:, 1].dropna().unique().tolist()) if not df_raw.empty else []
        act_f = st.multiselect("Activities:", act_opts)
    if st.button("🔄 REFRESH DATA"):
        st.cache_data.clear()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# 4. Vertoon Logika
if df_raw.empty:
    st.info("No data found. Ensure your 'Upcoming' sheet has entries.")
else:
    df = df_raw.copy()
    
    # Sorteer volgens datum (as beskikbaar)
    if 'dt_fixed' in df.columns:
        df = df.sort_values('dt_fixed', ascending=True)

    # Pas filters toe
    if cat_f != "All":
        df = df[df.iloc[:, 0] == cat_f]
    if act_f:
        df = df[df.iloc[:, 1].isin(act_f)]
    if search_q:
        df = df[df.apply(lambda r: search_q in " ".join(str(v) for v in r.values).lower(), axis=1)]

    if df.empty:
        st.write("No events matching your search.")
    else:
        # Bou die kaartjies met HTML
        h = """<style>body { background:#008080; font-family:sans-serif; padding:15px; } .card { background:white; padding:20px; border-radius:15px; border-left:10px solid #800000; margin-bottom:15px; box-shadow:0 4px 8px rgba(0,0,0,0.1); } .card-title { color:#800000; font-size:1.2rem; font-weight:bold; } .btn { background:#800000 !important; color:white !important; padding:8px 12px; border-radius:8px; text-decoration:none; font-size:0.7rem; display:inline-block; margin-right:5px; margin-top:10px; font-weight:bold; }</style>"""
        
        for _, r in df.iterrows():
            cat, sport, age, raw_dt, ven = str(r.iloc[0]), str(r.iloc[1]), str(r.iloc[2]), str(r.iloc[3]), str(r.iloc[4])
            
            # Wys die geformatteerde datum, of die rou teks as dit nie 'n datum is nie
            display_date = r['dt_fixed'].strftime('%d %B %Y') if pd.notnull(r['dt_fixed']) else raw_dt
            
            btns, extra = "", ""
            # Soek vir links in kolomme F, G, H
            for i in [5, 6, 7]:
                if i < len(r):
                    val = str(r.iloc[i])
                    if "https://" in val:
                        lbl = "PROGRAMME" if i == 5 else ("TEAM LIST" if i == 6 else "DOCUMENT")
                        btns += f"<a href='{fix_drive_link(val)}' target='_blank' class='btn'>{lbl}</a> "
            
            # Note kolom (I)
            if len(r) > 8:
                info_val = str(r.iloc[8])
                if info_val.lower() != 'nan' and info_val.strip() != "":
                    extra = f"<div style='font-size:0.8rem; margin-top:10px; color:#333; border-top:1px solid #eee; padding-top:5px;'><b>Note:</b> {info_val}</div>"

            h += f"<div class='card'><div style='font-size:0.8rem; color:#666;'>{display_date} | {cat}</div><div class='card-title'>{sport} {age}</div><div style='color:#008080;'>📍 {ven}</div>{btns}{extra}</div>"
        
        components.html(h, height=2500, scrolling=True)

st.markdown("<div style='background:#800000; color:white; text-align:center; padding:15px; font-size:0.8rem;'>Laerskool Midstream College Primary · Event Hub 2026</div>", unsafe_allow_html=True)
