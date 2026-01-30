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
    
    # Forceer formele Afrikaanse name
    if re.search(r'(?i)\bEAT\b', act_str):
        text = text.replace(activity_name, "Afrikaans Eerste Addisionele Taal")
    elif re.search(r'(?i)\bHT\b', act_str):
        text = text.replace(activity_name, "Afrikaans Hooftaal")
        
    if any(k in act_str.lower() for k in ["afrikaans", "eat", "eerste addisionele taal", "hooftaal", "ht"]):
        return text

    translations = {
        "Saal": "Hall", "Ouditorium": "Auditorium", "Musiekkamer": "Music Room",
        "Swembad": "Pool", "Tennisbane": "Tennis Courts", "Netbalbane": "Netball Courts",
        "Muurbalbane": "Squash Courts", "Veld": "Field", "Koor": "Choir", 
        "Astro": "Astro", "Atletiek": "Athletics", "Wiskunde": "Mathematics", 
        "Wetenskap": "Science", "Geskiedenis": "History", "Geografie": "Geography"
    }
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
    with st.container():
        st.markdown("<div style='background:white; padding:20px; border-radius:12px; border:1px solid #eee; box-shadow:0 4px 12px rgba(0,0,0,0.05); margin-bottom:20px;'>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            sel_cat = st.multiselect("Category", ["Sport", "Culture", "Academics"], key="f_cat")
        with c2:
            act_list = sorted(list(set([str(a).strip() for a in df_raw.iloc[:, 3] if a])))
            sel_act = st.multiselect("Activity / Subject", act_list, key="f_act")
        with c3:
            age_options = ["Gr 1", "Gr 2", "Gr 3", "Gr 4", "Gr 5", "Gr 6", "Gr 7", "U7", "U8", "U9", "U10", "U11", "U12", "U13"]
            sel_age = st.multiselect("Gr / Age Group", age_options, key="f_age")
        
        search_q = st.text_input("Search", placeholder="Search Subject, Grade or Detail...")
        if st.button("REFRESH HUB", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    SA_TIME = pytz.timezone('Africa/Johannesburg')
    today = datetime.now(SA_TIME).date()
    
    mapping = {"Gr 1":["1","U7","Gr 1"], "U7":["1","U7","Gr 1"], "Gr 2":["2","U8","Gr 2"], "U8":["2","U8","Gr 2"], "Gr 3":["3","U9","Gr 3"], "U9":["3","U9","Gr 3"], "Gr 4":["4","U10","Gr 4"], "U10":["4","U10","Gr 4"], "Gr 5":["5","U11","Gr 5"], "U11":["5","U11","Gr 5"], "Gr 6":["6","U12","Gr 6"], "U12":["6","U12","Gr 6"], "Gr 7":["7","U13","Gr 7"], "U13":["7","U13","Gr 7"]}
    expanded_sel_age = set(sel_age)
    for s in sel_age:
        if s in mapping: expanded_sel_age.update(mapping[s])

    df_filtered = []
    for _, r in df_raw.iterrows():
        dt_val = pd.to_datetime(str(r.iloc[5]), errors='coerce')
        if pd.isnull(dt_val):
            dt_val = pd.to_datetime(str(r.iloc
