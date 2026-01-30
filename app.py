import streamlit as st, pandas as pd, requests, io, re, pytz
from datetime import datetime
import streamlit.components.v1 as v1
from streamlit_autorefresh import st_autorefresh

# ================= CONFIG =================
st.set_page_config(page_title="LMCP Hub", layout="centered")
st_autorefresh(interval=120000, key="r_token")

U = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

def cl(v): return str(v).replace(".0", "").replace("nan", "").strip()

def tr(t, a):
    r = str(a).strip()
    t = re.sub(r'\bG\b', 'Girls', t)
    if re.search(r'(?i)\b(EAT|HT|Hooftaal|Eerste)\b', r):
        return "Afrikaans " + ("Eerste Addisionele Taal" if "eat" in r.lower() or "eerste" in r.lower() else "Hooftaal")
    d = {"Saal": "Hall", "Veld": "Field", "Atletiek": "Athletics", "Wiskunde": "Math"}
    for k, v in d.items(): t = re.sub(rf'\b{k}\b', v, t, flags=re.IGNORECASE)
    return t

def c_a(n):
    n = str(n).lower()
    for x in ["athletics", "atletiek", "hockey", "rugby", "netball", "netbal", "tennis"]:
        if x in n: return x.capitalize().replace("Netbal", "Netball").replace("Atletiek", "Athletics")
    if any(k in n for k in ["eat", "ht", "hooftaal", "eerste"]):
        return "Afrikaans " + ("EAT" if "eat" in n else "HT")
    return n.capitalize()

@st.cache_data(ttl=10)
def ld():
    try:
        r = requests.get(U, timeout=8)
        return pd.read_csv(io.StringIO(r.content.decode('utf-8')), dtype=str).fillna("")
    except: return pd.DataFrame()

df = ld()

if not df.empty:
    # --- Filter UI ---
    st.markdown("<div style='background:#ffffff;padding:20px;border-radius:15px;border:1px solid #eeeeee;box-shadow:0 4px 15px rgba(0,0,0,0.05);margin-bottom:25px;'>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1: sc = st.multiselect("Category", ["Sport", "Culture", "Academics"])
    with c2:
        m = df.iloc[:, 2].str.contains('|'.join(sc) if sc else ".*", case=False)
        if sc and "Academics" in sc: m |= df.iloc[:, 2].str.contains("academic", case=False)
        sa = st.multiselect("Activity", sorted(list({c_a(o) for o in df[m].iloc[:, 3]})))
    with c3:
        ao = ["Gr 1","Gr 2","Gr 3","Gr 4","Gr 5","Gr 6","Gr 7","U7","U8","U9","U10","U11","U12","U13"]
        opts = [o for o in ao if "U" in o] if sc == ["Sport"] else ([o for o in ao if "Gr" in o] if sc and "Sport" not in str(sc) else ao)
        sg = st.multiselect("Age Group", options=opts, key="stk_val")
    sq = st.text_input("Search Events...", placeholder="Type to filter results...")
    st.markdown("</div>", unsafe_allow_html=True)

    # --- Logic ---
    tn = set()
    for s in sg:
        v_m = re.findall(r'\d+', s)
        if v_m: 
            v = int(v_m[0])
            tn.update([v, v+6 if v<=7 else v-6])

    res = []
    for _, r in df.iterrows():
        n, cat, av, rd = str(r.iloc[3]), str(r.iloc[2]).lower
