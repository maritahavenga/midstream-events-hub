import streamlit as st
import pandas as pd
import urllib.parse as up

st.set_page_config(page_title="Events Hub", layout="wide")

# This CSS forces columns to stay side-by-side on mobile
st.markdown("""<style>
.stApp{background:#008080}.block-container{padding-top:0rem;max-width:800px}
.card{background:white;padding:15px;border-radius:15px;border-left:12px solid #800000;margin-bottom:5px;box-shadow:0 4px 10px rgba(0,0,0,0.2)}
.t{color:#800000;font-weight:bold;font-size:1rem}.v{color:#800000;font-weight:bold;text-decoration:underline}
/* Force columns to stay horizontal on mobile */
[data-testid="column"] {
    width: 24% !important;
    flex: 1 1 24% !important;
    min-width: 24% !important;
}
div[data-testid="stHorizontalBlock"] {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
}
.stButton button {
    width: 100%; background: #800000!important; color: white!important; 
    font-weight: bold; height: 2.8em; font-size: 0.6rem!important; 
    padding: 0px!important; border-radius: 6px; border: none;
}
div[data-baseweb="select"] > div { background-color: #800000 !important; border: none !important; }
div[data-baseweb="select"] * { color: white !important; }
.box{background:#f1f3f5;padding:10px;border-radius:10px;margin-top:5px;border-left:5px solid #008080;color:#333;font-size:0.8rem}
label { color: white !important; font-weight: bold; }
</style>""", unsafe_allow_html=True)

st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", use_container_width=True)
st.markdown("<h2 style='text-align:center;color:white;'>EVENTS HUB 2026</h2>", unsafe_allow_html=True)

U = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQifU4qPRCQVNckxHBtA75jfhVR-tqFXUIMEi5z1pdnE-YUgAQvUfaEEDBcwr3VfeSZCBPmePk067rn/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=2)
def load():
    df = pd.read_csv(U)
    df.columns = [str(c).strip() for c in df.columns]
    return df

try:
    df_raw = load()
    ch = st.selectbox("Filter Events:", ["All", "Sport", "Culture", "Academics"])
    data = df_raw if ch == "All" else df_raw[df_raw['Category'].str.contains(ch, case=False, na=False)]

    for _, r in data.iterrows():
        evt, dat = str(r.get('Event','Event')), str(r.get('Date','TBA'))
        ven, nfo = str(r.get('Venue','TBA')), str(r.get('Information',''))
        mu = f"https://www.google.com/maps/search/?api=1&query={up.quote(ven + ' Midstream')}"
        is_l = nfo.startswith('http')
        bx = f'<div class="box"><b>Note:</b> {nfo}</div>' if (nfo.strip() and nfo.lower()!='nan' and not is_l) else ""

        st.markdown(f'''<div class="card"><div>📅 {dat}</div><div class="t">{evt}</div><div>📍 <a href="{mu}" target="_blank" class="v">{ven}</a></div>{bx}</div>''', unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)
        
        cols = r.index.tolist()
        prog = next((r[c] for c in cols if "Program" in c), None)
        team = next((r[c] for c in cols if "Team" in c), None)
        sign = next((r[c] for c in cols if any(x in c for x in ["Transport", "Sign", "Confirm"])), None)

        with c1:
            if pd.notna(prog) and str(prog).strip().startswith("http"): st.link_button("PROG", str(prog))
        with c2:
            if pd.notna(team) and str(team).strip().startswith("http"): st.link_button("TEAM", str(team))
        with c3:
            if pd.notna(sign) and str(sign).strip().startswith("http"): st.link_button("CONFIRM", str(sign))
        with c4:
            if is_l: st.link_button("INFO", nfo)
            
        st.markdown("<br>", unsafe_allow_html=True)
except Exception:
    st.info("Syncing events...")
