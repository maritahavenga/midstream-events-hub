import streamlit as st
import pandas as pd

# =============================
# 1. Basiese opset
# =============================
st.set_page_config(page_title="LMCP Event Hub", layout="centered")

# =============================
# 2. Styl (Midstream rooi)
# =============================
st.markdown("""
<style>
.stApp { background-color: #f8f9fa; }
.nav-bar { background-color: #800000; color: white; padding: 20px; text-align: center; border-radius: 10px; margin-bottom: 20px; }
.card { background: white; padding: 20px; border-radius: 12px; border-left: 10px solid #800000; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
.tag { background: #800000; color: white; padding: 3px 10px; border-radius: 5px; font-size: 11px; font-weight: bold; }
.info { background: #f1f3f5; padding: 10px; border-radius: 5px; margin-top: 10px; border-left: 3px solid #008080; font-size: 14px; }
</style>
""", unsafe_allow_html=True)

st.markdown(
    '<div class="nav-bar"><h1>MIDSTREAM COLLEGE</h1><p>PRIMARY EVENT HUB</p></div>',
    unsafe_allow_html=True
)

# =============================
# 3. Google Sheets CSV
# =============================
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

# =============================
# 4. Data laai
# =============================
try:
    df = pd.read_csv(URL)
    df.columns = df.columns.str.strip()
    df = df.fillna("")

    # DEBUG – kan jy later uithaal
    # st.write("Kolomme:", list(df.columns))

    if df.empty:
        st.info("Geen data beskikbaar nie.")
        st.stop()

    # =============================
    # Kategorie filter
    # =============================
    categories = sorted([c for c in df["Category"].unique() if str(c).strip()])
    selected = st.multiselect("Kies Kategorie:", categories)

    # =============================
    # Events wys
    # =============================
    for _, row in df.iterrows():

        c_cat   = row["Category"].strip()
        c_subj  = row["Activity/Subject"].strip()
        c_team  = row["Team"].strip()
        c_date  = row["Date / Due Date"]
        c_ven   = row["Venue"]
        c_info  = row["Information"]
        c_grade = row["Age Group (9,10…)"] if "Age Group (9,10…)" in df.columns else ""
        c_link  = row["Programme / Doc"]

        if selected and c_cat not in selected:
            continue

        title = c_team if c_team else c_subj

        st.markdown(f"""
        <div class="card">
            <span class="tag">{c_cat}</span>
            <div style="color:#008080; font-weight:bold; margin-top:8px;">{c_subj}</div>
            <div style="font-size:1.2rem; font-weight:bold;">{title}</div>
            <div style="color:#555; font-size:14px;">
                Grade {c_grade} | 📅 {c_date} | 📍 {c_ven}
            </div>
            {f'<div class="info">{c_info}</div>' if str(c_info).strip() else ''}
            {f'<a href="{c_link}" target="_blank"><button style="margin-top:10px;">📂 OOP DOKUMENT</button></a>' if str(c_link).startswith("http") else ''}
        </div>
        """, unsafe_allow_html=True)

except Exception as e:
    st.error("Kon nie tans met Google Sheets koppel nie.")
    st.code(str(e))
