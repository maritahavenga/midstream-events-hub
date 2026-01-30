import streamlit as st
import pandas as pd
import requests, io

# 1. Page Config
st.set_page_config(page_title="LMCP Event Hub", layout="centered")

# 2. Styling - DIT MOET BO-AAN STAAN SODAT DIT ALTYD LAAI
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #f8f9fa; }
    .nav-bar {
        background: linear-gradient(135deg, #800000 0%, #a00000 100%);
        color: white; padding: 25px; text-align: center;
        border-radius: 0 0 20px 20px; margin-top: -60px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    .card {
        background: white; padding: 20px; border-radius: 15px;
        border-left: 10px solid #800000; margin-top: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .tag-cat { background: #800000; color: white; padding: 3px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: bold; }
    .event-title { color: #333; font-size: 1.3rem; font-weight: 700; margin: 5px 0; }
    </style>
    """, unsafe_allow_html=True)

# ONS WYS DIE NAV BAR EERSTE (Sodat jy weet die app werk)
st.markdown('<div class="nav-bar"><h1>MIDSTREAM COLLEGE</h1><p>PRIMARY EVENT HUB</p></div>', unsafe_allow_html=True)

# 3. Data Connection - BINNE 'N TRY-EXCEPT SODAT DIT NIE DIE APP BREEK NIE
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?output=csv"

@st.cache_data(ttl=5)
def load_data():
    try:
        r = requests.get(URL, timeout=10)
        if r.status_code == 200:
            return pd.read_csv(io.StringIO(r.content.decode('utf-8')), dtype=str).fillna("")
    except:
        return None
    return None

df = load_data()

# 4. Wys filters en data slegs as die data gelaai is
if df is not None:
    st.write("")
    
    # 4 Filters
    all_cats = sorted([c for c in df.iloc[:, 1].unique() if len(str(c)) > 1])
    selected_cats = st.multiselect("1. Category:", all_cats)
    
    # Age Options
    age_options = ["U7 (Gr 1)", "U8 (Gr 2)", "U9 (Gr 3)", "U10 (Gr 4)", "U11 (Gr 5)", "U12 (Gr 6)", "U13 (Gr 7)"]
    selected_ages = st.multiselect("2. Age Group / Grade:", age_options)
    
    # Simple list search
    search = st.text_input("3. Search venue or team:")

    # Display loop
    for i in range(len(df)):
        row = df.iloc[i]
        cat, act, age, date, ven, lnk = row.iloc[1], row.iloc[2], row.iloc[3], row.iloc[5], row.iloc[6], row.iloc[7]
        
        # Slegs vir toets: Wys alles as geen filters gekies is nie
        if (not selected_cats or cat in selected_cats) and (not search or search.lower() in act.lower()):
            st.markdown(f"""
                <div class="card">
                    <span class="tag-cat">{cat}</span>
                    <div class="event-title">{age}</div>
                    <div style="color:#555;"><b>{date}</b> | {ven}</div>
                </div>
                """, unsafe_allow_html=True)
else:
    st.warning("⚠️ Still waiting for Google to wake up. Please wait 10 seconds and Refresh.")
    if st.button("🔄 Refresh Connection"):
        st.cache_data.clear()
        st.rerun()
Waarom hierdie kode?
