import streamlit as st
import pandas as pd
import requests, io

st.set_page_config(page_title="LMCP Event Hub", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .nav-bar { background: linear-gradient(135deg, #800000 0%, #a00000 100%); color: white; padding: 25px; text-align: center; border-radius: 0 0 20px 20px; margin-top: -60px; }
    .card { background: white; padding: 20px; border-radius: 15px; border-left: 10px solid #800000; margin-top: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    .tag-cat { background: #800000; color: white; padding: 3px 10px; border-radius: 6px; font-size: 0.7rem; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="nav-bar"><h1>MIDSTREAM COLLEGE</h1><p>PRIMARY EVENT HUB</p></div>', unsafe_allow_html=True)

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

@st.cache_data(ttl=1)
def load_data():
    try:
        # Dwing vars data vanaf Google
        r = requests.get(f"{URL}&timestamp={pd.Timestamp.now().timestamp()}", timeout=10)
        # Lees rou data sonder om te vra oor headers
        df = pd.read_csv(io.StringIO(r.content.decode('utf-8'))).fillna("")
        return df
    except:
        return None

df = load_data()

if df is not None and len(df) > 0:
    st.success(f"Gekoppel! {len(df)} items gevind.")
    
    # Wys boksies
    for i in range(len(df)):
        row = df.iloc[i]
        # Ons gebruik net die eerste paar kolomme om te toets
        st.markdown(f"""
            <div class="card">
                <span class="tag-cat">{row.iloc[0]}</span>
                <div style="font-weight:bold; color:#008080; margin-top:5px;">{row.iloc[1]}</div>
                <div style="font-size:1.2rem; font-weight:700;">{row.iloc[2]}</div>
                <div style="color:#555;">📅 {row.iloc[3]} | 📍 {row.iloc[4]}</div>
            </div>
        """, unsafe_allow_html=True)
else:
    st.info("🔄 Die bladsy is tans leeg. Sodra daar data in die 'Upcoming' tab verskyn, sal dit hier gewys word.")

if st.button("Verfris Nou"):
    st.cache_data.clear()
    st.rerun()
