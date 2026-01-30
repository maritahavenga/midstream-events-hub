import streamlit as st
import pandas as pd
import requests, io, re, pytz
from datetime import datetime

st.set_page_config(page_title="LMCP Hub", layout="centered")

# --- BANNER ---
st.markdown("<h1 style='text-align:center;color:#800000;'>LMCP DEBUG MODE</h1>", unsafe_allow_html=True)

# JOU SKAKEL
U = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?output=csv"

@st.cache_data(ttl=1)
def ld():
    try:
        # Ons dwing Google om vars data te gee
        r = requests.get(f"{U}&nocache={datetime.now().timestamp()}", timeout=15)
        df = pd.read_csv(io.StringIO(r.content.decode('utf-8')), dtype=str).fillna("")
        return df
    except Exception as e:
        st.error(f"Konneksie Fout: {e}")
        return pd.DataFrame()

df = ld()

# --- STAP 1: WYS DIE ROU DATA TABEL ---
if not df.empty:
    st.write("### ✅ Data is suksesvol gelaai!")
    st.write(f"Aantal rye gevind: {len(df)}")
    st.write("Hier is die eerste 5 rye van jou sheet:")
    st.dataframe(df.head(5)) # Dit sal die rou tabel wys
    
    # --- STAP 2: PROBEER DIE KAARTE BOU ---
    st.markdown("---")
    
    # Ons gebruik nou jou kolom-opskrifte presies soos jy hulle gestuur het
    res = []
    for _, r in df.iterrows():
        try:
            # Ons probeer die kolomme by die naam kry in plaas van nommer
            # As die name in Excel presies soos onder is, sal dit werk
            act = str(r['Activity/Subject Name'])
            date_val = str(r['Date / Due Date'])
            
            res.append({"act": act, "date": date_val})
        except:
            # As name nie werk nie, gebruik ons weer die nommers
            res.append({"act": str(r.iloc[3]), "date": str(r.iloc[5])})

    for i in res:
        st.markdown(f"**Event:** {i['act']} | **Datum:** {i['date']}")

else:
    st.error("❌ Die data-tabel is leeg. Google stuur geen data deur hierdie skakel nie.")
    st.write("Gaan asseblief na jou Google Sheet > File > Share > Publish to Web.")
    st.write("Maak seker dit is op 'Comma-separated values (.csv)' gestel.")
