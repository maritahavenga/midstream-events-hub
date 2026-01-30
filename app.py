import streamlit as st
import pandas as pd
import requests, io

st.set_page_config(page_title="LMCP Event Hub", layout="centered")

# --- UI STYLING ---
st.markdown("""
    <style>
    .nav-bar { background: linear-gradient(135deg, #800000 0%, #a00000 100%); color: white; padding: 25px; text-align: center; border-radius: 0 0 20px 20px; margin-top: -60px; }
    .card { background: white; padding: 20px; border-radius: 15px; border-left: 10px solid #800000; margin-top: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    .tag-cat { background: #800000; color: white; padding: 3px 10px; border-radius: 6px; font-size: 0.7rem; font-weight: bold; text-transform: uppercase; }
    .event-title { color: #222; font-size: 1.25rem; font-weight: 700; margin: 8px 0; }
    .map-btn { display: inline-block; background-color: white; color: #008080 !important; padding: 8px 16px; border-radius: 8px; text-decoration: none; font-weight: bold; border: 1px solid #008080; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="nav-bar"><h1>MIDSTREAM COLLEGE</h1><p>PRIMARY EVENT HUB</p></div>', unsafe_allow_html=True)

# JOU NUWE WERKENDE SKAKEL
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

@st.cache_data(ttl=2)
def load_data():
    try:
        r = requests.get(f"{URL}&cb={pd.Timestamp.now().timestamp()}", timeout=15)
        if r.status_code == 200:
            return pd.read_csv(io.StringIO(r.content.decode('utf-8'))).fillna("")
        return None
    except:
        return None

df = load_data()

if df is not None and not df.empty:
    # 1. Filters
    all_cats = sorted([str(c) for c in df.iloc[:, 0].unique() if len(str(c)) > 1])
    sel_cats = st.multiselect("Select Category:", all_cats)

    # 2. Display Loop
    count = 0
    for i in range(len(df)):
        row = df.iloc[i]
        # Kolom mapping: A=0, B=1, C=2, D=3, E=4, F=5
        cat, act, team, date, venue, link = str(row.iloc[0]), str(row.iloc[1]), str(row.iloc[2]), str(row.iloc[3]), str(row.iloc[4]), str(row.iloc[5])
        
        if not sel_cats or cat in sel_cats:
            count += 1
            st.markdown(f"""
                <div class="card">
                    <span class="tag-cat">{cat}</span>
                    <div style="color:#008080; font-weight:bold; margin-top:5px;">{act}</div>
                    <div class="event-title">{team}</div>
                    <div style="color:#555;">📅 <b>{date}</b> | 📍 {venue}</div>
                    {f'<a href="{link}" target="_blank" class="map-btn">📂 VIEW</a>' if 'http' in link else ''}
                </div>
            """, unsafe_allow_html=True)
    
    if count == 0:
        st.info("No events found for this selection.")
else:
    st.warning("🔄 Connecting to the 'Upcoming' tab... If you see this for more than 10 seconds, refresh the page.")

if st.button("Refresh"):
    st.cache_data.clear()
    st.rerun()
