import streamlit as st
import pandas as pd
import requests, io

# 1. Page Configuration
st.set_page_config(page_title="LMCP Event Hub", layout="centered")

# 2. Professional Styling
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #f8f9fa; }
    .nav-bar {
        background: linear-gradient(135deg, #800000 0%, #a00000 100%);
        color: white; padding: 25px; text-align: center;
        border-radius: 0 0 20px 20px; margin-top: -60px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    .card {
        background: white; padding: 20px; border-radius: 15px;
        border-left: 10px solid #800000; margin-top: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .tag-container { margin-bottom: 8px; }
    .tag-cat { background: #800000; color: white; padding: 3px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: bold; text-transform: uppercase; }
    .tag-act { background: #008080; color: white; padding: 3px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: bold; margin-left: 5px; text-transform: uppercase; }
    .event-title { color: #333; font-size: 1.35rem; font-weight: 700; margin: 5px 0; }
    .info-line { color: #555; font-size: 1rem; margin-top: 2px; }
    .map-btn {
        display: inline-block; background-color: #e8f4f4; color: #008080 !important;
        padding: 8px 15px; border-radius: 8px; text-decoration: none;
        font-weight: bold; font-size: 0.85rem; margin-top: 12px; border: 1px solid #008080;
    }
    </style>
    """, unsafe_allow_html=True)

# Header
st.markdown('<div class="nav-bar"><h1>MIDSTREAM COLLEGE</h1><p>PRIMARY EVENT HUB</p></div>', unsafe_allow_html=True)

# 3. Data Connection
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?output=csv"

@st.cache_data(ttl=10)
def load_data():
    try:
        r = requests.get(URL, timeout=15)
        if r.status_code == 200:
            return pd.read_csv(io.StringIO(r.content.decode('utf-8')), dtype=str).fillna("")
    except: return None
    return None

df = load_data()

if df is not None and not df.empty:
    st.write("")
    
    # --- SMART FILTERS (English UI) ---
    
    # Filter 1: Category (Multi-select)
    all_cats = sorted([c for c in df.iloc[:, 1].unique() if len(str(c)) > 1])
    selected_cats = st.multiselect("1. Category (Sport, Culture, Academics):", all_cats)

    # Filter 2: Activity (Dynamic Multi-select)
    temp_df = df[df.iloc[:, 1].isin(selected_cats)] if selected_cats else df
    all_acts = sorted([a for a in temp_df.iloc[:, 2].unique() if len(str(a)) > 1])
    selected_acts = st.multiselect("2. Activity (Tennis, Choir, etc.):", all_acts)

    # Filter 3: Universal Age / Grade
    age_options = ["U7 (Gr 1)", "U8 (Gr 2)", "U9 (Gr 3)", "U10 (Gr 4)", "U11 (Gr 5)", "U12 (Gr 6)", "U13 (Gr 7)"]
    selected_age_labels = st.multiselect("3. Age Group / Grade:", age_options)
    
    # Create search keys for both U-format and Grade-format
    search_keys = []
    for label in selected_age_labels:
        u_val = label.split(" ")[0] # e.g. U11
        g_val = label.split("(")[1].replace(")", "") # e.g. Gr 5
        search_keys.extend([u_val, g_val])

    # Filter 4: Search Bar
    search_query = st.text_input("4. Search specifically:", placeholder="Search venue, team or date...").lower()

    # --- FILTER LOGIC & DISPLAY ---
    count = 0
    for i in range(len(df)):
        row = df.iloc[i]
        category = str(row.iloc[1]).strip()
        activity = str(row.iloc[2]).strip()
        age_data = str(row.iloc[3]).strip().replace("/", "").upper()
        date_val = str(row.iloc[5]).strip()
        venue_val = str(row.iloc[6]).strip()
        map_link = str(row.iloc[7]).strip()

        # Check conditions (Default to True if filter is empty)
        m_cat = not selected_cats or category in selected_cats
        m_act = not selected_acts or activity in selected_acts
        m_age = not search_keys or any(k.upper().replace(" ","") in age_data.replace(" ","") for k in search_keys)
        m_search = not search_query or (search_query in str(row).lower())

        if m_cat and m_act and m_age and m_search:
            if len(activity) > 1:
                count += 1
                st.markdown(f"""
                    <div class="card">
                        <div class="tag-container">
                            <span class="tag-cat">{category}</span>
                            <span class="tag-act">{activity}</span>
                        </div>
                        <div class="event-title">{row.iloc[3]}</div>
                        <div class="info-line">📅 <b>{date_val}</b></div>
                        <div class="info-line">📍 {venue_val}</div>
                        {f'<a href="{map_link}" target="_blank" class="map-btn">📍 OPEN MAP</a>' if 'http' in map_link else ''}
                    </div>
                    """, unsafe_allow_html=True)
    
    if count == 0:
        st.info("No events found for your selection. Try clearing some filters.")
else:
    st.warning("Google Connection is refreshing. Please wait a moment and then use the button below.")

# Refresh Button
st.markdown("---")
if st.button("🔄 Refresh Hub"):
    st.cache_data.clear()
    st.rerun()

st.caption("© 2026 Midstream College Primary Hub")
