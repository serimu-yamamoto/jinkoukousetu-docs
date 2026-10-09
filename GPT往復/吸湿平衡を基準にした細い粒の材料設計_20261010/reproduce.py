from pathlib import Path
import json,math,sys,hashlib,os
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;R=D.parents[1];sys.path.insert(0,str(R/'計算部品'))
from slab_moisture_response import uptake,time_to_fraction,pulse_remaining,finite_volume
a=json.loads((D/'inputs.json').read_text());h=a['hypothetical'];s=a['source'];checks=[]
def ck(n,b):
 if not b:raise AssertionError(n)
 checks.append(n)
def close(x,y):return math.isclose(x,y,rel_tol=1e-9,abs_tol=1e-12)
ck('zero uptake',uptake(0)==0);ck('long-time saturation',uptake(10)==1)
for bad in [-1,float('nan'),float('inf')]:
 try:uptake(bad)
 except ValueError:checks.append('reject invalid Fo '+str(bad))
 else:raise AssertionError('invalid accepted')
rows=[];times=[];pulses=[]
baseD=s['PEEK_table_D_mm2_h']
for thick in h['full_thicknesses_mm']:
 for fac in h['D_relative_to_reported']:
  d=baseD*fac;last=-1
  for hours in h['exposure_hours']:
   u=uptake(d*hours/thick**2);ck('uptake bounded monotone '+str((thick,fac,hours)),0<=u<=1 and u>=last);last=u
   rows.append(dict(thickness_mm=thick,D_factor=fac,hours=hours,uptake_fraction=u))
  for frac in h['fractions']:
   t=time_to_fraction(frac,thick,d)
   ck('inverse uptake '+str((thick,fac,frac)),close(uptake(d*t['hours']/thick**2),frac))
   times.append(dict(thickness_mm=thick,D_factor=fac,target_uptake_fraction=frac,**t))
  p=pulse_remaining(h['wet_h'],h['dry_h'],thick,d)
  ck('dry pulse bounds '+str((thick,fac)),0<=p['after_dry_fraction_of_equilibrium']<=p['before_dry_fraction_of_equilibrium'])
  pulses.append(dict(thickness_mm=thick,D_factor=fac,**p))
mesh=[]
for fo in h['Fo_checks']:
 analytic=uptake(fo);errors=[]
 for n in h['fv_cells']:
  f=finite_volume(fo,n);err=abs(f-analytic);errors.append(err)
  ck('FV bounded '+str((fo,n)),0<=f<=1)
  mesh.append(dict(Fo=fo,cells=n,series=analytic,finite_volume=f,absolute_error=err))
 ck('FV finest tolerance '+str(fo),errors[-1]<5e-5)
 ck('FV convergence '+str(fo),errors[-1]<errors[0])
ck('short time asymptote',abs(uptake(.001)-4*math.sqrt(.001/math.pi))<1e-12)
ref=time_to_fraction(.9,.03,baseD)['hours']
scales=[]
for m in h['thickness_multipliers']:
 t=time_to_fraction(.9,.03*m,baseD)['hours']
 ck('squared thickness scaling '+str(m),close(t/ref,m*m))
 scales.append(dict(thickness_multiplier=m,diffusion_time_ratio=m*m,same_width_length_beam_stiffness_ratio=m**3,same_width_length_mass_ratio=m))
for fac in h['D_relative_to_reported']:
 ck('inverse D scaling '+str(fac),close(time_to_fraction(.9,.03,baseD*fac)['hours']*fac,ref))
q=a['table_audit']
def reconstruct(thick,slope,sat):return math.pi/16*(thick*slope/sat)**2
dc=reconstruct(q['h_composite_mm'],q['composite_kprime_reported'],q['composite_Mm_percent'])
dcprose=reconstruct(q['h_composite_mm'],q['composite_kprime_reported'],q['composite_Mm_prose_percent'])
dp=reconstruct(q['PEEK_h_for_audit_only_mm'],q['PEEK_kprime_reported'],s['PEEK_equilibrium_mass_gain_percent'])
audit=dict(composite_reconstructed_D_mm2_h=dc,composite_ratio_to_table=dc/q['composite_D_reported_mm2_h'],
 composite_with_prose_saturation_D=dcprose,composite_ratio_with_prose_saturation=dcprose/q['composite_D_reported_mm2_h'],
 composite_implied_h_mm=4*q['composite_Mm_percent']/q['composite_kprime_reported']*math.sqrt(q['composite_D_reported_mm2_h']/math.pi),
 PEEK_hypothetical_2mm_D_mm2_h=dp,PEEK_reported_to_hypothetical_ratio=baseD/dp,PEEK_implied_h_mm=4*s['PEEK_equilibrium_mass_gain_percent']/q['PEEK_kprime_reported']*math.sqrt(baseD/math.pi),
 conclusion="Published slope, thickness, units and saturation need author clarification. No corrected material D assigned.")
ck('composite values not identical under either saturation entry',not close(dc,q['composite_D_reported_mm2_h']) and not close(dcprose,q['composite_D_reported_mm2_h']))
ck('no measured strain invented',s['linear_swelling_strain'] is None)
ck('temperature moisture confounding retained',s['immersion'] is False and s['PEEK_grade'] is None)
out=dict(cycle=131,physical_trials=0,success_probability=None,rows=rows,times=times,pulses=pulses,mesh=mesh,thickness_tradeoff=scales,table_audit=audit,
 dependency_hashes={p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in a['dependencies']},
 interpretation="Conditional dimension/time and audit results, no material pass or 50C prediction")
val=dict(count=len(checks),passed=True,checks=checks,physical_trials=0,success_probability=None)
def enc(v):return json.dumps(v,ensure_ascii=False,indent=2)+'\n'
if '--check' in sys.argv:
 assert (D/'results.json').read_text()==enc(out)
 assert (D/'validation.json').read_text()==enc(val)
else:
 (D/'results.json').write_text(enc(out),encoding='utf-8',newline='\n')
 (D/'validation.json').write_text(enc(val),encoding='utf-8',newline='\n')
print(json.dumps(dict(checks=len(checks),conditions=len(rows),times=len(times),pulse_conditions=len(pulses),max_fine_error=max(x['absolute_error'] for x in mesh if x['cells']==512),t90_reference_minutes=ref*60,table_audit=audit,selected_times=[x for x in times if x['target_uptake_fraction']==.9 and x['D_factor']==1],selected_pulses=[x for x in pulses if x['D_factor']==.1]),ensure_ascii=False))
