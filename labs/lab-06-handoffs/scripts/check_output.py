"""Usage: python3 scripts/check_output.py outputs/model-output.json. Partial automated check; human review is mandatory."""
import json,sys,re
from pathlib import Path
def check(n,d):
 issues=[]
 def need(ok,msg):
  if not ok:issues.append(msg)
 if n in (1,2):
  need(d.get('order_id')=='M101','order_id must be M101');need(d.get('status')=='in_transit','status must match O101');need(d.get('eta','missing') is None,'eta must be null');need(d.get('needs_review') is True,'needs_review must be true')
  need({'O101','P1'}.issubset(set(d.get('source_ids',[]))),'source IDs must include O101 and P1')
  replies=[d.get('reply','')] if n==1 else d.get('drafts',[])
  need(len(replies)==(1 if n==1 else 2),'wrong number of replies')
  for s in replies:
   need(bool(re.search(r'unconfirm|unknown|not.{0,20}(confirm|available)|no.{0,20}(confirm|ETA)|cannot.{0,20}confirm',s,re.I)),'reply must preserve unknown ETA')
   need(not re.search(r'tomorrow|2026-\d\d-\d\d|refund.{0,15}approved',s,re.I),'possible invented promise')
 elif n==3:
  need(bool(d.get('diagnosis')) and bool(d.get('changed_element')) and bool(d.get('revised_prompt')),'diagnosis, edit and revised prompt required')
  tests={x.get('order_id'):x for x in d.get('tests',[])}
  need(tests.get('M101',{}).get('eta','missing') is None,'M101 proposed eta must be null')
  need(tests.get('M102',{}).get('eta')=='2026-11-23','M102 proposed eta must preserve date')
  need(tests.get('M101',{}).get('needs_review') is True,'M101 unknown ETA must require human review')
  need(tests.get('M101',{}).get('status')=='in_transit','M101 status must match source')
  need(tests.get('M102',{}).get('status')=='delayed','M102 status must match source')
 elif n==4:
  need(len(d.get('findings',[]))==2,'evaluate both responses')
  for k in ['performance_tradeoff','impact','recommendation','no_use_condition','limitations']:need(bool(d.get(k)),k+' required')
 elif n==5:
  need(d.get('max_revisions')==2,'two-revision limit required')
  for k in ['critique','candidate_prompt','evaluation_plan','stop_conditions','rollback','human_gate','decision']:need(bool(d.get(k)),k+' required')
  stops=json.dumps(d.get('stop_conditions',[])).lower()
  need(bool(re.search(r'no.{0,30}(improv|progress)|stagn|stall',stops)),'stop on no improvement/progress required')
  need(bool(re.search(r'regress|new.{0,30}(fail|error)|critical.{0,30}(wors|fail)',stops)),'stop on regression/new critical failure required')
  need('prompt' in json.dumps(d.get('evaluation_plan',[])).lower(),'evaluation plan must optimise and retest the object prompt')
 elif n==6:
  need(len(d.get('roles',[]))>=3,'retriever, drafter and reviewer required')
  need(d.get('retry_limit')==1,'one retry maximum')
  for k in ['handoff_schema','success_replay','timeout_replay','human_gate','monitoring']:need(bool(d.get(k)),k+' required')
  sc=d.get('handoff_schema',{});props=sc.get('properties',{});required=set(sc.get('required',[]));fields={'order_id','status','eta','source_ids','needs_review','error'}
  need(fields.issubset(required) and fields.issubset(props),'all required handoff fields must be defined and required')
  def types(v):
   t=v.get('type',[]);out=set(t if isinstance(t,list) else [t])
   for k in ['anyOf','oneOf']:
    for x in v.get(k,[]):out|=types(x)
   return out
  need({'string','null'}.issubset(types(props.get('eta',{}))),'ETA must allow string and null')
  need({'object','null'}.issubset(types(props.get('error',{}))),'error must allow object and null')
  need(set(props.get('status',{}).get('enum',[]))=={'in_transit','delivered','delayed','unknown'},'status enum must match the contract')
  need(props.get('needs_review',{}).get('type')=='boolean','needs_review must be boolean')
 return issues
if __name__=='__main__':
 root=Path(__file__).resolve().parents[1];n=int(root.name.split('-')[1]);p=Path(sys.argv[1] if len(sys.argv)>1 else 'outputs/model-output.json')
 try:
  raw=p.read_text();raw=re.sub(r'^```(?:json)?\s*|\s*```$','',raw.strip());d=json.loads(raw);issues=check(n,d)
 except Exception as e:issues=[str(e)]
 for i in issues:print('CHECK:',i)
 print('Human review still required: source grounding, semantic accuracy and complete lab evidence.')
 print('RESULT: '+('AUTOMATED CHECKS PASS' if not issues else 'REVIEW REQUIRED'))
 sys.exit(bool(issues))
