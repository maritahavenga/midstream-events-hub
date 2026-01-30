import streamlit as st
import pandas as pd
import requests
import io
import re
from datetime import datetime
import pytz
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

# 1. Konfigurasie
st.set_page_config(page_title="LMCP Digital Hub", layout="centered")
st_autorefresh(interval=120000, key="datarefresh")

EVENTS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

def clean_val(val):
    v = str(val).replace(".0", "").replace("nan", "").replace("NAN", "").strip()
    return "" if v.lower() in ["n/a", "none", ""] else v

def translate_term(text, activity_name=""):
    act_str = str(activity_name).strip()
    if re.search(r'(?i)\bEAT\b', act_str):
        text = text.replace(activity_name, "Afrikaans Eerste Addisionele Taal")
    elif re.search(r'(?i)\bHT\b', act_str):
        text = text.replace(activity_name, "Afrikaans Hooftaal")
    if any(k in act_str.lower() for k in ["afrikaans", "eat", "eerste addisionele taal", "hooftaal", "ht"]):
        return text
    translations = {"Saal": "Hall", "Ouditorium": "Auditorium", "Musiekkamer": "Music Room", "Swembad": "Pool", "Tennisbane": "Tennis Courts", "Netbalbane": "Netball Courts", "Muurbalbane": "Squash Courts", "Veld": "Field", "Koor": "Choir", "Astro": "Astro", "Atletiek": "Athletics", "Wiskunde": "Mathematics", "Wetenskap": "Science", "Geskiedenis": "History", "Geografie": "Geography"}
    for afrikaans, english in translations.items():
        text = re.sub(rf'\b{afrikaans}\b', english, text, flags=re.IGNORECASE)
    return text

@st.cache_data(ttl=1)
def load_data(url):
    try:
        r = requests.get(f"{url}&cb={datetime.now().timestamp()}", timeout=10)
        df = pd.read_csv(io.StringIO(r.content.decode('utf-8')))
        return df.fillna("")
    except: return pd.DataFrame()

st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", use_container_width=True)
df_raw = load_data(EVENTS_URL)

if not df_raw.empty:
    SA_TIME = pytz.timezone('Africa/Johannesburg')
    today = datetime.now(SA_TIME).date()

    # --- VOORBEREIDING VIR DYNAMIESE FILTERS ---
    # Trek slegs data wat nie in die verlede is nie
    df_active = df_raw.copy()
    df_active['dt_temp'] = pd.to_datetime(df_active.iloc[:, 5], errors='coerce')
    # Hou items wat vandag of later is, of wat "Full Term" is
    df_active = df_active[(df_active['dt_temp'].dt.date >= today) | (df_active.iloc[:, 12].str.contains("full term", case=False, na=False)) | (df_active.iloc[:, 5].isna())]

    with st.container():
        st.markdown("<div style='background:white; padding:20px; border-radius:12px; border:1px solid #eee; box-shadow:0 4px 12px rgba(0,0,0,0.05); margin-bottom:20px;'>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        
        # 1. Kategorie Filter
        with c1:
            sel_cat = st.multiselect("Category", ["Sport", "Culture", "Academics"], key="f_cat")
        
        # 2. Aktiwiteit Filter (Pas aan by Kategorie)
        with c2:
            if sel_cat:
                mask = df_active.iloc[:, 2].str.contains('|'.join(sel_cat), case=False, na=False)
                if "Academics" in sel_cat:
                    mask |= df_active.iloc[:, 2].str.contains("academic", case=False, na=False)
                filtered_act_list = sorted(list(set(df_active[mask].iloc[:, 3].str.strip())))
            else:
                filtered_act_list = sorted(list(set(df_active.iloc[:, 3].str.strip())))
