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
    COL_LINK     = "Programme / Document Link"
    COL_DURATION = "Display Duration"

    if not df.empty:

        # --- parse datum ---
        df["_event_dt"] = pd.to_datetime(df[COL_DATE], errors="coerce", dayfirst=True)
        df["_dur_days"] = df[COL_DURATION].apply(safe_int)

        today = pd.Timestamp.now(tz="Africa/Johannesburg").normalize().tz_localize(None)

        # --- expiry filter (wys vir X dae ná datum) ---
        def expired(row):
            dt = row["_event_dt"]
            dur = row["_dur_days"]
            if pd.isna(dt) or dur is None:
                return False  # as ons nie kan bereken nie, wys dit eerder
            expiry_date = dt.normalize() + pd.Timedelta(days=dur)
            return today > expiry_date

        df = df[~df.apply(expired, axis=1)].copy()

        # --- sort volgens datum (naaste eerste) ---
        df["_sort_dt"] = df["_event_dt"].fillna(pd.Timestamp.max)
        df = df.sort_values("_sort_dt", ascending=True)

        # Kategorie Filter (jy kan dit hou, al wys ons nie Category op kaart nie)
        cats = sorted([c for c in df[COL_CAT].unique() if str(c).strip()])
        sel_cat = st.multiselect("Kies Kategorie:", cats)

        for _, row in df.iterrows():
            c_cat  = str(row[COL_CAT]).strip()
            if sel_cat and c_cat not in sel_cat:
                continue

            c_subj = str(row[COL_SUBJ]).strip()
            c_team = str(row[COL_TEAM]).strip()
            c_date = str(row[COL_DATE]).strip()
            c_ven  = str(row[COL_VEN]).strip()
            c_info = str(row[COL_INFO]).strip()
            c_link = str(row[COL_LINK]).strip()

            # 1) Moenie dubbel wys nie: kies 'n enkel titel
            title = c_team if c_team else c_subj

            st.markdown(f"""
            <div class="card">
                <div style="font-size:1.2rem; font-weight:bold;">{title}</div>
                <div style="color:#555; font-size:14px; margin-top:6px;">📅 {c_date}</div>
                <div style="color:#555; font-size:14px;">📍 {c_ven}</div>
                {f'<div class="info">{c_info}</div>' if c_info.strip() else ''}
            </div>
            """, unsafe_allow_html=True)

            # Link knoppie buite card (soos jou vorige uitleg)
            if c_link.startswith("http"):
                st.link_button("📂 OOP DOKUMENT", c_link)

    else:
        st.info("Wagtend op data vanaf die 'Upcoming' tab...")

except Exception as e:
    st.error("Kon nie tans met Google Sheets koppel nie.")
    st.code(str(e))
    if st.button("Probeer weer"):
        st.rerun()
