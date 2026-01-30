import streamlit as st
import pandas as pd

st.set_page_config(page_title="LMCP Hub", layout="centered")

# --- BANNER ---
st.markdown("<h1 style='text-align:center; color:#800000;'>MIDSTREAM EVENT HUB</h1>", unsafe_allow_html=True)

# ONS GEBRUIK DIE PUBLIEKE CSV SKAKEL (DIT IS DIE MEES REGUIT PAD)
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?output=csv"

@st.cache_data(ttl=5)
def load_raw_data():
    try:
        # Ons probeer die data direk lees
        df = pd.read_csv(URL)
        return df
    except Exception as e:
        st.error(f"Google Fout: {e}")
        return None

df = load_raw_data()

if df is not None:
    st.success("✅ ONS HET DATA!")
    
    # Wys 'n soekbalk
    search = st.text_input("🔍 Soek...", "")
    
    # Wys die data in mooi boksies
    for index, row in df.iterrows():
        try:
            # Kolom nommers (A=0, B=1, C=2, D=3, E=4, F=5, G=6)
            # Volgens jou sheet is Aktiwiteit in D (3), Datum in F (5), Venue in G (6)
            act = str(row.iloc[3]).strip()
            date = str(row.iloc[5]).strip()
            ven = str(row.iloc[6]).strip()

            if len(act) > 2 and "activity" not in act.lower():
                if search.lower() in act.lower() or search.lower() in ven.lower():
                    st.markdown(f"""
                    <div style="background:white; padding:15px; border-radius:10px; border-left:8px solid #800000; margin-bottom:10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <b style="color:#800000; font-size:1.1rem;">{act}</b><br>
                        <span style="color:#008080;">📅 {date}</span> | <span style="color:#555;">📍 {ven}</span>
                    </div>
                    """, unsafe_allow_html=True)
        except:
            continue
else:
    st.warning("Wag tans vir Google om die 'Publish' skakel aktief te maak. Dit kan tot 2 minute neem.")
    if st.button("Probeer weer"):
        st.cache_data.clear()
        st.rerun()
