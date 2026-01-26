import streamlit as st
import pandas as pd
import re
from datetime import datetime
import pytz
import requests
import io
import time
import html
from streamlit_autorefresh import st_autorefresh

# --------------------------------------------------
# Page Config
# --------------------------------------------------
st.set_page_config(page_title="LMCP Live Fixtures", layout="centered")
st_autorefresh(interval=120000, key="datarefresh")

# --------------------------------------------------
# Styling
# --------------------------------------------------
st.markdown("""
<style>
#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
.stApp{background:#008080}.block-container{padding:1rem;max-width:600px}
.card{background:white!important;padding:18px;border-radius:15px;border-left:12px solid #800000;margin-bottom:15px
