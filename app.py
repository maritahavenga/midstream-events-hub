import streamlit as st
import pandas as pd
import requests, io

st.set_page_config(page_title="LMCP Event Hub", layout="centered")

# --- UI STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .nav-bar { background: linear-gradient(135deg, #800000 0%, #a00000 100%); color: white; padding: 25px; text-align: center; border-radius: 0 0 20px 20px; margin-top: -60px; }
    .card { background: white; padding: 20px; border-radius: 15px; border-left: 10px solid #800000; margin-top: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    .tag-cat { background: #800000; color: white; padding: 3px 10px; border-radius: 6px; font-size: 0.7rem; font-weight: bold; text-transform: uppercase; }
    .event-title { color: #222; font-size: 1.2rem; font-weight: 700; margin: 5px 0; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="nav-bar"><h1>MIDSTREAM COLLEGE</h1><p>PRIMARY EVENT HUB</p></div>', unsafe_allow_html=True)

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

@st.cache_data(ttl=1)
def load_data():
    try:
        r = requests.get(f"{URL}&cb={pd.Timestamp.now().timestamp()}", timeout=15)
        # header=None dwing hom om alles, insluitend ry 1, as data te sien
        df = pd.read_csv(io.StringIO(r.content.decode('utf-8')), header=None).fillna("")
        return df
    except:
        return None

df = load_data()

if df is not None and len(df) > 0:
    # As die eerste ry die opskrifte is (Category, ens.), skip ons hom
    start_row = 1 if "Category" in str(df.iloc[0,0]) else 0
    
    # Wys data vanaf die regte ry
    for i in range(start_row, len(df)):
        row = df.iloc[i]
        cat   = str(row[0])  # Kolom A
        subj  = str(row[1])  # Kolom B
        asses = str(row[2])  # Kolom C
        date  = str(row[3])  # Kolom D
        ven   = str(row[4])  # Kolom E
        lnk   = str(row[5])  # Kolom F
        team  = str(row[6])  # Kolom G
        info  = str(row[7])  # Kolom H
        grade = str(row[9])  # Kolom J
        
        # Wys net as die ry nie heeltemal leeg is nie
        if len(cat) > 1:
            st.markdown(f"""
                <div class="card">
                    <span class="tag-cat">{cat}</span>
                    <div style="color:#008080; font-weight:bold; margin-top:5px;">{subj}</div>
                    <div class="event-title">{team if len(team) > 1 else asses}</div>
                    <div style="color:#555; font-size:0.9rem;">
                        <b>Graad {grade}</b> | 📅 {date} | 📍 {ven}
                    </div>
                    {f'<div style="background:#f1f3f5; padding:8px; border-radius:5px; margin-top:10px; font-size:0.85rem;">ℹ️ {info}</div>' if len(info) > 2 else ''}
                </div>
            """, unsafe_allow_html=True)
            if "http" in str(lnk):
                st.link_button("📂 OOP DOKUMENT", str(lnk))
else:
    st.warning("⚠️ Geen data gevind nie. Maak seker jou formule in Google Sheets wys data op die 'Upcoming' blad.")

if st.button("Herlaai"):
    st.cache_data.clear()
    st.rerun()
