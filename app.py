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
 s=str(a).strip()
 if re.search(r'(?i)\b(EAT|Afrikaans EAT)\b',s):t=t.replace(a,"Afrikaans Eerste Addisionele Taal")
 elif re.search(r'(?i)\b(HT|Afrikaans HT)\b',s):t=t.replace(a,"Afrikaans Hooftaal")
 if any(k in s.lower() for k in ["afrikaans","eat","ht"]):return t
 d={"Saal":"Hall","Veld":"Field","Atletiek":"Athletics","Wiskunde":"Math"}
 for k,v in d.items():t=re.sub(rf'\b{k}\b',v,t,flags=re.IGNORECASE)
 return t
@st.cache_data(ttl=10)
def ld():
 r=requests.get(f"{U}&cb={datetime.now().timestamp()}",timeout=5)
 return pd.read_csv(io.StringIO(r.content.decode('utf-8')),dtype=str).fillna("")
df=ld()
if not df.empty:
 st.markdown("<div style='background:white;padding:20px;border-radius:12px;border:1px solid #eee;'>",unsafe_allow_html=True)
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
   elif "eat" in lo or "eerste addisionele" in lo:clo.add("Afrikaans Eerste Addisionele Taal")
   elif "ht" in lo or "hooftaal" in lo:clo.add("Afrikaans Hooftaal")
   else:clo.add(o)
  sa=st.multiselect("Activity",sorted(list(clo)))
 with c3:
  al=["Gr 1","Gr 2","Gr 3","Gr 4","Gr 5","Gr 6","Gr 7","U7","U8","U9","U10","U11","U12","U13"]
  sg=st.multiselect("Age Group",al)
 sq=st.text_input("Search")
 if st.button("REFRESH HUB"):st.cache_data.clear();st.rerun()
 st.markdown("</div>",unsafe_allow_html=True)
 today=datetime.now(pytz.timezone('Africa/Johannesburg')).date()
 tn=set()
 for s in sg:
  ns=re.findall(r'\d+',s)
  if ns:nv=int(ns[0]);tn.add(nv);tn.add(nv-6 if nv>=7 else nv+6)
 res=[]
 for _,r in df.iterrows():
  n,cat=str(r.iloc[3]),str(r.iloc[2]).lower()
  dn="Athletics" if "athletics" in n.lower() else ("Hockey" if "hockey" in n.lower() else n)
  if "eat" in n.lower() or "eerste addisionele" in n.lower():dn="Afrikaans Eerste Addisionele Taal"
  elif "ht" in n.lower() or "hooftaal" in n.lower():dn="Afrikaans Hooftaal"
  cm=True
  if sc:cm=any(x.lower() in cat for x in sc) or ("Academics" in sc and "academic" in cat)
  if not cm or (sa and dn not in sa):continue
  dt=pd.to_datetime(cl(r.iloc[5]),dayfirst=True,errors='coerce')
  ft="full term" in str(r.iloc[12]).lower()
  if (not ft and pd.notnull(dt) and dt.date()<today):continue
  if tn and not any(x in n.lower() for x in ["swimming","athletics"]):
   v_n=re.findall(r'\d+',cl(r.iloc[11]))
   if not(v_n and int(v_n[0]) in tn):continue
  res.append({'r':r,'dt':dt if pd.notnull(dt) else datetime.max.replace(tzinfo=None),'n':n.lower(),'ft':ft,'dd':dt.strftime('%d %B %Y') if pd.notnull(dt) else cl(r.iloc[5])})
 res.sort(key=lambda x:(not x['ft'],x['dt'],x['n']))
 h="<style>body{font-family:sans-serif;}.card{background:white;padding:15px;border-radius:12px;border-left:8px solid #800000;margin-bottom:12px;box-shadow:0 2px 5px rgba(0,0,0,0.1);}.title{color:#800000;font-size:1.1rem;font-weight:bold;}.v-link{color:#008080;text-decoration:none;font-weight:bold;text-transform:uppercase;}.btn{background:#800000;color:white!important;padding:6px 10px;border-radius:6px;text-decoration:none;font-size:0.7rem;display:inline-block;margin:5px 5px 0 0;}</style>"
 for i in res:
  r,f,ds=i['r'],i['ft'],i['dd']
  cv,act,age=str(r.iloc[2]).lower(),str(r.iloc[3]),cl(r.iloc[11])
  ia="afrikaans" in act.lower()
  ic="academic" in cv or any(x in act.lower() for x in ["math","science","wiskunde"])
  b1="Dokumente" if ia else ("Document" if ic else "Programme")
  b2="Assessment" if ic or ia else "Team List"
  btns="".join([f"<a href='{r.iloc[j]}' target='_blank' class='btn'>{b1 if j==7 else b2}</a>" for j in [7,8] if "http" in str(r.iloc[j]).lower()])
  t_s=f"{tr(act,act)} {('U' if 'sport' in cv else 'Gr ')+age+' ' if age else ''}{tr(cl(r.iloc[4]),act)}".strip()
  if sq and sq.lower() not in t_s.lower():continue
  vv,vh=cl(r.iloc[6]),""
  if vv:vh=f"<div style='margin-top:5px;'>📍 <a href='https://www.google.com/maps/search/?api=1&query={vv.replace(' ','+')}+Midstream' target='_blank' class='venue-link' style='color:#008080;text-decoration:none;font-weight:bold;font-size:0.85rem;'>{tr(vv,act).upper()}</a></div>"
  h+=f"<div class='card'><div class='title'>{t_s}</div><div>📅 {'FULL TERM' if f else ds}</div>{vh}<div>{btns}</div></div>"
 v1.html(h,height=3000,scrolling=True)
st.markdown("<center style='font-size:0.7rem;color:#999;'>LMCP Digital Hub 2026</center>",unsafe_allow_html=True)
