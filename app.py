import streamlit as st
import pandas as pd
import requests, io

st.set_page_config(page_title="LMCP Event Hub", layout="centered")

st.markdown("""
    <style>
    .nav-bar { background: linear-gradient(135deg, #800000 0%, #a00000 100%); color: white; padding: 25px; text-align: center; border-radius: 0 0 20px 20px; margin-top: -60px; }
    .card { background: white; padding: 20px; border-radius: 15px; border-left: 10px solid #800000; margin-top: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    .tag-cat { background: #800000; color: white; padding: 3px 10px; border-radius: 6px; font-size: 0.7rem; font-weight: bold; }
    .event-title { color: #222; font-size: 1.25rem; font-weight: 700; margin: 8px 0; }
    .map-btn { display: inline-block; background-color: white; color: #008080 !important; padding: 8px 16px; border-radius: 8px; text-decoration: none; font-weight: bold; border: 1px solid #008080; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="nav-bar"><h1>MIDSTREAM COLLEGE</h1><p>PRIMARY EVENT HUB</p></div>', unsafe_allow_html=True)

# Gebruik jou spesifieke CSV skakel
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?output=csv"

@st.cache_data(ttl=5)
def load_data():
    try:
        # Ons voeg 'n vars tydstempel by om Google se cache te omseil
        r = requests.get(f"{URL}&cb={pd.Timestamp.now().timestamp()}", timeout=15)
        # Lees rou data - moenie eers probeer om headers te raai nie
        df = pd.read_csv(io.StringIO(r.content.decode('utf-8')), header=0)
        return df
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return None

df = load_data()

if df is not None and len(df) > 0:
    # 1. Filters (Gebruik kolom-indekse om foute te vermy)
    # Ons neem kolom 0 vir Category
    all_cats = sorted(df.iloc[:, 0].unique().astype(str))
    sel_cats = st.multiselect("Select Category:", all_cats)

    # DISPLAY LOOP
    count = 0
    for i in range(len(df)):
        row = df.iloc[i]
        
        cat = str(row.iloc[0])   # A
        act = str(row.iloc[1])   # B
        team = str(row.iloc[2])  # C
        date = str(row.iloc[3])  # D
        ven = str(row.iloc[4])   # E
        lnk = str(row.iloc[5])   # F
        # As Age Group in Kolom J is (nommer 9)
        age = str(row.iloc[9]) if len(row) > 9 else ""

        if not sel_cats or cat in sel_cats:
            count += 1
            st.markdown(f"""
                <div class="card">
                    <span class="tag-cat">{cat}</span>
                    <div style="color:#008080; font-weight:bold; margin-top:5px;">{act}</div>
                    <div class="event-title">{team}</div>
                    <div style="color:#555;">
                        📅 <b>{date}</b> | 📍 {ven}<br>
                        <small>Target: {age}</small>
                    </div>
                    {f'<a href="{lnk}" target="_blank" class="map-btn">📂 VIEW</a>' if 'http' in str(lnk) else ''}
                </div>
            """, unsafe_allow_html=True)
    
    if count == 0:
        st.info("No events found for this category.")
else:
    st.warning("⚠️ Google Sheet is returning an empty file. Go to File > Share > Publish to Web and make sure the 'Upcoming' tab is selected as CSV.")

if st.button("Refresh Hub"):
    st.cache_data.clear()
    st.rerun()
