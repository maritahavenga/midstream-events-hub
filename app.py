import streamlit as st
import pandas as pd

# 1. Basiese Opset
st.set_page_config(page_title="LMCP Event Hub", layout="centered")

# 2. Styl (Midstream Rooi)
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .nav-bar { background-color: #800000; color: white; padding: 20px; text-align: center; border-radius: 10px; margin-bottom: 20px; }
    .card { background: white; padding: 20px; border-radius: 12px; border-left: 10px solid #800000; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .tag { background: #800000; color: white; padding: 3px 10px; border-radius: 5px; font-size: 11px; font-weight: bold; }
    .info { background: #f1f3f5; padding: 10px; border-radius: 5px; margin-top: 10px; border-left: 3px solid #008080; font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="nav-bar"><h1>MIDSTREAM COLLEGE</h1><p>PRIMARY EVENT HUB</p></div>', unsafe_allow_html=True)

# 3. Die Skakel (Upcoming tab)
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

# Helper: maak Display Duration veilig na int
def safe_int(x):
    try:
        x = str(x).strip()
        if x == "":
            return None
        return int(float(x))
    except:
        return None

try:
    df = pd.read_csv(URL)
    df.columns = df.columns.str.strip()
    df = df.fillna("")

    # --- Kolomme uit jou CSV ---
    COL_CAT      = "Category"
    COL_SUBJ     = "Activity/Subject Name"
    COL_TEAM     = "Team"
    COL_DATE     = "Date / Due Date"
    COL_VEN      = "Venue"
    COL_INFO     = "Information"
    COL_GRADE    = "Age Gro_
