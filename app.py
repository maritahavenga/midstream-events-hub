import streamlit as st
import pandas as pd
import requests, io, re, pytz
from datetime import datetime
import streamlit.components.v1 as v1
from streamlit_autorefresh import st_autorefresh

# ---------------- CONFIG ----------------
st.set_page_config(page_title="LMCP Hub", layout="centered")
st_autorefresh(interval=120000, key="r")

U = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

# ---------------- HELPERS ----------------
def cl(v):
    return str(v).replace(".0", "").replace("nan", "").strip()

def tr(t, a):
    r = str(a).strip()
    t = t.replace(" G ", " Girls ").replace(" G", " Girls")

    if re.search(r'(?i)\b(EAT|HT|Hooftaal|Eerste)\b', r):
        return "Afrikaans " + (
            "Eerste Addisionele Taal"
            if "eat" in r.lower() or "eerste" in r.lower()
            else "Hooftaal"
        )

    d = {
        "Saal": "Hall",
        "Veld": "Field",
        "Atletiek": "Athletics",
        "Wiskunde": "Math"
    }
    for k, v in d.items():
        t = re.sub(rf'\b{k}\b', v, t, flags=re.IGNORECASE)

    return t

def c_a(n):
    n = n.lower()
    for x in ["athletics","atletiek","hockey","rugby","netball","netbal","tennis"]:
        if x in n:
            return x.capitalize().replace("Netbal","Netball").replace("Atletiek","Athletics")

    if any(x in n for x in ["eat","ht","hooftaal","eerste"]):
        return "Afrikaans " + (
            "Eerste Addisionele Taal" if "eat" in n or "eerste" in n else "Hooftaal"
        )

    return n.capitalize()

# ---------------- DATA LOAD ----------------
@st.cache_data(ttl=10)
def ld():
    try:
        r = requests.get(f"{U}&cb={datetime.now().timestamp()}", timeout=5)
        return pd.read_csv(io.StringIO(r.content.decode("utf-8")), dtype=str).fillna("")
    except:
        return pd.DataFrame()

df = ld()

# ---------------- UI ----------------
if not df.empty:

    st.markdown(
        "<div style='background:white;padding:10px;border-radius:10px;border:1px solid #eee;'>",
        unsafe_allow_html=True
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        sc = st.multiselect("Category", ["Sport", "Culture", "Academics"])

    with c2:
        m = df.iloc[:, 2].str.contains('|'.join(sc) if sc else ".*", case=False)
        if sc and "Academics" in sc:
            m |= df.iloc[:, 2].str.contains("academic", case=False)

        sa = st.multiselect(
            "Activity",
            sorted({c_a(o) for o in df[m].iloc[:, 3]})
        )

    with c3:
        # 🔒 STABLE AGE OPTIONS (never removed)
        ao = [
            "Gr 1","Gr 2","Gr 3","Gr 4","Gr 5","Gr 6","Gr 7",
            "U7","U8","U9","U10","U11","U12","U13"
        ]

        sg = st.multiselect(
            "Age Group",
            options=ao,
            key="stk_stable"
        )

    sq = st.text_input("Search")

    st.markdown("</div>", unsafe_allow_html=True)

    # ---------------- AGE MATCHING LOGIC ----------------
    tn = set()
    for s in sg:
        v_m = re.findall(r'\d+', s)
        if v_m:
            v = int(v_m[0])
            # U ↔ Grade equivalence ONLY for filtering
            tn.update([v, v + 6 if v <= 7 else v - 6])

    # ---------------- FILTER DATA ----------------
    res = []
    for _, r in df.iterrows():
        n   = str(r.iloc[3])
        cat = str(r.iloc[2]).lower()
        av  = cl(r.iloc[11])
        rd  = cl(r.iloc[5])

        dt = pd.to_datetime(rd, dayfirst=True, errors="coerce")

        cm = (
            any(x.lower() in cat for x in sc)
            or ("Academics" in sc and "academic" in cat)
        ) if sc else True

        if not cm:
            continue

        if sa and c_a(n) not in sa:
            continue

        v_m = re.findall(r'\d+', av)
        if tn and v_m and int(v_m[0]) not in tn:
            continue

        res.append({
            "r": r,
            "dt": dt if pd.notnull(dt) else datetime(2099,1,1),
            "dd": rd
        })

    res.sort(key=lambda x: x["dt"])

    # ---------------- CARDS ----------------
    h = """
    <style>
    .card{
        background:white;
        padding:12px;
        border-radius:10px;
        border-left:8px solid #800000;
        margin-bottom:10px;
        box-shadow:0 2px 5px rgba(0,0,0,0.1);
        font-family:sans-serif;
    }
    .title{color:#800000;font-weight:bold;}
    .btn{
        background:#800000;
        color:white!important;
        padding:5px 8px;
        border-radius:5px;
        text-decoration:none;
        font-size:0.7rem;
        display:inline-block;
        margin:5px 5px 0 0;
    }
    .nt{
        background:#f0f7f7;
        padding:6px;
        border-radius:5px;
        font-size:0.75rem;
    }
    </style>
    """

    for i in res:
        r  = i["r"]
        ds = i["dd"]

        cv  = str(r.iloc[2]).lower()
        act = str(r.iloc[3])
        age = cl(r.iloc[11])
        ven = cl(r.iloc[6])

        ia = "afrikaans" in act.lower() or "eat" in act.lower()
        ic = "academic" in cv or any(x in act.lower() for x in ["math","science"])

        b1 = "Dokumente" if ia else ("Document" if ic else "Programme")
        b2 = "Assessment" if ic or ia else "Team List"

        btns = "".join([
            f"<a href='{cl(r.iloc[j])}' target='_blank' class='btn'>"
            f"{b1 if j==7 else (b2 if j==8 else 'Information')}</a>"
            for j in [7,8,10]
            if "http" in cl(r.iloc[j]).lower()
        ])

        note = (
            f"<div class='nt'>{cl(r.iloc[10])}</div>"
            if cl(r.iloc[10]) and "http" not in cl(r.iloc[10]).lower()
            else ""
        )

        ts = (
            tr(act, act)
            + " "
            + (("U" if "sport" in cv else "Gr ") + age if age else "")
            + " "
            + tr(cl(r.iloc[4]), act)
        )

        if sq and sq.lower() not in ts.lower():
            continue

        vh = (
            f"<div style='margin-top:4px;'>📍 "
            f"<a href='http://googleusercontent.com/maps.google.com/search?q="
            f"{ven.replace(' ','+')}+Midstream' target='_blank' "
            f"style='color:#008080;text-decoration:none;font-weight:bold;font-size:0.8rem;'>"
            f"{tr(ven, act).upper()}</a></div>"
            if ven else ""
        )

        h += f"""
        <div class='card'>
            <div class='title'>{ts}</div>
            <div>📅 {ds}</div>
            {vh}
            {note}
            <div>{btns}</div>
        </div>
        """

    v1.html(h, height=3000, scrolling=True)

st.markdown(
    "<center style='font-size:0.7rem;color:#999;'>LMCP Digital Hub 2026</center>",
    unsafe_allow_html=True
)
