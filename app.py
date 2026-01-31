import streamlit as st
import pandas as pd
import requests
import io
import time

# Stel die bladsy op
st.set_page_config(page_title="LMCP Event Hub", layout="centered")

# --- STYLING (Midstream Kleure) ---
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .nav-bar { background: linear-gradient(135deg, #800000 0%, #a00000 100%); color: white; padding: 25px; text-align: center; border-radius: 0 0 20px 20px; margin-top: -60px; }
    .card { background: white; padding: 20px; border-radius: 15px; border-left: 10px solid #800000; margin-top: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    .tag-cat { background: #800000; color: white; padding: 3px 10px; border-radius: 6px; font-size: 0.7rem; font-weight: bold; text-transform: uppercase; }
    .event-title { color: #222; font-size: 1.2rem; font-weight: 700; margin: 5px 0; }
    .info-box { background: #f1f3f5; padding: 10px; border-radius: 8px; font-size: 0.85rem; color: #444; margin: 10px 0; border-left: 3px solid #008080; white-space: pre-wrap; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="nav-bar"><h1>MIDSTREAM COLLEGE</h1><p>PRIMARY EVENT HUB</p></div>', unsafe_allow_html=True)

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

# --- SMART LOADING SYSTEM ---
@st.cache_data(ttl=300) # Hou data vir 5 minute in geheue (baie stabiel vir ouers)
def fetch_data(url):
    try:
        # Voeg 'n cache-buster by
        csv_url = f"{url}&cb={int(time.time())}"
        response = requests.get(csv_url, timeout=5) # Gee Google net 5 sekondes
        if response.status_code == 200 and "html" not in response.text.lower():
            df = pd.read_csv(io.StringIO(response.text))
            return df.fillna("")
        return None
    except:
        return None

# Probeer data laai
df = fetch_data(URL)

if df is not None and not df.empty:
    # FILTERS (Gebruik name as hulle bestaan, anders indekse)
    try:
        categories = sorted(df.iloc[:, 0].unique())
        sel_cat = st.multiselect("Kies Kategorie:", categories)
        
        grades = sorted(df.iloc[:, 9].astype(str).unique())
        sel_grade = st.multiselect("Filter op Graad:", grades)

        for i in range(len(df)):
            row = df.iloc[i]
            
            # JOU KORREKTE MAPPING (A, B, G, H, J)
            cat, subj, team, date, ven = str(row.iloc[0]), str(row.iloc[1]), str(row.iloc[6]), str(row.iloc[3]), str(row.iloc[4])
            info, grade = str(row.iloc[7]), str(row.iloc[9])
            link = str(row.iloc[5])

            if (not sel_cat or cat in sel_cat) and (not sel_grade or grade in sel_grade):
                st.markdown(f"""
                    <div class="card">
                        <span class="tag-cat">{cat}</span>
                        <div style="color:#008080; font-weight:bold; margin-top:5px;">{subj}</div>
                        <div class="event-title">{team if len(team) > 1 else subj}</div>
                        <div style="color:#555; font-size:0.9rem;">
                            <b>Grade {grade}</b> | 📅 {date} | 📍 {ven}
                        </div>
                        {f'<div class="info-box">ℹ️ {info}</div>' if len(info) > 1 else ''}
                    </div>
                """, unsafe_allow_html=True)
                if "http" in link:
                    st.link_button("📂 OOP DOKUMENT", link)
    except Exception as e:
        st.error("Data-formaat fout. Kontroleer asseblief die kolomme in die Sheet.")
else:
    st.warning("🔄 Besig om data te verfris... As die boodskap bly staan, verfris asb die bladsy.")
    if st.button("Herlaai Nou"):
        st.cache_data.clear()
        st.rerun()

st.markdown("---")
st.caption("Laas opgedateer: " + time.strftime("%H:%M:%S"))
