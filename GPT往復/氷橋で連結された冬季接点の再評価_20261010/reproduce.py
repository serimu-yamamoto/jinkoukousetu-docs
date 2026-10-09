from pathlib import Path
import json,sys,math,hashlib
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;R=D.parents[1];sys.path.insert(0,str(R/'計算部品'))
from shrinkage_patches import analytic,geometry
from linked_shrinkage_patches import condensed,full_fe
a=json.loads((D/'inputs.json').read_text());h=a['hypothetical'];checks=[]
def ck(n,b):
 if not b:raise AssertionError(n)
 checks.append(n)
def eq(x,y):return math.isclose(x,y,rel_tol=1e-7,abs_tol=1e-10)
E=h['E_Pa'];t=h['thickness_m'];eps=h['natural_shrink_strain'];L=h['face_length_m'];gap=h['gap_m'];lam=h['transfer_length_m'];k=E*t/lam**2
prior=json.loads((R/a['reused_cycle129_inputs']).read_text())['hypothetical']
for key in ['E_Pa','thickness_m','natural_shrink_strain','face_length_m','gap_m']:ck('prior same '+key,prior[key]==h[key])
rows=[];baselines={};thresholds=[]
for qbar in h['footprint_shear_loads_Pa']:
 base=analytic(E,t,k,eps,L/2,qbar);baselines[str(qbar)]=base
 for N in h['counts']:
  g=geometry(L,gap,N);p=g['half_patch_m'];q=qbar/g['coverage'];free=analytic(E,t,k,eps,p,q);weld=analytic(E,t,k,eps,g['wet_length_m']/2,q)
  last_energy=None;last_peak=None
  for beta in h['bridge_ratios']:
   label=str((qbar,N,beta));x=condensed(E,t,k,eps,L,gap,N,beta,qbar)
   ck('global force balance '+label,abs(x['shrink_reaction_N_per_m_width'])<2e-8)
   ck('bridges in tension '+label,all(v>=-1e-12 for v in x['bridge_extensions_m']))
   ck('positive energies '+label,0<=x['bridge_stored_J_per_m_width']<=x['total_stored_J_per_m_width'])
   ck('endpoint antisymmetry '+label,max(abs(v+w) for v,w in zip(x['endpoint_w_m'],reversed(x['endpoint_w_m'])))<1e-10)
   if last_energy is not None:
    ck('constraint raises energy '+label,x['total_stored_J_per_m_width']>=last_energy-1e-10)
    ck('constraint raises interface peak '+label,x['peak_interface_shear_Pa']>=last_peak-1e-7)
   last_energy=x['total_stored_J_per_m_width'];last_peak=x['peak_interface_shear_Pa'];meshes=[]
   for n in h['mesh_elements_per_patch']:
    y=full_fe(E,t,k,eps,L,gap,N,beta,qbar,n)
    err=dict(endpoint=max(abs(xx-yy) for xx,yy in zip(x['endpoint_w_m'],y['endpoint_w_m']))/(abs(eps)*lam),
             peak_shear=abs(y['peak_interface_shear_Pa']/x['peak_interface_shear_Pa']-1),
             peak_stress=abs(y['peak_tensile_Pa']-x['peak_tensile_Pa'])/(E*abs(eps)),
             energy=abs(y['total_stored_J_per_m_width']/x['total_stored_J_per_m_width']-1))
    ck('FE force '+label+str(n),abs(y['shrink_reaction_N_per_m_width'])<2e-8)
    meshes.append(dict(elements_per_patch=n,errors=err))
   ck('fine errors '+label,max(meshes[-1]['errors'].values())<.001)
   ck('refined endpoint '+label,meshes[-1]['errors']['endpoint']<=meshes[0]['errors']['endpoint']+1e-7)
   if beta==0:
    ck('free limit stress '+label,eq(x['peak_tensile_Pa'],free['peak_tensile_Pa']))
    ck('free limit shear '+label,eq(x['peak_interface_shear_Pa'],free['peak_abs_interface_shear_Pa']))
    ck('free limit energy '+label,eq(x['total_stored_J_per_m_width'],N*free['stored_J_per_m_width']))
   if beta==h['bridge_ratios'][-1]:
    ck('weld limit shear '+label,abs(x['peak_interface_shear_Pa']/weld['peak_abs_interface_shear_Pa']-1)<.001)
    ck('weld limit energy '+label,abs(x['total_stored_J_per_m_width']/weld['stored_J_per_m_width']-1)<.001)
   rows.append(dict(footprint_load_Pa=qbar,patch_count=N,beta=beta,compared_to_unsegmented_peak=x['peak_interface_shear_Pa']/base['peak_abs_interface_shear_Pa'],solution=x,meshes=meshes))
  target=base['peak_abs_interface_shear_Pa'];lo=0.;hi=h['bridge_ratios'][-1]
  if condensed(E,t,k,eps,L,gap,N,lo,qbar)['peak_interface_shear_Pa']>=target:
   thresholds.append(dict(footprint_load_Pa=qbar,patch_count=N,status='no initial peak benefit',beta=None))
  elif condensed(E,t,k,eps,L,gap,N,hi,qbar)['peak_interface_shear_Pa']<target:
   thresholds.append(dict(footprint_load_Pa=qbar,patch_count=N,status='no crossing in tested bracket',beta=None))
  else:
   for _ in range(60):
    mid=(lo+hi)/2
    if condensed(E,t,k,eps,L,gap,N,mid,qbar)['peak_interface_shear_Pa']<target:lo=mid
    else:hi=mid
   root=(lo+hi)/2;v=condensed(E,t,k,eps,L,gap,N,root,qbar)['peak_interface_shear_Pa']
   ck('crossing root '+str((qbar,N)),abs(v/target-1)<1e-9)
   thresholds.append(dict(footprint_load_Pa=qbar,patch_count=N,status='conditional equal-peak boundary',beta=root,K_bridge_Pa=root*E*t/L))
ck('finite bridge can reverse benefit',any(r['compared_to_unsegmented_peak']>1 for r in rows if r['footprint_load_Pa']==2000 and r['patch_count']==8))
for args in [(E,t,k,.01,L,gap,8,1,2000),(E,t,k,eps,L,gap,8,-1,2000)]:
 try:condensed(*args)
 except ValueError:ck('invalid input '+str(args[-4:]),True)
 else:raise AssertionError('invalid accepted')
budgets=[]
N=8;qbar=2000;g=geometry(L,gap,N);q=qbar/g['coverage'];ref=condensed(E,t,k,eps,L,gap,N,0,qbar)
for beta in [100.,1e6]:
 x=condensed(E,t,k,eps,L,gap,N,beta,qbar);tau_shrink=x['peak_interface_shear_Pa']-q
 eta=(ref['peak_interface_shear_Pa']-tau_shrink)/q
 strain_factor=ref['peak_tensile_Pa']/x['peak_tensile_Pa']
 bypass=condensed(E,t,k,eps,L,gap,N,beta,qbar*.5)
 low_shrink=condensed(E,t,k,eps*strain_factor,L,gap,N,beta,qbar)
 ck('bypass does not remove tension '+str(beta),eq(bypass['peak_tensile_Pa'],x['peak_tensile_Pa']))
 ck('bypass linear shear change '+str(beta),eq(x['peak_interface_shear_Pa']-bypass['peak_interface_shear_Pa'],q*.5))
 ck('strain target restores tensile level '+str(beta),eq(low_shrink['peak_tensile_Pa'],ref['peak_tensile_Pa']))
 ck('strain target also below shear level '+str(beta),low_shrink['peak_interface_shear_Pa']<=ref['peak_interface_shear_Pa'])
 budgets.append(dict(beta=beta,maximum_wet_path_load_fraction_for_original_free_shear=eta,
                     required_dry_load_path_fraction_for_shear=1-eta,
                     original_shrink_strain_magnitude=abs(eps),
                     shrink_strain_magnitude_for_original_free_tension=abs(eps)*strain_factor,
                     stress_unchanged_by_half_load_bypass_Pa=bypass['peak_tensile_Pa'],
                     low_shrink_peak_shear_Pa=low_shrink['peak_interface_shear_Pa'],
                     limitation='Conditional targets at unchanged E,k,bridge stiffness; material changes may change all coefficients'))
deps=['計算部品/shrinkage_patches.py',a['reused_cycle129_inputs'],'GPT往復/凍結脱水と分割した冬季接点の拘束評価_20261010/model.md','GPT往復/凍結脱水と分割した冬季接点の拘束評価_20261010/sources.json']
data=dict(cycle=130,physical_trials=0,success_probability=None,dependency_hashes={p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in deps},baselines=baselines,cases=rows,conditional_crossings=thresholds,design_budgets=budgets,limits=a['limits'])
v=dict(count=len(checks),passed=True,checks=checks,physical_validation=False)
def enc(x):return (json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
for name,x in [('results.json',data),('validation.json',v)]:
 if '--check' in sys.argv:assert (D/name).read_bytes()==enc(x)
 else:(D/name).write_bytes(enc(x))
print(json.dumps(dict(checks=len(checks),cases=len(rows),max_final_error=max(x for r in rows for x in r['meshes'][-1]['errors'].values()),thresholds=thresholds,budgets=budgets,example=[dict(beta=r['beta'],peak_Pa=r['solution']['peak_interface_shear_Pa'],tension_Pa=r['solution']['peak_tensile_Pa']) for r in rows if r['footprint_load_Pa']==2000 and r['patch_count']==8]),ensure_ascii=False))
