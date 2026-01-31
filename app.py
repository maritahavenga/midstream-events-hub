import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="LMCP Event Hub", layout="centered")

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

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"


def norm(s: str) -> str:
    """Normaliseer kolomname sodat klein verskille nie breek nie."""
    s = str(s).strip().lower()
    s = s.replace("\ufeff", "")  # verwyder BOM indien daar is
    s = s.replace("…", "...")    # maak ellipsis uniform
    s = re.sub(r"\s+", "", s)    # verwyder spasies
    s = re.sub(r"[^\w]+", "", s) # verwyder / ( ) ens.
    return s


def read_sheet_safely(url: str) -> pd.DataFrame:
    """Probeer verskillende header-rye (0,1,2) tot die kolomme sin maak."""
    last = None
    for hdr in (0, 1, 2):
        try:
            df0 = pd.read_csv(url, header=hdr).fillna("")
            df0.columns = [str(c).strip() for c in df0.columns]
            # Basiese sanity check: moet minstens 'Category' êrens hê
            cols_norm = {norm(c) for c in df0.columns}
            if "category" in cols_norm:
                return df0
            last = df0
        except Exception as e:
            last = e
    # As ons hier uitkom, return die laaste poging (of raise)
    if isinstance(last, Exception):
        raise last
    return last


def pick_col(df: pd.DataFrame, *candidates: str) -> str:
    """
    Kry die werklike kolomnaam in df wat ooreenstem met een van candidates.
    Candidates kan klein verskille hê.
    """
    lookup = {norm(c): c for c in df.columns}  # norm -> actual
    for cand in candidates:
        key = norm(cand)
        if key in lookup:
            return lookup[key]
    return ""


try:
    df = read_sheet_safely(URL)

    # --- MATCH kolomme robust ---
    col_category = pick_col(df, "Category")
    col_subject  = pick_col(df, "Activity/Subject", "Activity Subject", "Activity", "Subject")
    col_team     = pick_col(df, "Team")
    col_date     = pick_col(df, "Date / Due Date", "Date", "Due Date")
    col_venue    = pick_col(df, "Venue")
    col_info     = pick_col(df, "Information", "Info")
    col_link     = pick_col(df, "Programme / Doc", "Programme/Doc", "Programme Doc", "Document", "Doc")
    col_grade    = pick_col(df, "Age Group (9,10…)", "Age Group (9,10...)", "Age Group", "AgeGroup")

    required = {
        "Category": col_category,
        "Activity/Subject": col_subject,
        "Team": col_team,
        "Date / Due Date": col_date,
        "Venue": col_venue,
        "Information": col_info,
        "Programme / Doc": col_link,
    }

    missing = [k for k, v in required.items() if not v]
    if missing:
        st.error("Ek kan nie jou kolomme match nie. Hierdie velde ontbreek:")
        st.write(missing)
        st.write("Kolomme wat ek wel sien in die CSV:")
        st.write(list(df.columns))
        st.stop()

    if df.empty:
        st.info("Geen data beskikbaar nie.")
        st.stop()

    # Kategorie filter
    categories = sorted([c for c in df[col_category].unique() if str(c).strip()])
    selected = st.multiselect("Kies Kategorie:", categories)

    # Events wys
    for _, row in df.iterrows():
        c_cat  = str(row[col_category]).strip()
        if selected and c_cat not in selected:
            continue

        c_subj = str(row[col_subject]).strip()
        c_team = str(row[col_team]).strip() if col_team else ""
        c_date = str(row[col_date]).strip()
        c_ven  = str(row[col_venue]).strip()
        c_info = str(row[col_info]).strip()
        c_link = str(row[col_link]).strip()
        c_grade = str(row[col_grade]).strip() if col_grade else ""

        title = c_team if c_team else c_subj

        st.markdown(f"""
        <div class="card">
            <span class="tag">{c_cat}</span>
            <div style="color:#008080; font-weight:bold; margin-top:8px;">{c_subj}</div>
            <div style="font-size:1.2rem; font-weight:bold;">{title}</div>
            <div style="color:#555; font-size:14px;">
                Grade {c_grade} | 📅 {c_date} | 📍 {c_ven}
            </div>
            {f'<div class="info">{c_info}</div>' if c_info else ''}
            {f'<a href="{c_link}" target="_blank"><button style="margin-top:10px;">📂 OOP DOKUMENT</button></a>' if c_link.startswith("http") else ''}
        </div>
        """, unsafe_allow_html=True)

except Exception as e:
    st.error("Kon nie tans met Google Sheets koppel nie.")
    st.code(str(e))
