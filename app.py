import streamlit as st
import pandas as pd
import requests, io

st.set_page_config(page_title="LMCP Event Hub", layout="centered")

# --- UI STYLING ---
st.markdown("""
    <style>
    .nav-bar { background: linear-gradient(135deg, #800000 0%, #a00000 100%); color: white; padding: 25px; text-align: center; border-radius: 0 0 20px 20px; margin-top: -60px; }
    .card { background: white; padding: 20px; border-radius: 15px; border-left: 10px solid #800000; margin-top: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    .tag-cat { background: #800000; color: white; padding: 3px 10px; border-radius: 6px; font-size: 0.7rem; font-weight: bold; }
    .event-title { color: #222; font-size: 1.2rem; font-weight: 700; margin: 8px 0; }
    .map-btn { display: inline-block; background-color: white; color: #008080 !important; padding: 8px 16px; border-radius: 8px; text-decoration: none; font-weight: bold; border: 1px solid #008080; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="nav-bar"><h1>MIDSTREAM COLLEGE</h1><p>PRIMARY EVENT HUB</p></div>', unsafe_allow_html=True)

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

@st.cache_data(ttl=2)
def load_data():
    try:
        # Ons dwing 'n nuwe versoek af
        r = requests.get(f"{URL}&cb={pd.Timestamp.now().timestamp()}", timeout=15)
        # Lees die data sonder om te worry oor die "header"
        df = pd.read_csv(io.StringIO(r.content.decode('utf-8')), header=None)
        return df
    except:
        return None

df = load_data()

# As daar data is, maar die eerste ry is dalk die opskrifte
if df is not None and len(df) > 1:
    # Ons skuif die eerste ry na die opskrifte
    df.columns = df.iloc[0]
    df = df[1:].reset_index(drop=True)
    df = df.fillna("")

    # Filter op die eerste kolom (Category)
    all_cats = sorted(df.iloc[:, 0].unique().astype(str))
    sel_cats = st.multiselect("Select Category:", all_cats)

    for i in range(len(df)):
        row = df.iloc[i]
        # Veiligheids-mapping: gebruik kolomnommers
        c = str(row.iloc[0]) # Category
        a = str(row.iloc[1]) # Activity
        t = str(row.iloc[2]) # Team
        d = str(row.iloc[3]) # Date
        v = str(row.iloc[4]) # Venue
        l = str(row.iloc[5]) # Link

        if not sel_cats or c in sel_cats:
            st.markdown(f"""
                <div class="card">
                    <span class="tag-cat">{c}</span>
                    <div style="color:#008080; font-weight:bold; margin-top:5px;">{a}</div>
                    <div class="event-title">{t}</div>
                    <div style="color:#555;">📅 <b>{d}</b> | 📍 {v}</div>
                    {f'<a href="{l}" target="_blank" class="map-btn">📂 VIEW</a>' if 'http' in l else ''}
                </div>
            """, unsafe_allow_html=True)
elif df is not None and len(df) == 1:
    st.warning("I can see the headers, but there are no events listed in the rows below. Check your 'Upcoming' tab filters.")
else:
    st.error("Still no data connection. Check if the 'Upcoming' tab has data and is published.")

if st.button("Refresh Now"):
    st.cache_data.clear()
    st.rerun()
