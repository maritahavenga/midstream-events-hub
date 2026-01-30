import streamlit as st
import pandas as pd
import requests, io

st.set_page_config(page_title="LMCP Event Hub", layout="centered")

st.markdown("""
    <style>
    @keyframes blinker { 50% { opacity: 0; } }
    .new-update { color: #ff0000; font-weight: bold; font-size: 0.85rem; animation: blinker 1s linear infinite; margin-bottom: 5px; display: block; }
    .stApp { background-color: #f8f9fa; }
    .nav-bar { background: linear-gradient(135deg, #800000 0%, #a00000 100%); color: white; padding: 25px; text-align: center; border-radius: 0 0 20px 20px; margin-top: -60px; }
    .card { background: white; padding: 20px; border-radius: 15px; border-left: 10px solid #800000; margin-top: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    .tag-cat { background: #800000; color: white; padding: 3px 10px; border-radius: 6px; font-size: 0.7rem; font-weight: bold; text-transform: uppercase; }
    .event-title { color: #222; font-size: 1.2rem; font-weight: 700; margin: 5px 0; }
    .info-box { background: #f1f3f5; padding: 10px; border-radius: 8px; font-size: 0.85rem; color: #444; margin: 10px 0; border-left: 3px solid #008080; white-space: pre-wrap; }
    .map-btn { display: inline-block; background-color: white; color: #008080 !important; padding: 8px 16px; border-radius: 8px; text-decoration: none; font-weight: bold; border: 1px solid #008080; margin-top: 5px; font-size: 0.8rem; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="nav-bar"><h1>MIDSTREAM COLLEGE</h1><p>PRIMARY EVENT HUB</p></div>', unsafe_allow_html=True)

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

@st.cache_data(ttl=1)
def load_data():
    try:
        r = requests.get(f"{URL}&cb={pd.Timestamp.now().timestamp()}", timeout=15)
        if r.status_code != 200: return None
        # Ons vul leë kategorieë aan en hanteer alle data as teks
        df = pd.read_csv(io.StringIO(r.content.decode('utf-8'))).fillna("")
        # Vul leë kategorieë afwaarts in (ffill) vir veiligheid
        df.iloc[:, 0] = df.iloc[:, 0].replace("", None).ffill().fillna("Algemeen")
        return df
    except:
        return None

df = load_data()

if df is not None and not df.empty:
    # FILTERS
    all_cats = sorted(df.iloc[:, 0].unique().astype(str))
    sel_cats = st.multiselect("Kies Kategorie:", all_cats)
    
    all_grades = sorted(df.iloc[:, 9].unique().astype(str))
    sel_grades = st.multiselect("Filter op Graad:", [g for g in all_grades if g.strip()])

    for i in range(len(df)):
        row = df.iloc[i]
        
        # JOU KOLOMME: A=0, B=1, C=2, D=3, E=4, F=5, G=6, H=7, J=9, K=10
        cat   = str(row.iloc[0])
        subj  = str(row.iloc[1])
        asses = str(row.iloc[2])
        date  = str(row.iloc[3])
        ven   = str(row.iloc[4])
        lnk   = str(row.iloc[5])
        team  = str(row.iloc[6])
        info  = str(row.iloc[7])
        grade = str(row.iloc[9])
        dur   = str(row.iloc[10])

        display_title = team if len(team) > 1 else (asses if len(asses) > 1 else subj)
        is_new = "NEW" in display_title.upper() or "NEW" in str(info).upper()

        if (not sel_cats or cat in sel_cats) and (not sel_grades or grade in sel_grades):
            st.markdown(f"""
                <div class="card">
                    { '<span class="new-update">🚨 NEW UPDATE</span>' if is_new else '' }
                    <span class="tag-cat">{cat}</span>
                    <div style="color:#008080; font-weight:bold; margin-top:5px;">{subj}</div>
                    <div class="event-title">{display_title}</div>
                    <div style="color:#555; font-size:0.9rem;">
                        <b>Target: {grade}</b> | 📅 {date} | 📍 {ven}
