from pathlib import Path
import json, math
D=Path(__file__).resolve().parent
load=lambda n:json.loads((D/n).read_text(encoding='utf-8'))
I=load('inputs.json'); M=load('mobility_results.json'); P=load('path_results.json'); C=load('correction_results.json')
checks=[]
def ck(name, condition):
 if not condition:raise AssertionError(name)
 checks.append(name)
for name,obj in [('input',I),('mobility',M),('paths',P),('correction',C)]:
 ck(name+'-not-experiment',obj['physical_tests']==0 and obj['success_probability'] is None)
ck('128-lp',len(M['mobility'])==128)
ck('32-relief',len(M['relief'])==32)
ck('36-sensitivity',len(M['rotation_sensitivity'])==36)
ck('12-independent-lp',len(M['independent_lp'])==12 and max(x['error'] for x in M['independent_lp'])<1e-7)
ck('15-original-endpoints',len(P['rows'])==15)
ck('7-correction-endpoints',len(C['corrected_path_endpoints'])==7)
ck('6-contact-refinement',len(C['refined_contact_mobility'])==6)
for label,rows,tol,maxnodes in [('original',P['rows'],.05,80000),('corrected',C['corrected_path_endpoints'],.01,160000)]:
 for j,r in enumerate(rows):
  ck(f'{label}-{j}-not-continuous-proof',r['continuous_free_path_proven'] is False)
  ck(f'{label}-{j}-three-neighbors',len(r['support_distances'])==3)
  for k,q in enumerate(r['support_distances']):
   lo=q['clearance_lower_mm'];hi=q['clearance_upper_mm']
   ck(f'{label}-{j}-{k}-ordered-bounds',lo<=hi)
   ck(f'{label}-{j}-{k}-bound-width',0<=1000*(hi-lo)<=tol*(1+1e-8))
   ck(f'{label}-{j}-{k}-gap-unit',abs(q['certificate_gap_um']-1000*(hi-lo))<1e-10)
   ck(f'{label}-{j}-{k}-completed-within-limit',q['nodes']<=maxnodes)
for r in P['rows']:
 if r['travel_mm']==.02:ck('end-collision-'+r['model'],min(q['clearance_upper_mm'] for q in r['support_distances'])<-.0001)
rs=C['corrected_path_endpoints'];selected=[r for r in rs if r['sideways_per_forward']==-.1 and r['travel_mm']>0]
ck('four-positive-sampled-endpoints',len(selected)==4 and all(r['all_endpoint_lower_bounds_clear'] for r in selected))
ck('initial-overlap-not-hidden',min(q['clearance_upper_mm'] for q in rs[0]['support_distances'])<0)
for r in rs:
 ck('prescribed-side-'+str(r['sideways_per_forward'])+'-'+str(r['travel_mm']),abs(r['center_mm'][1]-r['sideways_per_forward']*r['travel_mm'])<1e-15)
f=C['manufacturing'];a=.022;R=.24
arc_length=3*(7*math.pi/6)*R
vol=math.pi*a*a*arc_length+4*math.pi*a**3
ck('volume-independent-expression',abs(vol-f['volume_sum_upper_mm3'])<1e-15)
ck('mass-mm3-to-kg',abs(vol*960/1e9-f['particle_mass_upper_kg'])<1e-20)
ck('inventory-count-product',abs(f['particle_count_lower']*f['particle_mass_upper_kg']-135000)<1e-8)
ck('factory-count-product',abs(f['minimum_grains_per_second']*3600000-f['particle_count_lower'])<.02)
ck('serial-mass-product',abs(f['serial_10000_per_second_max_kg_per_1000h']-10000*3600000*f['particle_mass_upper_kg'])<1e-9)
ck('individual-processing-shortfall',f['serial_10000_per_second_max_kg_per_1000h']<144)
out={'passed':True,'checks':len(checks),'names':checks,'physical_tests':0,'success_probability':None,'scope':'Stored-output bounds, units, flags and manufacturing identities; not an independent collision solver or physical test.'}
(D/'audit_results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({k:out[k] for k in ['passed','checks','physical_tests','success_probability']}))
