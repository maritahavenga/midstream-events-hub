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
    .event-title { color: #222; font-size: 1.2rem; font-weight: 700; margin: 5px 0; }
    .info-box { background: #f1f3f5; padding: 10px; border-radius: 8px; font-size: 0.85rem; color: #444; margin: 10px 0; border-left: 3px solid #008080; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="nav-bar"><h1>MIDSTREAM COLLEGE</h1><p>PRIMARY EVENT HUB</p></div>', unsafe_allow_html=True)

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

try:
    # Ons gebruik 'n unieke tydstempel sodat Google nie 'n ou weergawe stuur nie
    r = requests.get(f"{URL}&t={time.time()}", timeout=15)
    # header=None dwing pandas om elke ry as data te sien, selfs ry 1
    df = pd.read_csv(io.StringIO(r.text), header=None).fillna("")
    
    # As die bladsy meer as 1 ry het (opskrifte + data)
    if len(df) > 1:
        # Ons skip ry 0 (die opskrifte) en loop deur die res
        for i in range(1, len(df)):
            row = df.iloc[i]
            
            # Slegs as daar iets in kolom A of B staan
            if len(str(row[0])) > 1:
                cat   = str(row[0])  # A
                subj  = str(row[1])  # B
                asses = str(row[2])  # C
                date  = str(row[3])  # D
                ven   = str(row[4])  # E
                lnk   = str(row[5])  # F
                team  = str(row[6])  # G
                info  = str(row[7])  # H
                grade = str(row[9])  # J
                
                title = team if len(team) > 1 else (asses if len(asses) > 1 else subj)
                
                st.markdown(f"""
                    <div class="card">
                        <span class="tag-cat">{cat}</span>
                        <div style="color:#008080; font-weight:bold; margin-top:5px;">{subj}</div>
                        <div class="event-title">{title}</div>
                        <div style="color:#555; font-size:0.9rem;">
                            <b>Gr {grade}</b> | 📅 {date} | 📍 {ven}
                        </div>
                        {f'<div class="info-box">ℹ️ {info}</div>' if len(info) > 2 else ''}
                    </div>
                """, unsafe_allow_html=True)
                if "http" in str(lnk):
                    st.link_button("📂 OOP DOKUMENT", str(lnk))
    else:
        st.warning("⚠️ Die CSV-lêer is leeg. Gaan asb na die 'Upcoming' tab en maak seker die data is sigbaar onder die opskrifte.")
        # Debug: wys wat Google stuur
        st.write("Rou data vanaf Google:", r.text[:100])

except Exception as e:
    st.error(f"Fout: {e}")

if st.button("Herlaai Hub"):
    st.rerun()
