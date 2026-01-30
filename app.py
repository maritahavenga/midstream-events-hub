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

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

def clean_val(val):
    return str(val).replace(".0", "").replace("nan", "").replace("NAN", "").strip()

def translate_term(text, act_name=""):
    s = str(act_name).strip()
    if re.search(r'(?i)\bEAT\b', s): text = text.replace(act_name, "Afrikaans Eerste Addisionele Taal")
    elif re.search(r'(?i)\bHT\b', s): text = text.replace(act_name, "Afrikaans Hooftaal")
    if any(k in s.lower() for k in ["afrikaans", "eat", "ht"]): return text
    trans = {"Saal": "Hall", "Ouditorium": "Auditorium", "Veld": "Field", "Atletiek": "Athletics", "Wiskunde": "Mathematics", "Wetenskap": "Science"}
    for k, v in trans.items(): text = re.sub(rf'\b{k}\b', v, text, flags=re.IGNORECASE)
    return text

@st.cache_data(ttl=1)
def load_data():
    try:
        r = requests.get(f"{URL}&cb={datetime.now().timestamp()}", timeout=10)
        return pd.read_csv(io.StringIO(r.content.decode('utf-8'))).fillna("")
    except: return pd.DataFrame()

df_raw = load_data()

if not df_raw.empty:
    with st.container():
        st.markdown("<div style='background:white; padding:20px; border-radius:12px; border:1px solid #eee; margin-bottom:20px;'>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        
        # 1. Kategorie Filter
        with c1: 
            s_cat = st.multiselect("Category", ["Sport", "Culture", "Academics"])
        
        # 2. Aktiwiteit Filter (PAS AAN BY KATEGORIE)
        with c2:
            if s_cat:
                mask = df_raw.iloc[:, 2].str.contains('|'.join(s_cat), case=False, na=False)
                if "Academics" in s_cat: mask |= df_raw.iloc[:, 2].str.contains("academic", case=False, na=False)
                opts = sorted(list(set(df_raw[mask].iloc[:, 3].str.strip())))
            else:
                opts = sorted(list(set(df_raw.iloc[:, 3].str.strip())))
            s_act = st.multiselect("Activity / Subject", opts)
            
        # 3. Age Filter
        with c3:
            age_opts = ["Gr 1", "Gr 2", "Gr 3", "Gr 4", "Gr 5", "Gr 6", "Gr 7", "U7", "U8", "U9", "U10", "U11", "U12", "U13"]
            s_age = st.multiselect("Gr / Age Group", age_opts)
            
        sq = st.text_input("Search", placeholder="Search Subject, Grade or Detail...")
        if st.button("REFRESH HUB", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    today = datetime.now(pytz.timezone('Africa/Johannesburg')).date()
    t_nums = set()
    for s in s_age:
        ns = re.findall(r'\d+', s)
        if ns:
            n = int(ns[0])
            t_nums.add(n)
            if n >= 7: t_nums.add(n - 6)
            elif n <= 7: t_nums.add(n + 6)

    filtered_list = []
    for _, r in df_raw.iterrows():
        name, cat_row = str(r.iloc[3]), str(r.iloc[2]).lower()
        dt = pd.to_datetime(str(r.iloc[5]), dayfirst=True, errors='coerce')
        is_f = "full term" in str(r.iloc[12]).lower()
        
        if not is_f and pd.notnull(dt) and dt.date() < today: continue
        
        # Filtreer Logika
        if s_cat and not any(s.lower() in cat_row or (s=="Academics" and "academic" in cat_row) for s in s_cat): continue
        if s_act and name.strip() not in s_act: continue
        
        is_global = any(ws in name.lower() for ws in ["swimming", "athletics"])
        if t_nums and not is_global:
            v = clean_val(r.iloc[11])
            vn = re.findall(r'\d+', v)
            if not (vn and int(vn[0]) in t_nums): continue
            
        g_raw = clean_val(r.iloc[11])
        g_match = re.search(r'\d+', g_raw)
        g_val = int(g_match.group()) if g_match else 99
        if "U" in g_raw.upper() and g_val >= 7: g_val -= 6
        
        filtered_list.append({'r': r, 'd': dt if pd.notnull(dt) else datetime.max.replace(tzinfo=None), 's': name.lower(), 'g': g_val, 'f': is_f})

    filtered_list.sort(key=lambda x: (not x['f'], x['d'], x['s'], x['g']))
    
    h = "<style>body{font-family:'Inter',sans-serif;}.card{background:white;padding:20px;border-radius:15px;border-left:10px solid #800000;margin-bottom:18px;box-shadow:0 4px 15px rgba(0,0,0,0.05);}.card-title{color:#800000;font-size:1.1rem;font-weight:800;margin-bottom:10px;}.venue{color:#008080;font-weight:800;text-transform:uppercase;}.btn{background:#800000;color:white!important;padding:8px 12px;border-radius:8px;text-decoration:none;font-size:0.75rem;font-weight:700;display:inline-block;margin-right:5px;}</style>"
    
    for i in filtered_list:
        r, d, is_f = i['r'], i['d'], i['f']
        act_display = str(r.iloc[3])
        is_ac = "academic" in str(r.iloc[2]).lower() or any(x in act_display.lower() for x in ["afrikaans", "eat", "ht", "math", "science"])
        age = clean_val(r.iloc[11])
        pre = "Gr " if is_ac else "U"
        age_d = f"{prefix if 'prefix' in locals() else pre}{age} " if age and not (any(ws in act_display.lower() for ws in ["swimming", "athletics"]) and not row_age if 'row_age' in locals() else not age) else ""
        
        title = f"{translate_term(act_display, act_display)} {age_d}{translate_term(clean_val(r.iloc[4]), act_display)}".strip()
        if sq and sq.lower() not in title.lower(): continue
        
        d_s = "FULL TERM" if is_f else (d.strftime('%d %B %Y') if d != datetime.max.replace(tzinfo=None) else str(r.iloc[5]))
        b1, b2 = ("Document", "Assessment Details") if is_ac else ("Programme", "Team List")
        
        btns = ""
        if "http" in str(r.iloc[7]).lower(): btns += f"<a href='{r.iloc[7]}' target='_blank' class='btn'>{b1}</a>"
        if "http" in str(r.iloc[8]).lower(): btns += f"<a href='{r.iloc[8]}' target='_blank' class='btn'>{b2}</a>"
        
        n_raw = clean_val(r.iloc[10])
        note = f"<div style='background:#e7f3f3;padding:10px;margin-top:10px;border-radius:8px;font-size:0.8rem;'>NOTE: {n_raw}</div>" if n_raw and "http" not in n_raw.lower() else ""
        if "http" in n_raw.lower(): btns += f"<a href='{n_raw}' target='_blank' class='btn'>Info</a>"
        
        h += f"<div class='card'><div class='card-title'>{title}</div><div>📅 {d_s}</div><div class='venue'>📍 {translate_term(str(r.iloc[6]), act_display).upper()}</div>{note}<div style='margin-top:10px;'>{btns}</div>
