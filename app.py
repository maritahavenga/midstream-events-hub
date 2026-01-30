import streamlit as st
import pandas as pd
import requests, io

st.set_page_config(page_title="LMCP Event Hub", layout="centered")

# --- UI STYLING ---
st.markdown("""
    <style>
    .nav-bar { background: linear-gradient(135deg, #800000 0%, #a00000 100%); color: white; padding: 25px; text-align: center; border-radius: 0 0 20px 20px; margin-top: -60px; }
    .card { background: white; padding: 20px; border-radius: 15px; border-left: 10px solid #800000; margin-top: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    .whole-term-card { border-left: 10px solid #FFD700 !important; background-color: #fffdf0 !important; }
    .tag-cat { background: #800000; color: white; padding: 3px 10px; border-radius: 6px; font-size: 0.7rem; font-weight: bold; text-transform: uppercase; }
    .event-title { color: #222; font-size: 1.2rem; font-weight: 700; margin: 8px 0; }
    .map-btn { display: inline-block; background-color: white; color: #008080 !important; padding: 8px 16px; border-radius: 8px; text-decoration: none; font-weight: bold; border: 1px solid #008080; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="nav-bar"><h1>MIDSTREAM COLLEGE</h1><p>PRIMARY EVENT HUB</p></div>', unsafe_allow_html=True)

# JOU NUWE SPESIFIEKE SKAKEL
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

@st.cache_data(ttl=5)
def load_data():
    try:
        r = requests.get(f"{URL}&cb={pd.Timestamp.now().timestamp()}", timeout=15)
        df = pd.read_csv(io.StringIO(r.content.decode('utf-8'))).fillna("")
        return df
    except Exception as e:
        return None

df = load_data()

if df is not None and len(df) > 0:
    # 1. Filters (Gebaseer op jou Upcoming Tab kolomme)
    all_cats = sorted(df.iloc[:, 0].unique().astype(str))
    sel_cats = st.multiselect("Select Category:", all_cats)

    # Sorteer dat "Whole Term" altyd eerste kom
    df['is_whole'] = df.apply(lambda x: 1 if "whole term" in str(x).lower() else 0, axis=1)
    df = df.sort_values(by=['is_whole'], ascending=False)

    # DISPLAY
    count = 0
    for i in range(len(df)):
        row = df.iloc[i]
        cat, act, team, date, venue, link = row.iloc[0], row.iloc[1], row.iloc[2], row.iloc[3], row.iloc[4], row.iloc[5]
        age = str(row.iloc[9]) if len(row) > 9 else ""

        if not sel_cats or cat in sel_cats:
            count += 1
            is_whole = "whole term" in str(team).lower() or "whole term" in str(act).lower()
            card_class = "card whole-term-card" if is_whole else "card"
            
            st.markdown(f"""
                <div class="{card_class}">
                    <span class="tag-cat">{cat}</span>
                    <div style="color:#008080; font-weight:bold; margin-top:5px;">{act}</div>
                    <div class="event-title">{"📌 " if is_whole else ""}{team}</div>
                    <div style="color:#555;">
                        📅 <b>{date}</b> | 📍 {venue}<br>
                        <small>Target: {age}</small>
                    </div>
                    {f'<a href="{link}" target="_blank" class="map-btn">📂 VIEW DOCUMENT / MAP</a>' if 'http' in str(link) else ''}
                </div>
            """, unsafe_allow_html=True)
else:
    st.warning("No events found. If there is data in your Sheet, wait a few seconds and Refresh.")

if st.button("Refresh Hub"):
    st.cache_data.clear()
    st.rerun()
