# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import requests, io, re, pytz
from datetime import datetime, timedelta
import hashlib

st.set_page_config(page_title="LMCP Hub", page_icon="📌", layout="wide")

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

# ✅ Your logo (direct PNG)
LOGO_URL = "https://midstream-primary.co.za/wp-content/uploads/2022/01/210828_Midstream_Icon-removebg-preview.png"

TZ = pytz.timezone("Africa/Johannesburg")

if not str(CSV_URL).strip().lower().startswith(("http://", "https://")):
    st.error("CSV_URL is missing/invalid. Paste the FULL https://...output=csv link.")
    st.stop()

# ------------------ STYLE ------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap');
html, body, [class*="css"] {font-family: 'Inter', sans-serif;}
:root{
  --card:#ffffff; --line:#e8edf5; --shadow:0 10px 30px rgba(0,0,0,.06);
  --maroon:#800000; --teal:#008080; --muted:#64748b;
}
.block-container{padding-top:.8rem;}
section[data-testid="stSidebar"]{border-right:1px solid var(--line);}

/* Top banner (shorter + professional) */
.topBanner{
  border-radius:22px;
  padding:14px 16px;
  margin-bottom:18px;
  background: linear-gradient(135deg, rgba(128,0,0,0.98), rgba(0,128,128,0.92));
  box-shadow: var(--shadow);
  color: #fff;
  display:flex; align-items:center; gap:14px; flex-wrap:wrap;
}
.topLogo{
  width:66px;height:66px;border-radius:16px;
  background:#fff; display:flex; align-items:center; justify-content:center;
  overflow:hidden; border: 2px solid rgba(255,255,255,0.45);
}
.topLogo img{width:66px;height:auto;}
.topText{line-height:1.05;}
.topTitle{font-weight:900;font-size:1.26rem; letter-spacing:.2px;}
.topSubRow{
  margin-top:7px;
  font-weight:800;
  font-size:.98rem;
  opacity:.96;
  display:flex;
  gap:10px;
  flex-wrap:wrap;
}
.pill{
  display:inline-block;
  padding:6px 10px;
  border-radius:999px;
  background:rgba(255,255,255,0.18);
  border:1px solid rgba(255,255,255,0.22);
}

/* Cards */
.card{
  border:1px solid var(--line);
  background:var(--card);
  box-shadow:var(--shadow);
  border-radius:18px;
  padding:14px 14px 12px 14px;
  margin-bottom:14px;
  border-left:10px solid var(--maroon);
  position:relative;
}
.card-title{font-weight:900;color:var(--maroon);font-size:1.15rem;line-height:1.2;}
.meta{color:var(--muted);margin-top:8px;font-size:.95rem;}
.noteBlock{
  margin-top:12px; padding:12px;
  border-radius:14px;
  background:rgba(0,128,128,0.08);
  border:1px solid rgba(0,128,128,0.25);
  color:#0f172a; font-size:.95rem; line-height:1.35;
}
.btnRow{display:flex;gap:10px;flex-wrap:wrap;margin-top:12px;}
.btn{
  display:inline-block;background:#008080;color:white !important;
  padding:9px 12px;border-radius:12px;font-weight:900;
  text-decoration:none;font-size:.90rem;
}
.btn:hover{opacity:.92;}

/* Per-card NEW UPDATE ribbon */
.ribbon{
  position:absolute; top:12px; right:12px;
  background:#FFD400;
  color:#B00000;
  font-weight:1000;
  font-size:.78rem;
  padding:6px 10px;
  border-radius:999px;
  border: 1px solid rgba(176,0,0,0.25);
  box-shadow: 0 8px 16px rgba(0,0,0,0.10);
  display:flex; align-items:center; gap:8px;
}
.rDot{
  width:8px;height:8px;border-radius:999px;background:#B00000;
  animation:pulse 1.0s infinite;
}
@keyframes pulse{
  0%{transform:scale(1); opacity:.4;}
  50%{transform:scale(1.7); opacity:1;}
  100%{transform:scale(1); opacity:.4;}
}
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="topBanner">
  <div class="topLogo"><img src="{LOGO_URL}"></div>
  <div class="topText">
    <div class="topTitle">LAERSKOOL MIDSTREAM COLLEGE PRIMARY</div>
    <div class="topSubRow">
      <span class="pill">Digital Hub</span>
      <span class="pill">midstreamprimary.co.za</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ------------------ HELPERS ------------------
def safe_txt(x) -> str:
    s = str(x or "")
    return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").strip()

def is_http(u: str) -> bool:
    s = str(u or "").strip().lower()
    return s.startswith("http://") or s.startswith("https://")

def is_form_link(u: str) -> bool:
    s = str(u or "").lower()
    return ("forms.gle" in s) or ("docs.google.com/forms" in s)

def clean_first_url(v: str) -> str:
    s = str(v or "").replace("\n"," ").strip()
    m = re.search(r"https?://\S+", s)
    return m.group(0) if m else s

def normalize_category(v: str) -> str:
    s = str(v or "").strip().lower()
    if "sport" in s: return "sport"
    if "culture" in s or "kultuur" in s: return "culture"
    if "academic" in s or "academics" in s or "akadem" in s: return "academics"
    return s

def normalize_activity(v: str) -> str:
    s = str(v or "").strip().lower()
    s = re.sub(r"\s+"," ", s)
    if s in ["ht","afrikaans ht"] or "hooftaal" in s:
        return "Afrikaans Hooftaal"
    if s in ["eat","afrikaans eat"] or "eerste addisionele" in s:
        return "Afrikaans Eerste Addisionele Taal"
    if "athletics" in s or "atletiek" in s: return "Athletics"
    if "swimming" in s or "swem" in s or "gala" in s: return "Swimming"
    if "tennis" in s: return "Tennis"
    if "rugby" in s: return "Rugby"
    if "hockey" in s: return "Hockey"
    if "netbal" in s or "netball" in s: return "Netball"
    return s.title()

def is_afrikaans_subject(b_raw: str) -> bool:
    s = str(b_raw or "").strip().lower()
    return ("afrikaans" in s) or (s in ["ht","eat"]) or ("hooftaal" in s) or ("eerste addisionele" in s)

def norm_gender_words(text: str) -> str:
    s = str(text or "").strip().replace("_", " ")
    s = re.sub(r"\s+"," ", s).strip()

    s = re.sub(r"\bmeisies\b", "Girls", s, flags=re.I)
    s = re.sub(r"\bseuns\b", "Boys", s, flags=re.I)

    has_boys = re.search(r"\bboys\b", s, flags=re.I) is not None
    has_girls = re.search(r"\bgirls\b", s, flags=re.I) is not None

    s = re.sub(r"\bgirls\b", "Girls", s, flags=re.I)
    s = re.sub(r"\bboys\b", "Boys", s, flags=re.I)

    if not has_boys:
        s = re.sub(r"\bB\b", "Boys", s)
    if not has_girls:
        s = re.sub(r"\bG\b", "Girls", s)

    s = re.sub(r"(Boys)\s*(Boys)\b", r"\1", s)
    s = re.sub(r"(Girls)\s*(Girls)\b", r"\1", s)

    return re.sub(r"\s+"," ", s).strip()

def parse_date_sa(s):
    if s is None: return None
    raw = str(s).strip()
    if raw == "" or raw.lower() in ["nan","none"]: return None
    if re.fullmatch(r"\d+(\.\d+)?", raw):
        try:
            n = float(raw)
            if n > 30000:
                base = datetime(1899, 12, 30)
                return base + timedelta(days=int(n))
        except:
            pass
    cleaned = raw.replace(".", "/").replace("-", "/")
    cleaned = re.sub(r"\s+"," ", cleaned)
    d = pd.to_datetime(cleaned, dayfirst=True, errors="coerce")
    if not pd.isnull(d): return d.to_pydatetime()
    d2 = pd.to_datetime(cleaned, dayfirst=False, errors="coerce")
    if not pd.isnull(d2): return d2.to_pydatetime()
    return None

def format_date_long_sa(s) -> str:
    dt = parse_date_sa(s)
    if not dt:
        return str(s or "").strip()
    return f"{dt.day} {dt.strftime('%B %Y')}"

VENUE_MAP = {
    "bondev": "Bondev Field",
    "veld": "Field",
    "saal": "Hall",
    "ouditorium": "Auditorium",
    "netbal bane": "Netball Courts",
    "tennis bane": "Tennis Courts",
    "swembad": "Swimming Pool",
    "cricket oval": "Cricket Oval",
    "skaak": "Chess",
    "musiekkamer": "Music Room",
    "musiek kamer": "Music Room",
}

def normalize_venue(v: str) -> str:
    s = str(v or "").strip().replace("_", " ")
    s = re.sub(r"\s+"," ", s)
    sl = s.lower()
    if "see programme" in sl or "see program" in sl or "sien program" in sl or "sien programme" in sl:
        return "SEE_PROGRAMME"
    for k, vv in VENUE_MAP.items():
        if k in sl:
            return vv
    return s

def expand_group_range(raw: str, kind: str):
    s = str(raw or "").strip().replace(" ", "")
    if not s:
        return []
    s = s.replace("–", "-").replace("to", "-").replace("TO", "-")
    nums = re.findall(r"\d+", s)
    if len(nums) >= 2 and "-" in s:
        lo, hi = sorted([int(nums[0]), int(nums[1])])
        if kind == "U":
            return [f"U{i}" for i in range(lo, hi + 1)]
        return [f"Gr {i}" for i in range(lo, hi + 1)]
    if kind == "U":
        if s.lower().startswith("u"):
            return [f"U{re.findall(r'\\d+', s)[0]}"] if re.findall(r"\d+", s) else []
        return [f"U{nums[0]}"] if nums else []
    else:
        if s.lower().startswith("gr"):
            return [f"Gr {re.findall(r'\\d+', s)[0]}"] if re.findall(r"\d+", s) else []
        return [f"Gr {nums[0]}"] if nums else []

def format_group_for_row(cat_norm: str, act_norm: str, j_raw: str, l_raw: str):
    l = str(l_raw or "").strip()
    j = str(j_raw or "").strip()

    if cat_norm == "sport":
        if l:
            matches = expand_group_range(l, "U")
            if len(matches) >= 2:
                return f"{matches[0]}-{matches[-1]}", matches
            return matches[0] if matches else "", matches

        if j:
            matches = expand_group_range(j, "U")
            if len(matches) >= 2:
                return f"{matches[0]}-{matches[-1]}", matches
            return matches[0] if matches else "", matches

        if act_norm.lower() == "athletics":
            m = [f"U{i}" for i in range(7,14)]
            return "U7-U13", m
        if act_norm.lower() == "swimming":
            m = [f"U{i}" for i in range(8,14)]
            return "U8-U13", m

        return "", []

    # Academics/Culture
    if l:
        matches = expand_group_range(l, "Gr")
        if len(matches) >= 2:
            return f"{matches[0]}–{matches[-1]}", matches
        return matches[0] if matches else "", matches

    if j:
        matches = expand_group_range(j, "Gr")
        if len(matches) >= 2:
            return f"{matches[0]}–{matches[-1]}", matches
        return matches[0] if matches else "", matches

    return "", []

def build_title(cat_val: str, b_val: str, c_val: str, j_val: str, l_val: str) -> str:
    cn = normalize_category(cat_val)
    act_norm = normalize_activity(b_val)
    b_txt = norm_gender_words(act_norm)
    c_txt = norm_gender_words(c_val).strip()
    group_disp, _ = format_group_for_row(cn, act_norm, j_val, l_val)
    if not group_disp:
        return f"{b_txt} {c_txt}".strip()
    if cn == "sport":
        return f"{b_txt} {group_disp}{c_txt}".strip()
    return f"{b_txt} {group_disp} {c_txt}".strip()

@st.cache_data(ttl=120)
def load_csv(url: str):
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, timeout=25, headers=headers, allow_redirects=True)
    r.encoding = "utf-8"
    txt = r.text or ""
    if r.status_code != 200 or len(txt) < 20 or "<html" in txt.lower():
        return pd.DataFrame(), txt
    df = pd.read_csv(io.StringIO(txt), dtype=str, engine="python", on_bad_lines="skip").fillna("")
    return df, txt

df, raw_txt = load_csv(CSV_URL)
if df.empty:
    st.error("No data loaded. Check your published CSV link.")
    st.stop()

now_dt = datetime.now(TZ)
today = now_dt.date()

# Column mapping A..L
A_CAT = 0
B_ACT = 1
C_TEAM = 2
D_DATE = 3
E_VEN = 4
F_PROG = 5
G_TEAMLINK = 6
H_CONFIRM = 7
I_INFO = 8
J_GROUP = 9
K_DUR = 10
L_EXTRA = 11

def col(i, default=""):
    if df.shape[1] > i:
        return df.iloc[:, i].astype(str)
    return pd.Series([default]*len(df), dtype=str)

cat_s = col(A_CAT)
act_s = col(B_ACT)
team_s = col(C_TEAM)
date_s = col(D_DATE)
ven_s = col(E_VEN)
prog_s = col(F_PROG)
teamlink_s = col(G_TEAMLINK)
confirm_s = col(H_CONFIRM)
info_s = col(I_INFO)
j_s = col(J_GROUP)
dur_s = col(K_DUR)
l_s = col(L_EXTRA)
# ------------------ TOP TOGGLES ------------------
view_mode = st.radio("View", ["Upcoming", "Next 7 Days", "Term Documents"], horizontal=True)

# ------------------ SIDEBAR FILTERS ------------------
st.sidebar.markdown("## Filters")
category_choice = st.sidebar.multiselect("Category", ["Sport", "Culture", "Academics"], default=[])
search = st.sidebar.text_input("Whole school search", placeholder="Type to filter...")

wanted = {c.lower() for c in category_choice} if category_choice else set()

def row_category_ok(i: int) -> bool:
    if not wanted:
        return True
    cn = normalize_category(cat_s.iloc[i])
    return (("sport" in wanted and cn == "sport") or
            ("culture" in wanted and cn == "culture") or
            ("academics" in wanted and cn == "academics"))

act_opts = sorted({normalize_activity(act_s.iloc[i]) for i in range(len(df)) if str(act_s.iloc[i]).strip() and row_category_ok(i)})
selected_activities = st.sidebar.multiselect("Activity/Subject", act_opts, default=[])

# Age/Grade filters (with ranges)
U_SINGLE = [f"U{i}" for i in range(7, 14)]
U_RANGES = ["U7-U9", "U10-U13", "U7-U13", "U8-U13"]
GR_SINGLE = [f"Gr {i}" for i in range(1, 8)]
GR_RANGES = ["Gr 1–Gr 3", "Gr 4–Gr 6", "Gr 5–Gr 7", "Gr 1–Gr 7"]

show_u = (not wanted) or ("sport" in wanted)
show_gr = (not wanted) or ("culture" in wanted) or ("academics" in wanted)

selected_u = st.sidebar.multiselect("Age Groups (Sport)", U_RANGES + U_SINGLE, default=[]) if show_u else []
selected_gr = st.sidebar.multiselect("Grades (Culture/Academics)", GR_RANGES + GR_SINGLE, default=[]) if show_gr else []

def expand_selected_u(sel):
    out = set()
    for v in sel:
        out.update(expand_group_range(v, "U"))
    return out

def expand_selected_gr(sel):
    out = set()
    for v in sel:
        out.update(expand_group_range(v.replace("–", "-"), "Gr"))
    return out

selected_u_set = expand_selected_u(selected_u)
selected_gr_set = expand_selected_gr(selected_gr)

# ------------------ PER-CARD NEW UPDATE TRACKING ------------------
def row_signature(i: int) -> str:
    parts = [
        cat_s.iloc[i], act_s.iloc[i], team_s.iloc[i], date_s.iloc[i], ven_s.iloc[i],
        prog_s.iloc[i], teamlink_s.iloc[i], confirm_s.iloc[i], info_s.iloc[i],
        j_s.iloc[i], dur_s.iloc[i], l_s.iloc[i]
    ]
    return hashlib.sha256(("||".join(map(str, parts))).encode("utf-8")).hexdigest()

if "row_hashes" not in st.session_state:
    st.session_state.row_hashes = {}
if "row_updated_at" not in st.session_state:
    st.session_state.row_updated_at = {}

# ------------------ FILTER + SORT ------------------
res = []
for i in range(len(df)):
    cn = normalize_category(cat_s.iloc[i])
    act_norm = normalize_activity(act_s.iloc[i])

    if wanted and not ((cn == "sport" and "sport" in wanted) or
                       (cn == "culture" and "culture" in wanted) or
                       (cn == "academics" and "academics" in wanted)):
        continue

    if selected_activities and act_norm not in selected_activities:
        continue

    term_flag = "full term" in str(dur_s.iloc[i]).strip().lower()

    d_raw = str(date_s.iloc[i]).strip()
    d_dt = parse_date_sa(d_raw)

    if d_dt and d_dt.date() < today:
        continue

    if view_mode == "Next 7 Days":
        if not d_dt:
            continue
        if d_dt.date() > (today + timedelta(days=7)):
            continue

    if view_mode == "Term Documents":
        if not term_flag:
            continue
        if d_dt and d_dt.date() < today:
            continue

    group_disp, group_matches = format_group_for_row(cn, act_norm, j_s.iloc[i], l_s.iloc[i])

    if cn == "sport" and selected_u_set:
        if group_matches and not any(x in selected_u_set for x in group_matches):
            continue

    if cn in ["culture", "academics"] and selected_gr_set:
        if group_matches and not any(x in selected_gr_set for x in group_matches):
            continue

    title = build_title(cat_s.iloc[i], act_s.iloc[i], team_s.iloc[i], j_s.iloc[i], l_s.iloc[i])

    if search and search.lower().replace(" ", "") not in title.lower().replace(" ", ""):
        continue

    # Update tracking
    sig = row_signature(i)
    prev = st.session_state.row_hashes.get(i)
    if prev is None:
        st.session_state.row_hashes[i] = sig
        st.session_state.row_updated_at[i] = now_dt
    elif prev != sig:
        st.session_state.row_hashes[i] = sig
        st.session_state.row_updated_at[i] = now_dt

    is_recent_update = False
    t = st.session_state.row_updated_at.get(i)
    if t and (now_dt - t) <= timedelta(hours=6):
        is_recent_update = True

    sort_dt = d_dt if d_dt else datetime(2099, 1, 1)
    res.append({"i": i, "dt": sort_dt, "title": title.lower(), "term": term_flag, "new": is_recent_update})

term_items = sorted([x for x in res if x["term"]], key=lambda x: x["title"])
other_items = sorted([x for x in res if not x["term"]], key=lambda x: (x["dt"], x["title"]))
res_sorted = term_items + other_items

# ------------------ DISPLAY ------------------
st.markdown("## 📅 Events")

if not res_sorted:
    st.info("Nothing matched your filters/search.")
else:
    for item in res_sorted:
        i = item["i"]
        cn = normalize_category(cat_s.iloc[i])
        is_academic = (cn == "academics")
        afr = is_afrikaans_subject(act_s.iloc[i])

        title = build_title(cat_s.iloc[i], act_s.iloc[i], team_s.iloc[i], j_s.iloc[i], l_s.iloc[i])

        # D then L then E
        d_raw = str(date_s.iloc[i]).strip()
        date_line = format_date_long_sa(d_raw) if d_raw else ""

        l_line = str(l_s.iloc[i]).strip().replace("_", " ")
        l_line = re.sub(r"\s+"," ", l_line).strip()

        raw_ven = str(ven_s.iloc[i]).strip()
        ven_norm = normalize_venue(raw_ven)

        prog_link = clean_first_url(prog_s.iloc[i])
        team_val = str(teamlink_s.iloc[i]).strip()
        info_val = str(info_s.iloc[i]).strip().replace("_", " ")
        confirm_link = clean_first_url(confirm_s.iloc[i])

        b_prog = "Documents" if is_academic else "Programme"
        b_team = "Team"
        b_info = "Information"
        b_confirm = "Confirm"

        if afr:
            if is_academic:
                b_prog = "Dokumente"
            b_info = "Inligting"

        venue_line = ""
        extra_prog_button = False
        if ven_norm == "SEE_PROGRAMME":
            extra_prog_button = True
        elif ven_norm:
            q = ven_norm
            if "midstream" in ven_norm.lower():
                q = f"{ven_norm} Midstream College"
            map_url = f"https://www.google.com/maps/search/?api=1&query={q.replace(' ','+')}"
            venue_line = (
                f"<div class='meta'>📍 "
                f"<a href='{map_url}' target='_blank' style='color:#008080;font-weight:900;text-decoration:none;'>"
                f"{safe_txt(ven_norm).upper()}</a></div>"
            )

        notes_parts = []
        if "revue" in (title.lower() + " " + info_val.lower()):
            notes_parts.append("<b>Note:</b><br>Revue")

        if team_val and not is_http(team_val):
            notes_parts.append(f"<b>{safe_txt(b_team)}:</b><br>{safe_txt(norm_gender_words(team_val))}")

        if info_val and not is_http(info_val):
            notes_parts.append(f"<b>{safe_txt(b_info)}:</b><br>{safe_txt(info_val)}")

        notes_block = f"<div class='noteBlock'>{'<br><br>'.join(notes_parts)}</div>" if notes_parts else ""

        btns = []
        if prog_link and is_http(prog_link):
            btns.append((b_prog, prog_link))
        if extra_prog_button and prog_link and is_http(prog_link):
            if not any(lbl.lower() == "programme" for lbl, _ in btns):
                btns.append(("Programme", prog_link))
        if team_val and is_http(team_val):
            btns.append((b_team, clean_first_url(team_val)))
        if info_val and is_http(info_val):
            btns.append((b_info, clean_first_url(info_val)))
        if confirm_link and is_http(confirm_link) and is_form_link(confirm_link):
            btns.append((b_confirm, confirm_link))

        btn_html = ""
        if btns:
            btn_html = "<div class='btnRow'>" + "".join(
                [f"<a class='btn' href='{u}' target='_blank'>{safe_txt(lbl)}</a>" for lbl, u in btns[:4]]
            ) + "</div>"

        ribbon = ""
        if item["new"]:
            ribbon = "<div class='ribbon'><span class='rDot'></span>NEW UPDATE</div>"

        st.markdown(f"""
<div class="card">
  {ribbon}
  <div class="card-title">{safe_txt(title)}</div>
  {f"<div class='meta'>📅 <b>{safe_txt(date_line)}</b></div>" if date_line else ""}
  {f"<div class='meta'>⏱ <b>{safe_txt(l_line)}</b></div>" if l_line else ""}
  {venue_line}
  {notes_block}
  {btn_html}
</div>
""", unsafe_allow_html=True)

st.markdown(
    "<br><center style='font-size:0.85rem;color:#94a3b8;'>LAERSKOOL MIDSTREAM COLLEGE PRIMARY Digital Hub 2026</center>",
    unsafe_allow_html=True
)
