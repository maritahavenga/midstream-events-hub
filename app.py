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
    if "drive.google.com" in str(url) and "id=" in str(url):
        f_id = str(url).split("id=")[-1].split("&")[0]
        return f"https://drive.google.com/file/d/{f_id}/view"
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
        r = requests.get(f"{URL}&cb={datetime.now().timestamp()}", timeout=10)
        df = pd.read_csv(io.StringIO(r.content.decode('utf-8')))
        if df.empty or len(df.columns) < 6: return pd.DataFrame()
        df.iloc[:, 2] = df.iloc[:, 2].apply(lambda x: clean_text(x, is_category=True))
        df.iloc[:, 3] = df.iloc[:, 3].apply(lambda x: clean_text(x))
        df.iloc[:, 4] = df.iloc[:, 4].apply(lambda x: clean_text(x, is_group=True))
        def parse_dt(x):
            s = str(x).strip()
            if not s or s.lower() == 'nan': return pd.NaT
            if '202' not in s: s = f"{s} {datetime.now().year}"
            return pd.to_datetime(s, dayfirst=True, errors='coerce')
        df['dt_fixed'] = df.iloc[:, 5].apply(parse_dt)
        return df
    except:
        return pd.DataFrame()

df_raw = load_data()
SA_TIME = pytz.timezone('Africa/Johannesburg')
today = datetime.now(SA_TIME).date()

# 2. Opskrif & Styl
st.markdown("<style>[data-testid='stHeader'] {display: none;} .block-container {padding:0 !important;} div.stButton > button {background-color: #800000 !important; color: white !important; border-radius: 10px; border: none; width: 100%; font-weight: bold; height: 3em;}</style>", unsafe_allow_html=True)
st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", use_container_width=True)
st.markdown("<div style='background:#008080; color:white; text-align:center; padding:15px; font-size:1.4rem; font-weight:700; border-bottom: 5px solid #800000;'>Laerskool Midstream College Primary Event Hub</div>", unsafe_allow_html=True)

# 3. Filter Seksie
with st.container():
    st.markdown("<div style='background:white; padding:20px; border-radius:0 0 20px 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);'>", unsafe_allow_html=True)
    search_q = st.text_input("🔍 Search:", placeholder="Type here...").lower().strip()
    col1, col2 = st.columns(2)
    with col1:
        cat_f = st.selectbox("Category:", ["All", "Sport", "Culture", "Academics"])
    with col2:
        act_opts = sorted(df_raw.iloc[:, 3].dropna().unique().tolist()) if not df_raw.empty else []
        act_f = st.multiselect("Activities:", act_opts)
    if st.button("🔄 REFRESH DATA"):
        st.cache_data.clear()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# 4. Kaartjie Vertoning
if df_raw.empty:
    st.info("No data found in the Upcoming sheet.")
else:
    df = df_raw.copy()
    if 'dt_fixed' in df.columns:
        df = df.sort_values('dt_fixed', ascending=True)
    if cat_f != "All":
        df = df[df.iloc[:, 2] == cat_f]
    if act_f:
        df = df[df.iloc[:, 3].isin(act_f)]
    if search_q:
        df = df[df.apply(lambda r: search_q in " ".join(str(v) for v in r.values).lower(), axis=1)]

    if df.empty:
        st.write("No upcoming events found.")
    else:
        card_style = """<style>body { background:#008080; font-family:sans-serif; padding:15px; } .card { background:white; padding:20px; border-radius:15px; border-left:10px solid #800000; margin-bottom:15px; box-shadow:0 4px 8px rgba(0,0,0,0.1); } .card-title { color:#800000; font-size:1.25rem; font-weight:bold; margin-top:0; } .btn { background:#800000 !important; color:white !important; padding:8px 12px; border-radius:8px; text-decoration:none; font-size:0.75rem; display:inline-block; margin-right:5px; margin-top:10px; font-weight:bold; }</style>"""
        h = card_style
        for _, r in df.iterrows():
            sport_h = str(r.iloc[3]).strip()
            age_l = str(r.iloc[4]).strip()
            raw_dt = str(r.iloc[5]).strip()
            ven_r = str(r.iloc[6]).strip()
            display_date = r['dt_fixed'].strftime('%d %B %Y') if pd.notnull(r['dt_fixed']) else raw_dt
            btns = ""
            for i in [7, 8]:
                if i < len(r):
                    val = str(r.iloc[i])
                    if "https://" in val:
                        lbl = "PROGRAMME" if i == 7 else "TEAM LIST"
                        btns += f"<a href='{fix_drive_link(val)}' target='_blank' class='btn'>{lbl}</a> "
            extra = ""
            if len(r) > 10:
                info_val = str(r.iloc[10])
                if info_val.lower() != 'nan' and info_val.strip() != "":
                    extra = f"<div style='font-size:0.85rem; margin-top:10px; color:#333; border-top:1px solid #eee; padding-top:8px;'><b>Note:</b> {info_val}</div>"
            h += f"<div class='card'><div class='card-title'>{sport_h} {age_l}</div><div style='font-size:0.95rem; color:#008080;'>📅 {display_date}</div><div style='font-size:0.95rem; color:#444;'>📍 {ven_r}</div>{btns}{extra}</div>"
        components.html(h, height=2500, scrolling=True)

st.markdown("<div style='background:#800000; color:white; text-align:center; padding:15px; font-size:0.8rem;'>Laerskool Midstream College Primary · Event Hub 2026</div>", unsafe_allow_html=True)
