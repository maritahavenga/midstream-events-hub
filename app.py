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
    .event-title { color: #222; font-size: 1.2rem; font-weight: 700; margin: 8px 0; }
    .map-btn { display: inline-block; background-color: white; color: #008080 !important; padding: 8px 16px; border-radius: 8px; text-decoration: none; font-weight: bold; border: 1px solid #008080; margin-top: 10px; }
    .info-box { background: #f1f3f5; padding: 10px; border-radius: 8px; font-size: 0.85rem; color: #444; margin: 10px 0; border-left: 3px solid #008080; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="nav-bar"><h1>MIDSTREAM COLLEGE</h1><p>PRIMARY EVENT HUB</p></div>', unsafe_allow_html=True)

# Die werkende skakel
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

@st.cache_data(ttl=2)
def load_data():
    try:
        # Voeg 'n cache-buster by om vars data te dwing
        response = requests.get(f"{URL}&cb={pd.Timestamp.now().timestamp()}", timeout=15)
        # Lees sonder om headers te raai (header=None) en dwing dan die eerste ry as kolom-name
        raw_data = pd.read_csv(io.StringIO(response.content.decode('utf-8')), header=None)
        if len(raw_data) > 1:
            df = raw_data.copy()
            df.columns = df.iloc[0] # Stel ry 0 as kolomname
            df = df.drop(0).reset_index(drop=True).fillna("")
            return df
        return None
    except:
        return None

df = load_data()

if df is not None and not df.empty:
    # 1. Filters (Gebruik kolom-indekse om foute met name te vermy)
    try:
        # Kolom A is 0, Kolom J is 9
        all_cats = sorted([str(x) for x in df.iloc[:, 0].unique() if str(x).strip()])
        sel_cats = st.multiselect("Select Category:", all_cats)

        all_ages = sorted([str(x) for x in df.iloc[:, 9].unique() if str(x).strip()])
        sel_ages = st.multiselect("Filter by Grade:", all_ages)

        # 2. Display Loop
        for _, row in df.iterrows():
            cat = str(row.iloc[0])   # A: Category
            act = str(row.iloc[1])   # B: Activity
            team = str(row.iloc[2])  # C: Team
            date = str(row.iloc[3])  # D: Date
            ven = str(row.iloc[4])   # E: Venue
            lnk = str(row.iloc[5])   # F: Link
            info = str(row.iloc[8])  # I: Information
            age = str(row.iloc[9])   # J: Age Group

            # Pas filters toe
            if (not sel_cats or cat in sel_cats) and (not sel_ages or age in sel_ages):
                st.markdown(f"""
                    <div class="card">
                        <span class="tag-cat">{cat}</span>
                        <div style="color:#008080; font-weight:bold; margin-top:5px;">{act}</div>
                        <div class="event-title">{team}</div>
                        <div style="color:#555;">
                            <b>Gr {age}</b> | 📅 {date} | 📍 {ven}
                        </div>
                        {f'<div class="info-box">ℹ️ {info}</div>' if info and len(info) > 2 else ''}
                        {f'<a href="{lnk}" target="_blank" class="map-btn">📂 VIEW DOCUMENT</a>' if 'http' in lnk else ''}
                    </div>
                """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Data error: {e}")
else:
    st.info("🔄 Verfris tans... Maak seker daar is data in jou 'Upcoming' tab en dat dit 'Published' is.")

if st.button("Refresh Hub"):
    st.cache_data.clear()
    st.rerun()
