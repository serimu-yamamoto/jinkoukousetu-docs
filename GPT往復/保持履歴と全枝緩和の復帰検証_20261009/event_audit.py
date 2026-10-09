from reproduce import simulate,P
import json
base=json.loads((P/'results.json').read_text(encoding='utf-8'))
rows=[]
for x in [1.3,1.5]:
 for mode in ['vertical_SLS','all_SLS']:
  old=next(r for r in base['cases'] if r['lambda']==.2501 and r['X_initial']==x and r['hold_T']==10 and r['mode']==mode)
  new=simulate(.2501,.5,x,10,mode,max_step=.0025)
  error=abs(old['first_zero_T']-new['first_zero_T'])/new['first_zero_T']
  assert error<2e-5
  rows.append({'X_initial':x,'mode':mode,'original_first_zero_T':old['first_zero_T'],'max_step_0_0025_first_zero_T':new['first_zero_T'],'relative_difference':error,'passed':True})
obj={'purpose':'check possible missed oscillatory zero crossings in four reported cases; not a material test','checks':rows,'all_passed':all(r['passed'] for r in rows)}
(P/'event_audit.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'event_checks':len(rows),'all_passed':obj['all_passed']}))
