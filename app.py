import streamlit as st
import pandas as pd
import requests, io

st.set_page_config(page_title="LMCP Hub", layout="centered")

# --- MODERNE STYL ---
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .event-card {
        background: white;
        padding: 24px;
        border-radius: 18px;
        border-left: 12px solid #800000;
        box-shadow: 0 6px 12px rgba(0,0,0,0.08);
        margin-bottom: 18px;
    }
    .event-title { color: #800000; font-size: 1.4rem; font-weight: bold; margin-bottom: 8px; }
    .date-text { color: #008080; font-size: 1.1rem; font-weight: 600; }
    .venue-text { color: #555; font-size: 1rem; margin-top: 4px; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center; color:#800000; margin-bottom:0;'>LMCP EVENT HUB</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#666; margin-top:0;'>Altyd op datum</p>", unsafe_allow_html=True)

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?output=csv"

# --- HIERDIE DEEL STOP DIE BLOCKING ---
@st.cache_data(ttl=300) # Die app onthou die data vir 5 MINUTE (300 sekondes)
def get_safe_data():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(URL, headers=headers, timeout=10)
        if r.status_code == 200:
            return pd.read_csv(io.StringIO(r.content.decode('utf-8')), dtype=str).fillna("")
    except:
        return None
    return None

df = get_safe_data()

if df is not None and not df.empty:
    # Soekbalk vir ouers
    search = st.text_input("🔍 Soek aktiwiteit (bv. Rugby, Tennis...)", "")

    for i in range(len(df)):
        try:
            row = df.iloc[i]
            act = str(row.iloc[3]).strip()
            date = str(row.iloc[5]).strip()
            ven = str(row.iloc[6]).strip()

            if len(act) > 2 and "activity" not in act.lower():
                # As daar gesoek word, filter die data
                if search.lower() in act.lower() or search.lower() in ven.lower():
                    st.markdown(f"""
                        <div class="event-card">
                            <div class="event-title">{act}</div>
                            <div class="date-text">📅 {date}</div>
                            <div class="venue-text">📍 {ven}</div>
                        </div>
                        """, unsafe_allow_html=True)
        except:
            continue
else:
    st.error("Besig om konneksie te verfris... Wag asseblief 'n oomblik.")
    if st.button("Herlaai nou"):
        st.cache_data.clear()
        st.rerun()

st.markdown("---")
st.caption("Data word elke 5 minute outomaties verfris vanaf Google Sheets.")
