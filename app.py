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

    # --- MATCH k
