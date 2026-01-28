import streamlit as st
import pandas as pd
import re
from datetime import datetime
import pytz
import requests
import io
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

# 1. Basiese Konfigurasie
st.set_page_config(page_title="LMCP Event Hub", layout="centered")
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
    """Logika vir U13C Boys formaat."""
    if not text or str(text).lower() == 'nan': return ""
    t = str(text).strip().upper()
    
    # 1. Kry die nommer (ouderdom)
    nums = re.findall(r'\d+', t)
    age = nums[0] if nums else ""
    
    # 2. Bepaal geslag
    gender = ""
    if any(x in t for x in ["G", "DOGTER", "GIRL"]): gender = "Girls"
    elif any(x in t for x in ["B", "SEUN", "BOY"]): gender = "Boys"
    
    # 3. Kyk vir span-letters (A, B, C)
    team = ""
    if " A" in t or "A " in t or t.endswith("A") or "U13A" in t.replace(" ",""): team = "A"
    elif " B" in t or "B " in t or t.endswith("B") or "U13B" in t.replace(" ",""): team = "B"
    elif " C" in t or "C " in t or t.endswith("C") or "U13C" in t.replace(" ",""): team = "C"
    
    # BOU DIT: U[Ouderdom][Span] [Spasie] [Geslag]
    # Resultaat: U13C Boys
    if age:
        return f"U{age}{team} {gender}".strip()
    return t

@st.cache_data(ttl=5)
def load_data():
    try:
        r = requests.get(f"{URL}&cb={datetime.now().timestamp()}", timeout=10)
        df = pd.read_csv(io.StringIO(r.content.decode('utf-8')))
        if df.empty: return pd.DataFrame()
        
        df['activity_display'] = df.iloc[:, 3].fillna("").astype(str).str.replace("Hokkie", "Hockey").str.replace("Netbal", "Netball").str.replace("Rugbi", "Rugby").str.replace("Atletiek", "Athletics")
        df['group_display'] = df.iloc[:, 4].apply(format_group_final)
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
    search_q = st.text_input("🔍 Search:", placeholder="Search...").lower().strip()
    if st.button("🔄 REFRESH DATA"):
        st.cache_data.clear()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# 4. Vertoon
if not df_raw.empty:
    df = df_raw.copy()
    if 'dt_fixed' in df.columns:
        df = df[(df['dt_fixed'].dt.date >= today) | (df['dt_fixed'].isnull())]
        df = df.sort_values(by=['dt_fixed', 'activity_display'], ascending=[True, True])

    if search_q:
        df = df[df.apply(lambda r: search_q in " ".join(str(v) for v in
