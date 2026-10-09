from pathlib import Path
import sys,json,math,hashlib,itertools
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;R=D.parents[1];sys.path.insert(0,str(R/'計算部品'))
from vibration_dwell import *
dep='GPT往復/温暖形成と開放環粒の製造監査_20261010/results.json'
prior=json.loads((R/dep).read_text());g=prior['geometry'];target=(g['R_mm']+g['r_mm'])/1000
inp=json.loads((D/'inputs.json').read_text());p=inp['reported'];a=inp['assumed'];checks=[]
def ck(n,v):
 if not v:raise AssertionError(n)
 checks.append(n)
def close(x,y):return math.isclose(x,y,rel_tol=1e-10,abs_tol=1e-10)
ref=vibration(p['source_diameter_centerline_m'],p['source_amplitude_m'],p['source_frequency_hz'],p['g_m_s2'])
scaled=[scaled_kinematics(ref,d,p['example_event_s']) for d in [target,*a['other_comparison_diameters_m']]]
for v in scaled:
 ck('equal amplitude/diameter '+str(v['diameter_m']),close(v['amplitude_over_diameter'],ref['amplitude_over_diameter']))
 ck('equal peak acceleration/g '+str(v['diameter_m']),close(v['peak_acceleration_over_g'],ref['peak_acceleration_over_g']))
 ck('equal cycle count '+str(v['diameter_m']),close(v['frequency_hz']*v['matched_cycle_duration_s'],p['example_event_s']*p['source_frequency_hz']))
 ck('velocity square-root scaling '+str(v['diameter_m']),close(v['peak_velocity_m_s']/ref['peak_velocity_m_s'],math.sqrt(v['length_scale'])))
same_controls=vibration(target,p['source_amplitude_m'],p['source_frequency_hz'])
ck('same controls keep acceleration',close(same_controls['peak_acceleration_over_g'],ref['peak_acceleration_over_g']))
ck('same controls change relative amplitude',not close(same_controls['amplitude_over_diameter'],ref['amplitude_over_diameter']))
ck('prior mean diameter',close(target,.0017))
rows=[]
for v in scaled:
 for L,speed in itertools.product(a['footprints_m'],a['speeds_m_s']):
  r=moving_dwell(L,speed,v['frequency_hz'],a['course_length_m'],a['operating_fraction'],a['overhead_min'])
  r['comparison_diameter_m']=v['diameter_m'];rows.append(r)
  ck('path length closure '+str((v['diameter_m'],L,speed)),close(r['local_dwell_s']*speed,L))
  ck('oscillation count '+str((v['diameter_m'],L,speed)),close(r['local_cycles']/r['local_dwell_s'],v['frequency_hz']))
target_case=scaled[0]
budgets=[dict(footprint_m=L,**dwell_budget(a['course_length_m'],a['closure_budget_min'],a['overhead_min'],a['operating_fraction'],target_case['matched_cycle_duration_s'],L)) for L in a['footprints_m']]
for b in budgets:
 ck('budget time boundary '+str(b['footprint_m']),close(moving_dwell(b['footprint_m'],b['minimum_travel_speed_m_s'],target_case['frequency_hz'],a['course_length_m'],a['operating_fraction'],a['overhead_min'])['course_closure_min'],a['closure_budget_min']))
 ck('event dwell boundary '+str(b['footprint_m']),close(b['footprint_m']/b['speed_for_comparison_event_m_s'],target_case['matched_cycle_duration_s']))
for func,args in [(vibration,(0,.001,20)),(moving_dwell,(1,.6,20,1000,1.1,22)),(dwell_budget,(1000,60,60,.75,3,1))]:
 try:func(*args)
 except ValueError:ck('invalid input '+str(args),True)
 else:raise AssertionError('invalid accepted')
data=dict(cycle=117,physical_trials=0,success_probability=None,dependency_hashes={dep:hashlib.sha256((R/dep).read_bytes()).hexdigest()},
 inherited_length_scale=dict(R_mm=g['R_mm'],r_mm=g['r_mm'],mean_ring_diameter_m=target,note="Dimensional comparison only; prior two-ring six-web shape is not a C-particle"),
 source_kinematics=ref,scaled_kinematic_comparisons=scaled,same_controls_counterexample=same_controls,machine_scenarios=rows,closure_budgets=budgets,
 caveats=["No threshold, bond kinetics or shear stress inferred","No stiffness friction density water or confinement similarity established","Local dwell is not full course closure","Source example8s is not required/adequate grooming time","Roller acceleration reaching bed depth unknown"])
v=dict(count=len(checks),checks=checks,passed=True,physical_validation=False,scope="Kinematic scaling and timing identities only")
def enc(x):return (json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
for name,obj in [('results.json',data),('validation.json',v)]:
 if '--check' in sys.argv:assert (D/name).read_bytes()==enc(obj)
 else:(D/name).write_bytes(enc(obj))
print(json.dumps(dict(checks=len(checks),source=ref,scaled_reference=target_case,same_controls=same_controls,
 selected_dwell=[r for r in rows if r['comparison_diameter_m']==target and r['speed_m_s_assumed']==.6],budgets=budgets)))
