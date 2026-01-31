import streamlit as st
import pandas as pd

st.set_page_config(page_title="LMCP Hub", layout="centered")

# Skool Kleure & Styl
st.markdown("""
    <style>
    .stApp { background-color: #f4f4f4; }
    .nav-bar { background-color: #800000; color: white; padding: 20px; text-align: center; border-radius: 10px; }
    .card { background: white; padding: 15px; border-radius: 10px; border-left: 8px solid #800000; margin-bottom: 15px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    .tag { background: #800000; color: white; padding: 2px 8px; border-radius: 5px; font-size: 10px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="nav-bar"><h1>MIDSTREAM COLLEGE</h1><p>EVENT HUB</p></div>', unsafe_allow_html=True)

# Die CSV skakel wat jy vir my gegee het
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

def load_data():
    # Ons lees die URL direk - die eenvoudigste manier moontlik
    return pd.read_csv(URL)

try:
    df = load_data().fillna("")
    
    if not df.empty:
        # Kategories en Graad Filters
        cat_list = sorted(df.iloc[:, 0].unique())
        sel_cat = st.multiselect("Kies Kategorie:", cat_list)

        for i in range(len(df)):
            row = df.iloc[i]
            # Mapping: A=0, B=1, G=6 (Team), H=7 (Info), J=9 (Grade)
            cat, subj, team, date, ven = str(row.iloc[0]), str(row.iloc[1]), str(row.iloc[6]), str(row.iloc[3]), str(row.iloc[4])
            info, grade = str(row.iloc[7]), str(row.iloc[9])

            if not sel_cat or cat in sel_cat:
                st.markdown(f"""
                <div class="card">
                    <span class="tag">{cat}</span>
                    <div style="font-weight:bold; color:#008080; margin-top:5px;">{subj}</div>
                    <div style="font-size:18px; font-weight:bold;">{team if len(team)>1 else subj}</div>
                    <div style="color:#555;">Grade {grade} | 📅 {date} | 📍 {ven}</div>
                    {f'<div style="font-size:13px; margin-top:10px; color:#333; background:#f9f9f9; padding:5px;">{info}</div>' if len(info)>2 else ''}
                </div>
                """, unsafe_allow_html=True)
    else:
        st.error("Die lêer is leeg. Maak seker die data is in jou 'Upcoming' tab.")

except Exception as e:
    st.warning("🔄 Besig om data te verfris... Klik die knoppie hieronder.")
    if st.button("Herlaai Hub"):
        st.cache_data.clear()
        st.rerun()
