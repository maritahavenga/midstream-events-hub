import streamlit as st
import pandas as pd
import requests
import io,re
from datetime import datetime
import pytz
import streamlit.components.v1 as v1
from streamlit_autorefresh import st_autorefresh
st.set_page_config(page_title="LMCP Hub",layout="centered")
st_autorefresh(interval=120000,key="r")
U="https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"
def cl(v):return str(v).replace(".0","").replace("nan","").strip()
def tr(t,a):
 r=str(a).strip()
 t=t.replace(" G "," Girls ").replace(" G"," Girls")
 if re.search(r'(?i)\b(EAT|HT|Hooftaal|Eerste Addisionele)\b',r):
  return "Afrikaans "+("Eerste Addisionele Taal" if "eat" in r.lower() or "eerste" in r.lower() else "Hooftaal")
 d={"Saal":"Hall","Veld":"Field","Atletiek":"Athletics","Wiskunde":"Math"}
 for k,v in d.items():t=re.sub(rf'\b{k}\b',v,t,flags=re.IGNORECASE)
 return t
@st.cache_data(ttl=10)
def ld():
 try:
  r=requests.get(f"{U}&cb={datetime.now().timestamp()}",timeout=5)
  return pd.read_csv(io.StringIO(r.content.decode('utf-8')),dtype=str).fillna("")
 except:return pd.DataFrame()
df=ld()
if not df.empty:
 st.markdown("<div style='background:white;padding:15px;border-radius:10px;border:1px solid #eee;'>",unsafe_allow_html=True)
 c1,c2,c3=st.columns(3)
 with c1:sc=st.multiselect("Category",["Sport","Culture","Academics"])
 with c2:
  m=df.iloc[:,2].str.contains('|'.join(sc) if sc else ".*",case=False)
  if sc and "Academics" in sc:m|=df.iloc[:,2].str.contains("academic",case=False)
  o_r=sorted(list(set(df[m].iloc[:,3].str.strip())))
  clo=set()
  for o in o_r:
   lo=o.lower()
   if "athletics" in lo:clo.add("Athletics")
   elif "hockey" in lo:clo.add("Hockey")
   elif "tennis" in lo:clo.add("Tennis")
   elif "eat" in lo or "eerste" in lo:clo.add("Afrikaans Eerste Addisionele Taal")
   elif "ht" in lo or "hooftaal" in lo:clo.add("Afrikaans Hooftaal")
   else:clo.add(o)
  sa=st.multiselect("Activity",sorted(list(clo)))
 with c3:
  al=["U7","U8","U9","U10","U11","U12","U13"] if sc==["Sport"] else (["Gr 1","Gr 2","Gr 3","Gr 4","Gr 5","Gr 6","Gr 7"] if sc and "Sport" not in str(sc) else ["Gr 1","Gr 2","Gr 3","Gr 4","Gr 5","Gr 6","Gr 7","U7","U8","U9","U10","U11","U12","U13"])
  sg=st.multiselect("Age Group",al)
 sq=st.text_input("Search")
 st.markdown("</div>",unsafe_allow_html=True)
 today=datetime.now(pytz.timezone('Africa/Johannesburg')).date()
 tn=set()
 for s in sg:
  ns=re.findall(r'\d+',s)
  if ns:
   nv=int(ns[0]);tn.add(nv)
   if nv<=7:tn.add(nv+6)
   else:tn.add(nv-6)
 res=[]
 for _,r in df.iterrows():
  n,cat,av=str(r.iloc[3]),str(r.iloc[2]).lower(),cl(r.iloc[11])
  dn="Athletics" if "athletics" in n.lower() else ("Hockey" if "hockey" in n.lower() else ("Tennis" if "tennis" in n.lower() else n))
  if "eat" in n.lower() or "eerste" in n.lower():dn="Afrikaans Eerste Addisionele Taal"
  elif "ht" in n.lower() or "hooftaal" in n.lower():dn="Afrikaans Hooftaal"
  cm=any(x.lower() in cat for x in sc) or ("Academics" in sc and "academic" in cat) if sc else True
  if not cm or (sa and dn not in sa):continue
  if tn and av:
   v_n=re.findall(r'\d+',av)
   if v_n and int(v_n[0]) not in tn:continue
  rd=cl(r.iloc[5]);dt=pd.to_datetime(rd,dayfirst=True,errors='coerce');ft="full term" in str(r.iloc[12]).lower()
  if not ft and pd.notnull(dt) and dt.date()<today:continue
  res.append({'r':r,'dt':dt if pd.notnull(dt) else datetime.max.replace(tzinfo=None),'n':n.lower(),'ft':ft,'dd':dt.strftime('%d %B %Y') if pd.notnull(dt) else rd})
 res.sort(key=lambda x:(not x['ft'],x['dt'],x['n']))
 h="<style>body{font-family:sans-serif;}.card{background:white;padding:
