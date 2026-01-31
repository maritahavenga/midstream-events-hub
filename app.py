import re
import streamlit as st
import pandas as pd

# =============================
# PAGE CONFIG (mobile-friendly)
# =============================
st.set_page_config(page_title="LMCP Event Hub", layout="centered")

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

# =============================
# BRAND
# =============================
MAROON = "#6b0019"
TEAL = "#0f5b66"
BG = "#f6f7fb"
TEAL_SHADE = "#e8f3f5"

# =============================
# CSS (new font + no full-width buttons)
# =============================
st.markdown(
    f"""
<style>
  .stApp {{
    background: {BG};
    /* modern “phone” feel */
    font-family: "Segoe UI Variable", "Segoe UI", system-ui, -apple-system, "SF Pro Display",
                 Roboto, "Helvetica Neue", Arial, sans-serif;
  }}

  section.main > div {{
    max-width: 860px;
  }}

  .lmcp-divider {{
    height: 10px;
    background: linear-gradient(90deg, {MAROON}, {TEAL});
    border-radius: 999px;
    margin: 10px 0 16px 0;
    border: 2px solid rgba(0,0,0,0.06);
  }}

  .lmcp-panel {{
    background: white;
    border-radius: 18px;
    padding: 14px 16px;
    border: 1px solid rgba(0,0,0,0.06);
    box-shadow: 0 8px 16px rgba(0,0,0,0.05);
    margin-bottom: 14px;
  }}

  .lmcp-card {{
    background: white;
    border-radius: 18px;
    padding: 16px;
    border: 1
