import streamlit as st
import pandas as pd
import requests, io

st.set_page_config(page_title="LMCP Event Hub", layout="centered")

# --- UI STYLING ---
st.markdown("""
    <style>
    .nav-bar { background: linear-gradient(135deg, #800000 0%, #a00000 100%); color: white; padding: 25px; text-align: center; border-radius: 0 0 20px 20px; margin-top: -60px; }
    .card { background: white; padding: 20px; border-radius: 15px; border-left: 10px solid #800000; margin-top: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.06); }
    .tag-cat { background: #800000; color: white; padding: 3px 10px; border-radius: 6px; font-size: 0.7rem; font-weight: bold; text-transform: uppercase; }
    .event-title { color: #222; font-size: 1.25rem; font-weight: 700; margin: 8px 0; }
    .map-btn { display: inline-block; background-color: white; color: #008080 !important; padding: 8px 16px; border-radius: 8px; text-decoration: none; font-weight: bold; border: 1px solid #008080; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="nav-bar"><h1>MIDSTREAM COLLEGE</h1><p>PRIMARY EVENT HUB</p></div>', unsafe_allow_html=True)

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?output=csv"

@st.cache_data(ttl=5)
def load_data():
    try:
        r = requests.get(f"{URL}&cb={pd.Timestamp.now().timestamp()}", timeout=10)
        df = pd.read_csv(io.StringIO(r.content.decode('utf-8'))).fillna("")
        return df
    except: return None

df = load_data()

if df is not None and not df.empty:
    # 1. Category Filter (Kolom A = Index 0)
    all_cats = sorted([str(c) for c in df.iloc[:, 0].unique() if len(str(c)) > 1])
    sel_cats = st.multiselect("1. Category:", all_cats)

    # 2. Age Group Filter (Kolom L = Index 9 in jou 11-kolom lys)
    age_options = ["U7 (Gr 1)", "U8 (Gr 2)", "U9 (Gr 3)", "U10 (Gr 4)", "U11 (Gr 5)", "U12 (Gr 6)", "U13 (Gr 7)"]
    sel_ages = st.multiselect("2. Age Group / Grade:", age_options)

    # DISPLAY
    count = 0
    for i in range(len(df)):
        row = df.iloc[i]
        
        # Mapping gebaseer op jou Upcoming Tab (A tot K)
        cat = str(row.iloc[0])   # A: Category
        act = str(row.iloc[1])   # B: Activity
        team = str(row.iloc[2])  # C: Team / Assessment
        date = str(row.iloc[3])  # D: Date
        ven = str(row.iloc[4])   # E: Venue
        lnk = str(row.iloc[5])   # F: Link
        age_info = str(row.iloc[9]) if len(row) > 9 else ""

        # Filter Logika
        m_cat = not sel_cats or cat in sel_cats
        m_age = not sel_ages or any(k.split(" ")[0].upper() in (str(age_info) + str(team)).upper() for k in sel_ages)

        if m_cat and m_age:
            count += 1
            st.markdown(f"""
                <div class="card">
                    <span class="tag-cat">{cat}</span>
                    <div style="color:#008080; font-weight:bold; margin-top:5px;">{act}</div>
                    <div class="event-title">{team}</div>
                    <div style="color:#555;">
                        📅 <b>{date}</b> | 📍 {ven}<br>
                        <small>Target: {age_info}</small>
                    </div>
                    {f'<a href="{lnk}" target="_blank" class="map-btn">📂 VIEW</a>' if 'http' in str(lnk) else ''}
                </div>
            """, unsafe_allow_html=True)
else:
    st.error("No data found. Please check your Google Sheet.")

if st.button("Refresh Hub"):
    st.cache_data.clear()
    st.rerun()
