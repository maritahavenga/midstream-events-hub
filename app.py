import streamlit as st
import pandas as pd
import requests, io
import time

st.set_page_config(page_title="LMCP Event Hub", layout="centered")

# --- UI STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .nav-bar { background: linear-gradient(135deg, #800000 0%, #a00000 100%); color: white; padding: 25px; text-align: center; border-radius: 0 0 20px 20px; margin-top: -60px; }
    .card { background: white; padding: 20px; border-radius: 15px; border-left: 10px solid #800000; margin-top: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    .tag-cat { background: #800000; color: white; padding: 3px 10px; border-radius: 6px; font-size: 0.7rem; font-weight: bold; text-transform: uppercase; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="nav-bar"><h1>MIDSTREAM COLLEGE</h1><p>EVENT HUB DEBUG MODE</p></div>', unsafe_allow_html=True)

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

# GEEN CACHE NIE - ons dwing hom om elke keer vars te lees
def load_data_debug():
    try:
        # Ons gebruik 'n unieke nommer (timestamp) sodat Google nie 'n ou weergawe stuur nie
        response = requests.get(f"{URL}&nocache={time.time()}", timeout=10)
        content = response.content.decode('utf-8')
        
        # Wys vir ons op die skerm wat hy kry (net vir nou)
        if len(content) < 50:
            st.error(f"Google stuur amper niks nie: {content}")
            return None
            
        df = pd.read_csv(io.StringIO(content)).fillna("")
        return df
    except Exception as e:
        st.error(f"Fout met konneksie: {e}")
        return None

df = load_data_debug()

if df is not None and not df.empty:
    st.success(f"Sukses! Ek sien {len(df)} events.")
    
    # KATEGORIE FILTER
    all_cats = sorted([str(x) for x in df.iloc[:, 0].unique() if str(x).strip()])
    sel_cats = st.multiselect("Select Category:", all_cats)

    for i in range(len(df)):
        row = df.iloc[i]
        cat, subj, team, date, ven = str(row.iloc[0]), str(row.iloc[1]), str(row.iloc[2]), str(row.iloc[3]), str(row.iloc[4])
        info, grade = str(row.iloc[7]), str(row.iloc[9])

        if not sel_cats or cat in sel_cats:
            st.markdown(f"""
                <div class="card">
                    <span class="tag-cat">{cat}</span>
                    <div style="font-weight:bold; color:#008080;">{subj}</div>
                    <div style="font-size:1.2rem; font-weight:700;">{team if len(team)>1 else subj}</div>
                    <div style="color:#555;">Gr {grade} | 📅 {date} | 📍 {ven}</div>
                    {f'<div style="background:#eee;padding:8px;border-radius:5px;margin-top:5px;">{info}</div>' if len(info)>2 else ''}
                </div>
            """, unsafe_allow_html=True)
else:
    st.warning("Data is nog nie beskikbaar nie. Gaan na jou Google Sheet en maak seker daar is data onder die opskrifte in die 'Upcoming' tab.")

if st.button("Dwing Vars Data"):
    st.rerun()
