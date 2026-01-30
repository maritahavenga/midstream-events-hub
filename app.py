import streamlit as st
import pandas as pd
import requests, io, re, pytz
from datetime import datetime

st.set_page_config(page_title="LMCP Hub", layout="centered")

# --- BANNER ---
st.markdown("""
<div style='text-align:center; padding: 10px;'>
    <h1 style='color:#800000; font-family:sans-serif; margin-bottom:0;'>LAERSKOOL MIDSTREAM COLLEGE PRIMARY</h1>
    <p style='color:#008080; font-size:1.2rem; margin-top:5px; font-weight:bold;'>Digital Event Hub</p>
</div>
""", unsafe_allow_html=True)

# KOPIEER HIERDIE SKAKEL PRESIES VANAF JOU FOTO
U = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?output=csv"

def cl(v): return str(v).replace(".0", "").replace("nan", "").strip()

def fix_text(t):
    t = str(t).replace("nan", "").strip()
    # Outomatiese vertalings vir vakke
    t = t.replace("Afrikaans FAL", "Afrikaans Eerste Addisionele Taal")
    t = t.replace("Afrikaans HT", "Afrikaans Hooftaal")
    # Tennis Fix (U13 C -> U13C)
    t = re.sub(r'(U\d+)\s+([A-D])', r'\1\2', t)
    return t

@st.cache_data(ttl=1)
def ld():
    try:
        # Die tydstempel dwing Google om vars data te gee
        r = requests.get(f"{U}&v={datetime.now().timestamp()}", timeout=15)
        if r.status_code == 200:
            df = pd.read_csv(io.StringIO(r.content.decode('utf-8')), dtype=str).fillna("")
            return df
        return pd.DataFrame()
    except: return pd.DataFrame()

df = ld()

if not df.empty:
    try:
        # Kolom-name presies soos in jou Google Sheet agtergrond
        C_CAT = "Category"
        C_ACT = "Activity/Subject Name"
        C_DESC = "Team / Assessment"
        C_DATE = "Date / Due Date"
        C_VEN = "Venue"
        C_DOC = "Programme / Document Link"
        C_TEAM = "TeamConfirm"
        C_INFO = "Information"
        C_AGE = "Age Group (9,10) / Grade (1,2,3)"

        # Filters bo-aan
        st.markdown("<div style='background-color:#f9f9f9; padding:20px; border-radius:15px; margin-bottom:20px;'>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1: sa = st.multiselect("Activity", sorted(df[C_ACT].unique()))
        with c2: sg = st.multiselect("Grade/Age", sorted(df[C_AGE].unique()))
        sq = st.text_input("🔍 Search Events", placeholder="Tik om te soek...")
        st.markdown("</div>", unsafe_allow_html=True)

        res = []
        for _, r in df.iterrows():
            act = fix_text(r[C_ACT])
            age = cl(r[C_AGE])
            date_raw = str(r[C_DATE]).strip()
            
            # Logika vir U vs Gr
            prefix = "U" if any(x in act.lower() for x in ["rugby", "netball", "hockey", "tennis"]) else "Gr "
            full_title = f"{act} {prefix}{age} {fix_text(r[C_DESC])}".strip()
            
            if sa and not any(x in act for x in sa): continue
            if sg and age not in sg: continue
            if sq and sq.lower() not in full_title.lower(): continue
            
            res.append({"title": full_title, "date": date_raw, "venue": str(r[C_VEN]), "doc": cl(r[C_DOC]), "team": cl(r[C_TEAM])})

        # Wys die kaarte
        for i in res:
            btns = ""
            if "http" in i['doc']: btns += f"<a href='{i['doc']}' target='_blank' style='background:#800000; color:white; padding:8px 12px; border-radius:5px; text-decoration:none; display:inline-block; margin-top:10px; margin-right:5px;'>Info</a>"
            if "http" in i['team']: btns += f"<a href='{i['team']}' target='_blank' style='background:#008080; color:white; padding:8px 12px; border-radius:5px; text-decoration:none; display:inline-block; margin-top:10px;'>Teams</a>"
            
            st.markdown(f"""
            <div style="background:white; padding:20px; border-radius:12px; border-left:10px solid #800000; margin-bottom:20px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
                <b style="color:#800000; font-size:1.2rem;">{i['title']}</b><br>
                <span style="color:#555;">📅 {i['date']}</span><br>
                <b style="color:#008080;">📍 {i['venue'].upper()}</b><br>
                {btns}
            </div>
            """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Fout met data-uitlees: {e}. Maak seker die opskrifte in Excel is korrek.")
else:
    st.info("🔄 Besig om data vanaf Google te trek... Klik 'Force Refresh' as dit lank neem.")
    if st.button("Force Refresh"):
        st.cache_data.clear()
        st.rerun()

st.markdown("<br><center style='font-size:0.8rem;color:#999;'>LAERSKOOL MIDSTREAM COLLEGE PRIMARY Digital Hub 2026</center>", unsafe_allow_html=True)
