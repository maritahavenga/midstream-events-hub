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

def format_group_final(age_val, team_val):
    """Hanteer 11.0, NAN en 46308.0 datums."""
    age_str = str(age_val).upper().replace(".0", "").replace("NAN", "").strip()
    team_str = str(team_val).upper().replace("NAN", "").strip()
    combined = f"{age_str} {team_str}"
    
    # 1. Soek vir nommers, maar ignoreer Excel datums (bv. 46308)
    all_nums = re.findall(r'\d+', combined)
    valid_nums = [n for n in all_nums if len(n) < 4] # Net ouderdomme, nie datums nie
    
    if not valid_nums: return combined.replace("  ", " ").strip()
    
    # Bepaal ouderdom-deel
    if len(valid_nums) >= 2:
        age_part = f"U{valid_nums[0]}-U{valid_nums[1]}"
    else:
        age_part = f"U{valid_nums[0]}"
    
    # 2. Soek Span (A, B, C)
    team = ""
    for letter in ["A", "B", "C"]:
        if re.search(rf"\b{letter}\b", combined):
            team = letter
            break
            
    # 3. Soek Geslag
    gender = ""
    if any(x in combined for x in ["GIRL", "DOGTER"]): gender = "Girls"
    elif any(x in combined for x in ["BOY", "SEUN"]): gender = "Boys"
    
    return f"{age_part}{team} {gender}".strip()

@st.cache_data(ttl=2)
def load_data(url):
    try:
        r = requests.get(f"{url}&cb={datetime.now().timestamp()}", timeout=10)
        df = pd.read_csv(io.StringIO(r.content.decode('utf-8')))
        if df.empty: return pd.DataFrame()
        df = df.replace(['N/A', 'n/a', 'NA', 'na', 'nan', 'NAN'], '', regex=True)
        # Unieke ID vir duplikate
        df['unique_id'] = df.iloc[:, 5].astype(str) + df.iloc[:, 3].astype(str) + df.iloc[:, 4].astype(str) + df.iloc[:, 11].astype(str) + df.iloc[:, 6].astype(str)
        df = df.drop_duplicates(subset=['unique_id'], keep='last')
        return df
    except: return pd.DataFrame()

# Branding
st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", use_container_width=True)
st.markdown("<div style='background:#008080; color:white; text-align:center; padding:15px; font-size:1.4rem; font-weight:700; border-bottom: 5px solid #800000;'>Laerskool Midstream College Primary Digital Hub</div>", unsafe_allow_html=True)

df_raw = load_data(EVENTS_URL)
SA_TIME =
