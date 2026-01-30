mport streamlit as st
import pandas as pd
import requests, io, datetime

st.set_page_config(page_title="LMCP Hub", layout="centered")

# --- BANNER ---
st.markdown("<h1 style='text-align:center;color:#800000;'>LMCP EVENT HUB</h1>", unsafe_allow_html=True)

# ONS GEBRUIK NOU DIE DIREKTE DOCS ID OM GOOGLE TE DWING
SID = "1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8"
U = f"https://docs.google.com/spreadsheets/d/{SID}/export?format=csv&gid=0"

@st.cache_data(ttl=1)
def ld():
    try:
        # Hierdie dwing 'n vars konneksie elke keer
        r = requests.get(f"{U}&v={datetime.datetime.now().timestamp()}", timeout=10)
        df = pd.read_csv(io.StringIO(r.content.decode('utf-8')), dtype=str).fillna("")
        return df
    except Exception as e:
        return pd.DataFrame()

df = ld()

if not df.empty:
    st.success(f"✅ {len(df)} Events gevind!")
    
    for _, r in df.iterrows():
        try:
            # Ons lees die kolomme in volgorde (0, 3, 5, 6)
            act = str(r.iloc[3])  # Activity
            date = str(r.iloc[5]) # Date
            ven = str(r.iloc[6])  # Venue
            
            if len(act) < 2: continue

            st.markdown(f"""
            <div style="background:white; padding:15px; border-radius:10px; border-left:8px solid #800000; margin-bottom:10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                <b style="color:#800000;">{act}</b><br>
                📅 {date} | 📍 {ven}
            </div>
            """, unsafe_allow_html=True)
        except: continue
else:
    st.warning("⚠️ Google stuur nog nie die data nie. Maak seker die Sheet is 'Public' (Anyone with the link can view).")
    if st.button("Probeer Weer"):
        st.cache_data.clear()
        st.rerun()
