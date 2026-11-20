"""Usage: python3 scripts/replay_workflow.py. Deterministic routing simulation; no live API."""
import json
from pathlib import Path
def replay(results):
 trace=['orchestrator: start'];calls=0
 for result in results[:2]:
  calls+=1;trace.append('retriever: lookup attempt '+str(calls))
  if result.get('error'):
   trace.append('orchestrator: '+result['error'])
   if calls==1:trace.append('orchestrator: retry once');continue
   trace.append('orchestrator: stop; escalate to human; no draft');return trace
  required={'order_id','status','eta','source_ids'}
  if not required.issubset(result):return trace+['validator: invalid contract; stop; no draft']
  trace+=['validator: fields present; compare facts with source','drafter: draft from validated source only','reviewer: check claims','human: approval required before any communication'];return trace
 return trace+['orchestrator: no usable result; stop']
if __name__=='__main__':
 root=Path(__file__).resolve().parents[1];f=json.loads((root/'data/tool-fixtures.json').read_text())
 success=replay([f['success']]);failure=replay([f['timeout'],f['timeout']])
 print('SIMULATION — supplied tool results, no live calls')
 print(json.dumps({'success':success,'timeout':failure},indent=2))
 assert sum('lookup attempt' in t for t in failure)==2
 assert not any(t.startswith('drafter:') for t in failure)
 print('RESULT: ROUTING CHECKS PASS')
