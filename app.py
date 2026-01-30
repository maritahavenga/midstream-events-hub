import streamlit as st, pandas as pd, requests, io, re, pytz
from datetime import datetime
import streamlit.components.v1 as v1
from streamlit_autorefresh import st_autorefresh

# ================= CONFIG & STYLE =================
st.set_page_config(page_title="LMCP Hub", layout="centered")
st_autorefresh(interval=120000, key="refresh_token")

# Google Sheet CSV URL
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

# ================= HELPERS =================
def cl(v): return str(v).replace(".0", "").replace("nan", "").strip()

def tr(text, activity):
    text, activity = str(text), str(activity).lower()
    # Afrikaans benamings
    if any(x in activity for x in ["eat", "ht", "hooftaal", "eerste"]):
        return "Afrikaans " + ("Eerste Addisionele Taal" if "eat" in activity or "eerste" in activity else "Hooftaal")
    # Vertalings & Girls regstelling
    repl = {"Saal": "Hall", "Veld": "Field", "Atletiek": "Athletics", "Wiskunde": "Math", " G ": " Girls ", " G": " Girls"}
    for k, v in repl.items(): 
        text = re.sub(rf"\b{k}\b", v, text, flags=re.IGNORECASE)
    return text

def clean_activity_name(name):
    name = str(name).lower()
    # Skoonmaak van Sport name (verwyder kodes soos P4/P8)
    for s in ["athletics", "atletiek", "hockey", "rugby", "netball", "netbal", "tennis"]:
        if s in name: 
            return s.capitalize().replace("Netbal", "Netball").replace("Atletiek", "Athletics")
    if any(x in name for x in ["eat", "ht", "hooftaal", "eerste"]):
        return "Afrikaans " + ("EAT" if "eat" in name else "HT")
    return name.capitalize()

# ================= DATA LOAD =================
@st.cache_data(ttl=15)
def load_data():
    try:
        r = requests.get(DATA_URL, timeout=8)
        return pd.read_csv(io.StringIO(r.content.decode("utf-8")), dtype=str).fillna("")
    except: return pd.DataFrame()

df = load_data()

# ================= UI FILTERS (Oorspronklike Look) =================
if not df.empty:
    st.markdown("<div style='background:#f9f9f9;padding:20px;border-radius:15px;border:1px solid #ddd;margin-bottom:20px;'>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    
    with c1: 
        sc = st.multiselect("Category", ["Sport", "Culture", "Academics"])
    
    with c2:
        mask = df.iloc[:, 2].str.contains("|".join(sc) if sc else ".*", case=False)
        if "Academics" in sc: mask |= df.iloc[:, 2].str.contains("academic", case=False)
        # Gebruik skoon name vir die dropdown
        sa = st.multiselect("Activity", sorted({clean_activity_name(x) for x in df[mask].iloc[:, 3]}))
    
    with c3:
        # Dinamiese maar STICKY Age Group
        all_ages = ["Gr 1","Gr 2","Gr 3","Gr 4","Gr 5","Gr 6","Gr 7","U7","U8","U9","U10","U11","U12","U13"]
        if sc == ["Sport"]: opts = [o for o in all_ages if "U" in o]
        elif sc and "Sport" not in str(sc): opts = [o for o in all_ages if "Gr" in o]
        else: opts = all_ages
        sg = st.multiselect("Age Group", opts, key="sticky_age_key")

    sq = st.text_input("Search Events...", placeholder="Type to search...")
    st.markdown("</div>", unsafe_allow_html=True)

    # ================= LOGIKA: Gr 4 = U10 MAPPING =================
    age_match = set()
    for s in sg:
        nums = re.findall(r"\d+", s)
        if nums:
            v = int(nums[0])
            age_match.add(v)
            # Voeg die maatjie by: Gr 4 (4) <-> U10 (10)
            age_match.add(v - 6 if v > 7 else v + 6)

    # ================= FILTER & SORTERING =================
    results = []
    for _, row in df.iterrows():
        cat, act, age, rd = str(row.iloc[2]).lower(), str(row.iloc[3]), cl(row.iloc[11]), cl(row.iloc[5])
        
        if sc and not (
