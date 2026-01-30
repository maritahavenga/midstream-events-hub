<div class="header-banner">
        <h1 style='margin:0;'>LAERSKOOL MIDSTREAM COLLEGE</h1>
        <p style='margin:0; opacity:0.9;'>Primary Event Hub</p>
    </div>
    """, unsafe_allow_html=True)

# --- DATA KONNEKSIE ---
# Ons gebruik die mees direkte pad na jou blad (Sheet ID en GID)
SHEET_ID = "1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8"
GID = "37057995"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

@st.cache_data(ttl=10) # Verfris elke 10 sekondes
def get_data():
    try:
        # Hierdie lees die CSV direk in 'n tabel in
        return pd.read_csv(URL, on_bad_lines='skip')
    except Exception as e:
        return None

df = get_data()

st.write("") 

if df is not None:
    search = st.text_input("🔍 Soek vir aktiwiteit...", "")
    
    st.markdown("### Opkomende Events")
    
    found_any = False
    # Ons kyk deur die rye (ons begin by ry 0)
    for index, row in df.iterrows():
        try:
            # Ons gebruik die kolom-nommers: 3=Activity, 5=Date, 6=Venue
            act = str(row.iloc[3]).strip()
            date = str(row.iloc[5]).strip()
            ven = str(row.iloc[6]).strip()
            
            # Slaan leë rye of die opskrif ry oor
            if len(act) < 2 or "activity" in act.lower() or "nan" in act.lower():
                continue
            
            # Soek filter
            if search.lower() in act.lower() or search.lower() in ven.lower():
                found_any = True
                st.markdown(f"""
                    <div class="event-card">
                        <div class="event-title">{act}</div>
                        <div style="color:#008080; font-weight:bold;">📅 {date}</div>
                        <div style="color:#555;">📍 {ven.upper()}</div>
                    </div>
                    """, unsafe_allow_html=True)
        except:
            continue

    if not found_any:
        st.info("Besig om data te sinkroniseer... Verfris asseblief oor 'n paar sekondes.")
else:
    st.error("Kon nie die Google Sheet bereik nie. Maak seker die blad is op 'Anyone with the link can view' gestel.")

# --- REFRESH ---
if st.button("🔄 Herlaai Nou"):
    st.cache_data.clear()
    st.rerun()
