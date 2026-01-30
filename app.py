import streamlit as st
import pandas as pd
import requests, io

st.set_page_config(page_title="LMCP Event Hub", layout="centered")

# --- CSS ---
st.markdown("""
    <style>
    .nav-bar { background: linear-gradient(135deg, #800000 0%, #a00000 100%); color: white; padding: 25px; text-align: center; border-radius: 0 0 20px 20px; margin-top: -60px; }
    .card { background: white; padding: 20px; border-radius: 15px; border-left: 10px solid #800000; margin-top: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    .tag-cat { background: #800000; color: white; padding: 3px 10px; border-radius: 6px; font-size: 0.7rem; font-weight: bold; }
    .map-btn { display: inline-block; background-color: white; color: #008080 !important; padding: 8px 16px; border-radius: 8px; text-decoration: none; font-weight: bold; border: 1px solid #008080; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="nav-bar"><h1>MIDSTREAM COLLEGE</h1><p>PRIMARY EVENT HUB</p></div>', unsafe_allow_html=True)

# JOU SKAKEL
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

@st.cache_data(ttl=2) # Baie kort tydjie vir toetsing
def load_data():
    try:
        r = requests.get(f"{URL}&cb={pd.Timestamp.now().timestamp()}", timeout=15)
        if r.status_code != 200:
            return f"Error: Google returned status {r.status_code}"
        df = pd.read_csv(io.StringIO(r.content.decode('utf-8'))).fillna("")
        return df
    except Exception as e:
        return f"Error: {str(e)}"

data = load_data()

if isinstance(data, str):
    st.error(data)
elif data is not None and not data.empty:
    # FILTERS
    try:
        cat_col = data.columns[0]
        all_cats = sorted(data[cat_col].unique().astype(str))
        sel_cats = st.multiselect("Select Category:", all_cats)

        for _, row in data.iterrows():
            # Gebruik kolom posisies
            c, a, t, d, v, l = str(row.iloc[0]), str(row.iloc[1]), str(row.iloc[2]), str(row.iloc[3]), str(row.iloc[4]), str(row.iloc[5])
            
            if not sel_cats or c in sel_cats:
                st.markdown(f"""
                    <div class="card">
                        <span class="tag-cat">{c}</span>
                        <div style="color:#008080; font-weight:bold; margin-top:5px;">{a}</div>
                        <div style="font-size:1.2rem; font-weight:700;">{t}</div>
                        <div style="color:#555;">📅 {d} | 📍 {v}</div>
                        {f'<a href="{l}" target="_blank" class="map-btn">📂 VIEW</a>' if 'http' in l else ''}
                    </div>
                """, unsafe_allow_html=True)
    except:
        st.write("I see the file, but it looks different than expected. Columns found:", data.columns.tolist())
else:
    st.warning("Google Sheet is connected, but the 'Upcoming' tab looks empty. Did you add data and Publish?")

if st.button("Refresh"):
    st.cache_data.clear()
    st.rerun()
