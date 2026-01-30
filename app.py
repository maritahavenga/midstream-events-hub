import streamlit as st
import pandas as pd
import requests, io

st.set_page_config(page_title="LMCP Event Hub", layout="centered")

st.markdown("""
    <style>
    .nav-bar { background: linear-gradient(135deg, #800000 0%, #a00000 100%); color: white; padding: 25px; text-align: center; border-radius: 0 0 20px 20px; margin-top: -60px; }
    .card { background: white; padding: 20px; border-radius: 15px; border-left: 10px solid #800000; margin-top: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    .tag-cat { background: #800000; color: white; padding: 3px 10px; border-radius: 6px; font-size: 0.7rem; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="nav-bar"><h1>MIDSTREAM COLLEGE</h1><p>DIAGNOSTIC MODE</p></div>', unsafe_allow_html=True)

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

@st.cache_data(ttl=1)
def load_data():
    try:
        r = requests.get(f"{URL}&cb={pd.Timestamp.now().timestamp()}", timeout=15)
        if r.status_code != 200:
            return f"Google Error: Status {r.status_code}"
        
        # Probeer die data lees
        content = r.content.decode('utf-8')
        if len(content) < 10:
            return "Error: Die lêer vanaf Google is leeg."
            
        df = pd.read_csv(io.StringIO(content)).fillna("")
        return df
    except Exception as e:
        return f"System Error: {str(e)}"

result = load_data()

# AS DIT 'N FOUTBOODSKAP IS (String)
if isinstance(result, str):
    st.error(result)
    st.info("Gaan na 'File > Share > Publish to Web' en maak seker die 'Upcoming' tab is gepubliseer as CSV.")

# AS DIT DATA IS (DataFrame)
elif result is not None and not result.empty:
    st.success(f"Sukses! Ek sien {len(result)} rye data.")
    
    # Wys 'n vinnige tabel van wat hy sien vir 5 sekondes
    if st.checkbox("Wys rou data"):
        st.write(result.head())

    # Die normale kaartjies
    for i in range(len(result)):
        row = result.iloc[i]
        cat, act, team = str(row.iloc[0]), str(row.iloc[1]), str(row.iloc[2])
        st.markdown(f"""
            <div class="card">
                <span class="tag-cat">{cat}</span>
                <div style="font-weight:bold; margin-top:5px;">{act}</div>
                <div style="font-size:1.2rem;">{team}</div>
            </div>
        """, unsafe_allow_html=True)
else:
    st.warning("Geen data gevind nie. Is die 'Upcoming' tab dalk leeg?")

if st.button("Refresh Hub"):
    st.cache_data.clear()
    st.rerun()
