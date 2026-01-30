import streamlit as st
import pandas as pd

st.set_page_config(page_title="LMCP Hub", layout="centered")

# --- DIE STYL (Ons hou dit minimalisties sodat dit vinnig laai) ---
st.markdown("""
    <style>
    .stApp { background-color: #f4f4f4; }
    .header { background: #800000; color: white; padding: 20px; text-align: center; border-radius: 10px; margin-bottom: 20px; }
    .event-card { background: white; padding: 15px; border-radius: 10px; border-left: 8px solid #800000; margin-bottom: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="header"><h1>MIDSTREAM EVENT HUB</h1></div>', unsafe_allow_html=True)

# ONS GEBRUIK DIE DIREKTE EXPORT PAD (Dit is dikwels vinniger as die PUB pad)
SHEET_ID = "1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=2) # Ons hou die data net vir 2 sekondes
def load_fast():
    try:
        # Ons gebruik pandas se ingeboude leser wat baie vinnig is
        df = pd.read_csv(URL, timeout=5) # Gee hom net 5 sekondes om te antwoord
        return df
    except:
        return None

df = load_fast()

if df is not None and not df.empty:
    st.success("Data gelaai!")
    
    # Soekbalk
    search = st.text_input("🔍 Soek aktiwiteit...", "")

    for i in range(len(df)):
        try:
            row = df.iloc[i]
            # Kolomme: D=3, F=5, G=6
            act = str(row.iloc[3]).strip()
            date = str(row.iloc[5]).strip()
            ven = str(row.iloc[6]).strip()
            
            if len(act) > 2 and "activity" not in act.lower():
                if search.lower() in act.lower() or search.lower() in ven.lower():
                    st.markdown(f"""
                        <div class="event-card">
                            <b style="color:#800000; font-size:1.1rem;">{act}</b><br>
                            <span style="color:#008080;"><b>📅 {date}</b></span><br>
                            <span style="color:#555;">📍 {ven}</span>
                        </div>
                        """, unsafe_allow_html=True)
        except:
            continue
else:
    st.error("Google antwoord nie vinnig genoeg nie.")
    st.info("Dit gebeur soms as Google se publieke skakel 'moeg' is. Wag 30 sekondes en klik 'Herlaai'.")
    if st.button("🔄 Herlaai"):
        st.cache_data.clear()
        st.rerun()

st.caption("Verfris die bladsy as die data nie dadelik verskyn nie.")
