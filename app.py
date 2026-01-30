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
 if re.search(r'(?i)\b(EAT|HT|Hooftaal|Eerste)\b',r):return "Afrikaans "+("Eerste Addisionele Taal" if "eat" in r.lower() or "eerste" in r.lower() else "Hooftaal")
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
  orw=sorted(list(set(df[m].iloc[:,3].str.strip())))
  clo=set()
  for o in orw:
   lo=o.lower()
   if "athletics" in lo:clo.add("Athletics")
   elif "hockey" in lo:clo.add("Hockey")
   elif "eat" in lo or "eerste" in lo:clo.add("Afrikaans Eerste Addisionele Taal")
   elif "ht" in lo or "hooftaal" in lo:clo.add("Afrikaans Hooftaal")
   else:clo.add(o)
  sa=st.multiselect("Activity",sorted(list(clo)))
 with c3:
  # ONS HOU HIERDIE LYS STABIEL SODAT DIT NIE RESET NIE
  al=["Gr 1","Gr 2","Gr 3","Gr 4","Gr 5","Gr 6","Gr 7","U7","U8","U9","U10","U11","U12","U13"]
  sg=st.multiselect("Age Group",al)
 sq=st.text_input("Search")
 st.markdown("</div>",unsafe_allow_html=True)

 today=datetime.now(pytz.timezone('Africa/Johannesburg')).date()
 # --- SMART MAPPING LOGIKA ---
 target_nums = set()
 for s in sg:
  nums = re.findall(r'\d+', s)
  if nums:
   n = int(nums[0])
   target_nums.add(n)
   if n <= 7: target_nums.add(n + 6) # As Gr 4 gekies is, voeg 10 by
   if n >= 7: target_nums.add(n - 6) # As U10 gekies is, voeg 4 by

 res=[]
 for _,r in df.iterrows():
  n,cat,av=str(r.iloc[3]),str(r.iloc[2]).lower(),cl(r.iloc[11])
  dn="Athletics" if "athletics" in n.lower() else ("Hockey" if "hockey" in n.lower() else n)
  if "eat" in n.lower() or "eerste" in n.lower():dn="Afrikaans Eerste Addisionele Taal"
  elif "ht" in n.lower() or "hooftaal" in n.lower():dn="Afrikaans Hooftaal"
  
  cm=any(x.lower() in cat for x in sc) or ("Academics" in sc and "academic" in cat) if sc else True
  if not cm or (sa and dn not in sa):continue
  
  if target_nums:
   row_nums = re.findall(r'\d+', av)
   if not row_nums:
    if not any(x in n.lower() for x in ["athletics","swimming"]): continue
   else:
    if not any(int(rn) in target_nums for rn in row_nums): continue

  rd=cl(r.iloc[5]);dt=pd.to_datetime(rd,dayfirst=True,errors='coerce');ft="full term" in str(r.iloc[12]).lower()
  if not ft and pd.notnull(dt) and dt.date()<today:continue
  res.append({'r':r,'dt':dt if pd.notnull(dt) else datetime.max.replace(tzinfo=None),'n':n.lower(),'ft':ft,'dd':dt.strftime('%d %B %Y') if pd.notnull(dt) else rd})

 res.sort(key=lambda x:(not x['ft'],x['dt'],x['n']))
 h="<style>.card{background:white;padding:12px;border-radius:10px;border-left:8px solid #800000;margin-bottom:10px;box-shadow:0 2px 5px rgba(0,0,0,0.1);font-family:sans-serif;}.title{color:#800000;font-size:1rem;font-weight:bold;}.btn{background:#800000;color:white!important;padding:5px 8px;border-radius:5px;text-decoration:none;font-size:0.7rem;display:inline-block;margin:5px 5px 0 0;}.nt{background:#f0f7f7;padding:6px;margin-top:5px;border-radius:5px;font-size:0.7rem;}</style>"
 for i in res:
  r,f,ds=i['r'],i['ft'],i['dd']
  cv,act,age=str(r.iloc[2]).lower(),str(r.iloc[3]),cl(r.iloc[11])
  ia,ic="afrikaans" in act.lower() or "eat" in act.lower(),"academic" in cv or any(x in act.lower() for x in ["math","science"])
  b1="Dokumente" if ia else ("Document" if ic else "Programme")
  btns="".join([f"<a href='{cl(r.iloc[j])}' target='_blank' class='btn'>{b1 if j==7 else ('Assessment' if ic or ia else 'Team List' if j==8 else 'Information')}</a>" for j in [7,8,10] if "http" in cl(r.iloc[j]).lower()])
  nt=f"<div class='nt'>{cl(r.iloc[10])}</div>" if cl(r.iloc[10]) and "http" not in cl(r.iloc[10]).lower() else ""
  ts=f"{tr(act,act)} {('U' if 'sport' in cv else 'Gr ')+age+' ' if age else ''}{tr(cl(r.iloc[4]),act)}".strip()
  if sq and sq.lower() not in ts.lower():continue
  vv,vh=cl(r.iloc[6]),""
  if vv:vh=f"<div style='margin-top:4px;'>📍 <a href='http://googleusercontent.com/maps.google.com/search?q={vv.replace(' ','+')}+Midstream' target='_blank' style='color:#008080;text-decoration:none;font-weight:bold;font-size:0.8rem;'>{tr(vv,act).upper()}</a></div>"
  h+=f"<div class='card'><div class='title'>{ts}</div><div>📅 {'FULL TERM' if f else ds}</div>{vh}{nt}<div>{btns}</div></div>"
 v1.html(h,height=3000,scrolling=True)
st.markdown("<center style='font-size:0.7rem;color:#999;'>LMCP Digital Hub 2026</center>",unsafe_allow_html=True)
