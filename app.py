import streamlit as st
import pandas as pd
import requests, io, time

st.set_page_config(page_title="LMCP Event Hub", layout="centered")

# --- UI STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .nav-bar { background: linear-gradient(135deg, #800000 0%, #a00000 100%); color: white; padding: 25px; text-align: center; border-radius: 0 0 20px 20px; margin-top: -60px; }
    .card { background: white; padding: 20px; border-radius: 15px; border-left: 10px solid #800000; margin-top: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    .whole-term-card { border-left: 10px solid #FFD700 !important; background-color: #fffdf0 !important; }
    .tag-cat { background: #800000; color: white; padding: 3px 10px; border-radius: 6px; font-size: 0.7rem; font-weight: bold; text-transform: uppercase; }
    .event-title { color: #222; font-size: 1.2rem; font-weight: 700; margin: 5px 0; }
    .info-box { background: #f1f3f5; padding: 10px; border-radius: 8px; font-size: 0.85rem; color: #444; margin: 10px 0; border-left: 3px solid #008080; white-space: pre-wrap; }
    .map-btn { display: inline-block; background-color: white; color: #008080 !important; padding: 8px 16px; border-radius: 8px; text-decoration: none; font-weight: bold; border: 1px solid #008080; margin-top: 5px; font-size: 0.8rem; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="nav-bar"><h1>MIDSTREAM COLLEGE</h1><p>PRIMARY EVENT HUB</p></div>', unsafe_allow_html=True)

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

# ONS VERWYDER CACHE VOLLEDIG OM DATA TERUG TE BRING
def get_fresh_data():
    try:
        # Timestamp dwing Google om vars data te stuur
        r = requests.get(f"{URL}&cb={time.time()}", timeout=10)
        # As Google HTML stuur ipv CSV, vang ons dit hier
        if "<!DOCTYPE" in r.text or "html" in r.text.lower()[:50]:
            return "HTML_ERROR"
        df = pd.read_csv(io.StringIO(r.text)).fillna("")
        return df
    except:
        return None

df = get_fresh_data()

if df is str(df) and df == "HTML_ERROR":
    st.error("Google stuur weer HTML. Verfris asb die bladsy oor 'n minuut.")
elif df is not None and not df.empty:
    # FILTERS
    all_cats = sorted([str(x) for x in df.iloc[:, 0].unique() if str(x).strip()])
    sel_cats = st.multiselect("Kies Kategorie:", all_cats)
    
    all_grades = sorted([str(x) for x in df.iloc[:, 9].unique() if str(x).strip()])
    sel_grades = st.multiselect("Filter op Graad:", all_grades)

    for i in range(len(df)):
        row = df.iloc[i]
        
        # JOU LYS PRESIES BELYN:
        cat   = str(row.iloc[0])  # A: Category
        subj  = str(row.iloc[1])  # B: Activity / Subject
        asses = str(row.iloc[2])  # C: Team / Assessment
        date  = str(row.iloc[3])  # D: Date
        ven   = str(row.iloc[4])  # E: Venue
        lnk   = str(row.iloc[5])  # F: Link
        team  = str(row.iloc[6])  # G: Team
        info  = str(row.iloc[7])  # H: Information
        grade = str(row.iloc[9])  # J: Grade
        dur   = str(row.iloc[10]) # K: Duration

        display_title = team if len(team) > 1 else (asses if len(asses) > 1 else subj)
        is_whole = "whole term" in dur.lower() or "whole term" in date.lower()

        if (not sel_cats or cat in sel_cats) and (not sel_grades or grade in sel_grades):
            card_class = "card whole-term-card" if is_whole else "card"
            st.markdown(f"""
                <div class="{card_class}">
                    <span class="tag-cat">{cat}</span>
                    <div style="color:#008080; font-weight:bold; margin-top:5px;">{subj}</div>
                    <div class="event-title">{display_title}</div>
                    <div style="color:#555; font-size:0.9rem;">
                        <b>Target: {grade}</b> | 📅 {date} | 📍 {ven}
                    </div>
                    {f'<div class="info-box">ℹ️ {info}</div>' if len(info) > 2 else ''}
                    {f'<a href="{lnk}" target="_blank" class="map-btn">📂 OOP DOKUMENT</a>' if 'http' in lnk else ''}
                </div>
            """, unsafe_allow_html=True)
else:
    st.info("Besig om konneksie te herstel... Klik op 'Dwing Verfris' as die data nie binne 5 sekondes verskyn nie.")

if st.button("Dwing Verfris"):
    st.rerun()
