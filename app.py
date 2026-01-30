import streamlit as st
import pandas as pd
import requests, io

# Stel die bladsy op
st.set_page_config(page_title="LMCP Hub", layout="centered")

# --- DIE STYL (Ons hou dit eenvoudig vir nou) ---
st.markdown("""
    <style>
    .header { background-color: #800000; color: white; padding: 20px; text-align: center; border-radius: 10px; }
    .card { background: white; padding: 15px; border-radius: 10px; border-left: 8px solid #800000; margin-top: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="header"><h1>MIDSTREAM EVENT HUB</h1></div>', unsafe_allow_html=True)

# ONS GEBRUIK DIE REKORDS-PAD (Dit is dikwels vinniger as CSV)
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?output=csv"

def get_data_no_cache():
    try:
        # Geen cache nie, ons vra Google direk met 'n vars tydstempel
        import time
        response = requests.get(f"{URL}&t={int(time.time())}", timeout=10)
        if response.status_code == 200:
            return pd.read_csv(io.StringIO(response.content.decode('utf-8')), dtype=str).fillna("")
    except Exception as e:
        st.error(f"Fout: {e}")
        return None
    return None

df = get_data_no_cache()

if df is not None and not df.empty:
    st.success("✅ Data is gelaai!")
    
    # Soekbalk
    search = st.text_input("Soek vir 'n aktiwiteit...", "")

    for i in range(len(df)):
        try:
            row = df.iloc[i]
            # Ons gebruik die posisies wat vroeër gewerk het
            act = str(row.iloc[3]).strip() # Kolom D
            date = str(row.iloc[5]).strip() # Kolom F
            ven = str(row.iloc[6]).strip() # Kolom G
            
            if len(act) > 2 and "activity" not in act.lower():
                if search.lower() in act.lower() or search.lower() in ven.lower():
                    st.markdown(f"""
                        <div class="card">
                            <b style="color:#800000; font-size:1.2rem;">{act}</b><br>
                            <span style="color:#008080;">📅 {date}</span> | 📍 {ven}
                        </div>
                        """, unsafe_allow_html=True)
        except:
            continue
else:
    st.warning("Google neem te lank. Verfris asseblief jou browser-bladsy (F5).")

if st.button("Dwing Herlaai"):
    st.rerun()
