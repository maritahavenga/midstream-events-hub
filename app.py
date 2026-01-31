import streamlit as st
import pandas as pd
import requests, io, time

st.set_page_config(page_title="LMCP Event Hub", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .nav-bar { background: linear-gradient(135deg, #800000 0%, #a00000 100%); color: white; padding: 25px; text-align: center; border-radius: 0 0 20px 20px; margin-top: -60px; }
    .card { background: white; padding: 20px; border-radius: 15px; border-left: 10px solid #800000; margin-top: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    .tag-cat { background: #800000; color: white; padding: 3px 10px; border-radius: 6px; font-size: 0.7rem; font-weight: bold; text-transform: uppercase; }
    .event-title { color: #222; font-size: 1.2rem; font-weight: 700; margin: 5px 0; }
    .info-box { background: #f1f3f5; padding: 10px; border-radius: 8px; font-size: 0.85rem; color: #444; margin: 10px 0; border-left: 3px solid #008080; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="nav-bar"><h1>MIDSTREAM COLLEGE</h1><p>PRIMARY EVENT HUB</p></div>', unsafe_allow_html=True)

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

@st.cache_data(ttl=60) # Die app gaan nou net een keer per minuut Google pla
def load_data():
    try:
        # Ons voeg 'n unieke nommer by die URL om Google te dwing om te kyk vir nuwe data
        r = requests.get(f"{URL}&refresh={int(time.time() / 60)}", timeout=10)
        if r.status_code == 200 and "html" not in r.text.lower():
            df = pd.read_csv(io.StringIO(r.text)).fillna("")
            return df
        return "WAIT"
    except:
        return None

data = load_data()

if isinstance(data, pd.DataFrame) and not data.empty:
    # FILTERS
    all_cats = sorted([str(x) for x in data.iloc[:, 0].unique() if str(x).strip()])
    sel_cats = st.multiselect("Kies Kategorie:", all_cats)
    
    for i in range(len(data)):
        row = data.iloc[i]
        # JOU KOLOMME: A=0, B=1, G=6, H=7, J=9
        cat, subj, team, date, ven, info, grade = str(row.iloc[0]), str(row.iloc[1]), str(row.iloc[6]), str(row.iloc[3]), str(row.iloc[4]), str(row.iloc[7]), str(row.iloc[9])
        
        if not sel_cats or cat in sel_cats:
            st.markdown(f"""
                <div class="card">
                    <span class="tag-cat">{cat}</span>
                    <div style="color:#008080; font-weight:bold; margin-top:5px;">{subj}</div>
                    <div class="event-title">{team if len(team) > 1 else subj}</div>
                    <div style="color:#555; font-size:0.9rem;">
                        <b>Grade {grade}</b> | 📅 {date} | 📍 {ven}
                    </div>
                    {f'<div class="info-box">ℹ️ {info}</div>' if len(info) > 2 else ''}
                </div>
            """, unsafe_allow_html=True)
elif data == "WAIT":
    st.info("🔄 Google verwerk tans die nuutste veranderinge... Die data behoort binne 'n minuut te verskyn.")
    time.sleep(2)
    st.rerun()
else:
    st.warning("Wagtend op data vanaf Google Sheets...")

if st.button("Dwing Verfris"):
    st.cache_data.clear()
    st.rerun()
