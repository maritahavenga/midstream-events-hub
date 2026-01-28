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
st_autorefresh(interval=120000, key="datarefresh")

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

def fix_drive_link(url):
    u = str(url).strip()
    if "drive.google.com" in u:
        if "id=" in u:
            f_id = u.split("id=")[-1].split("&")[0]
        elif "/d/" in u:
            f_id = u.split("/d/")[1].split("/")[0]
        else: return u
        return f"https://drive.google.com/file/d/{f_id}/view?usp=sharing"
    return u

def clean_text(text, is_group=False, is_category=False):
    if not text or str(text).lower() == 'nan': return ""
    t = str(text).strip()
    
    if is_category:
        low_t = t.lower()
        if "acad" in low_t: return "Academics"
        if "sport" in low_t: return "Sport"
        if "cult" in low_t or "kult" in low_t: return "Culture"
        return t.capitalize()

    if is_group:
        # Stap 1: Kry die nommer (ouderdom)
        nums = re.findall(r'\d+', t)
        age = nums[0] if nums else ""
        
        # Stap 2: Bepaal geslag
        gender = ""
        low_t = t.lower()
        if "g" in low_t or "dogter" in low_t or "girl" in low_t:
            gender = "Girls"
        elif "b" in low_t or "seun" in low_t or "boy" in low_t:
            gender = "Boys"
            
        # Stap 3: Kyk vir span-letters (A, B, C)
        team = ""
        if re.search(r'\b[Aa]$|\s[Aa]\s', t): team = " A"
        elif re.search(r'\b[Bb]$|\s[Bb]\s', t): team = " B"
        elif re.search(r'\b[Cc]$|\s[Cc]\s', t): team = " C"
        
        # Stap 4: BOU DIT PRESIES: Hoofletter U, Nommer VAS, Spasie, Geslag
        # Resultaat: U12 Girls
        if age:
            return f"U{age} {gender}{team}".strip()
        return t

    # Aktiwiteit vertaling
    t = t.replace("Hokkie", "Hockey").replace("hokkie", "Hockey")
    t = t.replace("Rugbi", "Rugby").replace("rugbi", "Rugby")
    t = t.replace("Atletiek", "Athletics").replace("atletiek", "Athletics")
    t = t.replace("Netbal", "Netball").replace("netbal", "Netball")
    return t

@st.cache_data(ttl=5)
def load_data():
    try:
        r = requests.get(f"{URL}&cb={datetime.now().timestamp()}", timeout=10)
        df = pd.read_csv(io.StringIO(r.content.decode('utf-8')))
        if df.empty or len(df.columns) < 6: return pd.DataFrame()
        df['category_display'] = df.iloc[:, 2].apply(lambda x: clean_text(x, is_category=True))
        df['activity_display'] = df.iloc[:, 3].apply(lambda x: clean_text(x))
        df['group_display'] = df.iloc[:, 4].apply(lambda x: clean_text(x, is_group=True))
        df['dt_fixed'] = pd.to_datetime(df.iloc[:, 5], dayfirst=True, errors='coerce')
        return df
    except: return pd.DataFrame()

df_raw = load_data()
SA_TIME = pytz.timezone('Africa/Johannesburg')
today = datetime.now(SA_TIME).date()

# 2. Styling
st.markdown("""<style>[data-testid="stHeader"] {display: none;} .block-container {padding:0 !important;} div.stButton > button {background-color: #800000 !important; color: white !important; border-radius: 10px; font-weight: bold; width: 100%; border:none;}</style>""", unsafe_allow_html=True)
st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", use_container_width=True)
st.markdown("<div style='background:#008080; color:white; text-align:center; padding:15px; font-size:1.4rem; font-weight:700; border-bottom: 5px solid #800000;'>Laerskool Midstream College Primary Event Hub</div>", unsafe_allow_html=True)

# 3. Filters
with st.container():
    st.markdown("<div style='background:white; padding:20px; border-radius:0 0 20px 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);'>", unsafe_allow_html=True)
    search_q = st.text_input("🔍 Search:", placeholder="Type here...").lower().strip()
    col1, col2 = st.columns(2)
    with col1:
        cat_f = st.selectbox("Category:", ["All", "Sport", "Culture", "Academics"])
    with col2:
        act_opts = sorted(df_raw['activity_display'].dropna().unique().tolist()) if not df_raw.empty else []
        act_f = st.multiselect("Activities:", act_opts)
    if st.button("🔄 REFRESH DATA"):
        st.cache_data.clear()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# 4. Vertoon
if df_raw.
