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
    low_t = t.lower()
    # Vertalings & Korreksies
    corrections = {
        "reve": "Rugby", "rugbi": "Rugby", "atletik": "Athletics", "atletiek": "Athletics",
        "netbal": "Netball", "hokkie": "Hockey", "swem": "Swimming",
        "ouditorium": "Auditorium", "saal": "Hall", "veld": "Field", "astro": "Astro"
    }
    for typo, correct in corrections.items():
        if typo in low_t:
            t = correct
            break
    if is_category:
        if "acad" in low_t: return "Academics"
        if "sport" in low_t: return "Sport"
        if "cult" in low_t or "kult" in low_t: return "Culture"
    if is_group:
        nums = re.findall(r'\d+', t)
        if nums:
            age_num = nums[0]
            suffix = " Girls" if "girl" in low_t or "dogter" in low_t else (" Boys" if "boy" in low_t or "seun" in low_t else "")
            return f"U{age_num}{suffix}"
    return t.capitalize() if t.isupper() else t

@st.cache_data(ttl=5)
def load_data():
    try:
        r = requests.get(f"{URL}&cb={datetime.now().timestamp()}", timeout=10)
        df = pd.read_csv(io.StringIO(r.content.decode('utf-8')))
        if df.empty or len(df.columns) < 6: return pd.DataFrame()
        df.iloc[:, 2] = df.iloc[:, 2].apply(lambda x: clean_text(x, is_category=True))
        df.iloc[:, 3] = df.iloc[:, 3].apply(lambda x: clean_text(x))
        df.iloc[:, 4] = df.iloc[:, 4].apply(lambda x: clean_text(x, is_group=True))
        df['dt_fixed'] = pd.to_datetime(df.iloc[:, 5], dayfirst=True, errors='coerce')
        return df
    except: return pd.DataFrame()

df_raw = load_data()
SA_TIME = pytz.timezone('Africa/Johannesburg')
today = datetime.now(SA_TIME).date()

# 2. Styling (Midstream Kleure)
st.markdown("""<style>[data-testid="stHeader"] {display: none;} .block-container {padding:0 !important;} div.stButton > button {background-color: #800000 !important; color: white !important; border-radius: 10px; font-weight: bold; width: 100%; border:none;}</style>""", unsafe_allow_html=True)
st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", use_container_width=True)
st.markdown("<div style='background:#008080; color:white; text-align:center; padding:15px; font-size:1.4rem; font-weight:700; border-bottom: 5px solid #800000;'>Laerskool Midstream College Primary Event Hub</div>", unsafe_allow_html=True)

# 3. Filters
with st.container():
    st.markdown("<div style='background:white; padding:20px; border-radius:0 0 20px 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);'>", unsafe_allow_html=True)
    search_q = st.text_input("🔍 Search Events:", placeholder="Search activity, group or venue...").lower().strip()
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

# 4. Vertoon Kaartjies
if df_raw.empty:
    st.info("No data found.")
else:
    df = df_raw.copy()
    if 'dt_fixed' in df.columns:
        # POOF Logika: Wys alles vandag of later, of waar datum nie gelees kon word nie
        df = df[(df['dt_fixed'].dt.date >= today) | (df['dt_fixed'].isnull())]
        df = df.sort_values('dt_fixed', ascending=True, na_position='last')

    if cat_f != "All": df = df[df.iloc[:, 2] == cat_f]
    if act_f: df = df[df.iloc[:, 3].isin(act_f)]
    if search_q:
        df = df[df.apply(lambda r: search_q in " ".join(str(v) for v in r.values).lower(), axis=1)]

    if df.empty:
        st.write("<p style='text-align:center; padding:20px;'>No upcoming events found.</p>", unsafe_allow_html=True)
    else:
        # Hier is die "symbol fix" en skoner voorkoms
        h = """<style>
            body { background:#008080; font-family: sans-serif; padding:15px; } 
            .card { background:white; padding:20px; border-radius:15px; border-left:10px solid #800000; margin-bottom:15px; position:relative; box-shadow:0 4px 8px rgba(0,0,0,0.1); } 
            .card-title { color:#800000; font-size:1.25rem; font-weight:bold; margin-top:0; } 
            .btn { background:#800000 !important; color:white !important; padding:8px 12px; border-radius:8px; text-decoration:none; font-size:0.75rem; display:inline-block; margin-right:5px; margin-top:10px; font-weight:bold; } 
            .badge { position:absolute; top:15px; right:15px; background:#FFD700; color:#800000; padding:4px 8px; border-radius:5px; font-weight:bold; font-size:0.65rem; animation: blink 1.5s infinite; } 
            @keyframes blink { 0% {opacity: 1;} 50% {opacity: 0.3;} 100% {opacity: 1;} } 
            .map-link { color:#800000; text-decoration:underline; font-size:0.95rem; font-weight:600; }
            .date-row { font-size:0.95rem; color:#008080; margin: 5px 0; font-weight: 500; }
        </style>"""
        
        for _, r in df.iterrows():
            sport_h, age_l = str(r.iloc[3]), str(r.iloc[4])
            # Skoner datum sonder die "17" kalender emoji
            display_date = r['dt_fixed'].strftime('%d %B %Y') if pd.notnull(r['dt_fixed']) else str(r.iloc[5])
            
            ven_r = str(r.iloc[6])
            prog_url = fix_drive_link(str(r.iloc[7])) if len(r) > 7 and "https" in str(r.iloc[7]) else None
            
            # Venue vertaling
            ven_display = ven_r
            if "ouditorium" in ven_r.lower(): ven_display = "Auditorium"
            elif "veld" in ven_r.lower(): ven_display = "Field"
            elif "saal" in ven_r.lower(): ven_display = "Hall"

            if "see programme" in ven_r.lower() and prog_url:
                venue_html = f"📍 <a class='map-link' href='{prog_url}' target='_blank'>SEE PROGRAMME</a>"
            else:
                mq = f"Midstream+College+{ven_r.replace(' ', '+')}"
                maps_url = f"https://www.google.com/maps/search/?api=1&query={mq}"
                venue_html = f"📍 <a class='map-link' href='{maps_url}' target='_blank'>{ven_display.upper()}</a>"
            
            btns = ""
            for i in [7, 8, 10]:
                val = str(r.iloc[i]) if i < len(r) else ""
                if "https://" in val:
                    lbl = "PROGRAMME" if i == 7 else ("TEAM LIST" if i == 8 else "INFORMATION")
                    btns += f"<a href='{fix_drive_link(val)}' target='_blank' class='btn'>{lbl}</a> "
            
            badge, note = "", ""
            if len(r) > 10:
                info_text = str(r.iloc[10])
                if info_text.lower() != 'nan' and info_text.strip() != "":
                    if "$" in info_text: badge = "<div class='badge'>RECENT UPDATE</div>"
                    if "https://" not in info_text:
                        note = f"<div style='font-size:0.85rem; margin-top:10px; color:#333; border-top:1px solid #eee; padding-top:8px;'><b>Note:</b> {info_text.replace('$', '')}</div>"

            h += f"<div class='card'>{badge}<div class='card-title'>{sport_h} {age_l}</div><div class='date-row'>📅 {display_date}</div><div>{venue_html}</div>{btns}{note}</div>"
        
        components.html(h, height=2500, scrolling=True)

st.markdown("<div style='background:#800000; color:white; text-align:center; padding:15px; font-size:0.8rem;'>Laerskool Midstream College Primary · Event Hub 2026</div>", unsafe_allow_html=True)
