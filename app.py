import streamlit as st
import pandas as pd
import requests, io

st.set_page_config(page_title="LMCP Hub", layout="centered")

st.markdown("<h1 style='text-align:center;color:#800000;'>LAERSKOOL MIDSTREAM COLLEGE PRIMARY</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:#008080;font-weight:bold;text-align:center;'>Digital Event Hub</p>", unsafe_allow_html=True)

# JOU SHEET ID EN GID
SID = "1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8"
GID = "37057995"

# ONS GEBRUIK DIE 'GVIZ' SKAKEL - DIT IS 'N ANDER PAD NA DIE DATA
URL = f"https://docs.google.com/spreadsheets/d/{SID}/gviz/tq?tqx=out:csv&gid={GID}"

@st.cache_data(ttl=1)
def load_data():
    try:
        # Ons probeer die data trek asof ons 'n gewone webblaaier is
        r = requests.get(URL, timeout=10)
        if r.status_code == 200:
            df = pd.read_csv(io.StringIO(r.content.decode('utf-8')), dtype=str).fillna("")
            return df
        return pd.DataFrame()
    except:
        return pd.DataFrame()

df = load_data()

st.markdown("---")

if not df.empty:
    st.success(f"✅ Data gekoppel! ({len(df)} rye)")
    for index, row in df.iterrows():
        try:
            # Kolom D=3, F=5, G=6
            act = str(row.iloc[3]).strip()
            date = str(row.iloc[5]).strip()
            ven = str(row.iloc[6]).strip()
            
            if len(act) < 2 or "activity" in act.lower():
                continue

            st.markdown(f"""
            <div style="background:white; padding:15px; border-radius:10px; border-left:8px solid #800000; margin-bottom:10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                <b style="color:#800000;">{act}</b><br>
                📅 {date} | 📍 {ven}
            </div>
            """, unsafe_allow_html=True)
        except:
            continue
else:
    st.error("Google se sekuriteit blokkeer steeds die konneksie.")
    st.write("Indien dit môre nog so is, moet die IT-departement net 'External Sharing' vir hierdie sheet aanskakel.")
    if st.button("Probeer weer"):
        st.rerun()
