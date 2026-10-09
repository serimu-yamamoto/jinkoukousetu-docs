from pathlib import Path
import json,sys,math,hashlib,itertools
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;R=D.parents[1];sys.path.insert(0,str(R/'計算部品'))
from platelet_exposure import geometry,robust_height_window,rework_inventory
dep='GPT往復/生体分子結晶の接触相と製造物量_20261010/results.json'
prior=json.loads((R/dep).read_text());g=prior['reported_geometry'];L=g['platelet_length_m']*1e9;t=g['platelet_thickness_m']*1e9
a=json.loads((D/'inputs.json').read_text())['assumed'];checks=[]
def ck(n,v):
 if not v:raise AssertionError(n)
 checks.append(n)
def close(x,y):return math.isclose(x,y,rel_tol=1e-10,abs_tol=1e-8)
rows=[]
for angle,d,r in itertools.product(a['angles_deg'],a['recesses_nm'],a['rim_rises_nm']):
 row=geometry(L,t,angle,d,r);rows.append(row)
 # Independent explicit rotation of a rectangular cross-section.
 ang=math.radians(angle);verts=[(x*math.sin(ang)+y*math.cos(ang)) for x,y in [(0,0),(L,0),(0,t),(L,t)]]
 ck('rotated vertices '+str((angle,d,r)),close(max(verts)-min(verts),row['vertical_extent_nm']))
 ck('reference-plane translation '+str((angle,d,r)),close(row['protrusion_above_rim_nm']+d+r,row['vertical_extent_nm']))
windows=[robust_height_window(a['comparison_height_limit_nm'],u) for u in a['vertical_uncertainties_nm']]
for w in windows:
 lo=w['nominal_height_lower_exclusive_nm'];hi=w['nominal_height_upper_inclusive_nm']
 ck('tolerance interval '+str(lo),w['interval_nonempty']==(lo<hi))
masked=geometry(L,t,0,0,0,True);ck('continuous cover masks crystal regardless of elevation',not masked['geometrically_exposed'])
flat=geometry(L,t,0,0);ck('flat thickness',close(flat['vertical_extent_nm'],t))
ck('recess50 buries flat42',not geometry(L,t,0,50)['geometrically_exposed'])
ck('rim rise30 buries flat recessed20',not geometry(L,t,0,20,30)['geometrically_exposed'])
ck('right angle equals length',close(geometry(L,t,90,0)['vertical_extent_nm'],L))
mass=prior['reference_platelet']['net_crystal_kg']
flows=[rework_inventory(mass,y,r) for y,r in itertools.product(a['accepted_fractions'],a['rework_recovery_fractions'])]
for j,f in enumerate(flows):
 ck('fresh mass closure '+str(j),close(f['steady_state_fresh_input_kg'],f['target_kg']+f['final_unrecovered_loss_kg']))
 ck('application mass closure '+str(j),close(f['total_application_throughput_kg'],f['target_kg']+f['rejected_throughput_kg']))
 ck('recovery does not eliminate processing '+str(j),f['total_application_throughput_kg']>=f['steady_state_fresh_input_kg']-1e-9)
for func,args in [(geometry,(L,t,-1,0)),(robust_height_window,(100,-1)),(rework_inventory,(mass,0,.8))]:
 try:func(*args)
 except ValueError:ck('invalid boundary '+str(args),True)
 else:raise AssertionError('Accepted invalid')
data=dict(cycle=116,physical_trials=0,success_probability=None,dependency_hashes={dep:hashlib.sha256((R/dep).read_bytes()).hexdigest()},
 geometry_scenarios=rows,height_windows=windows,continuous_cover_counterexample=masked,rework_scenarios=flows,
 interpretation="Potential geometric exposure only; no load-bearing area, friction, wear, safety or process yield measured.100nm comparison ceiling is arbitrary, not a validated roughness requirement.")
v=dict(count=len(checks),checks=checks,passed=True,physical_validation=False,scope='Rotation geometry, tolerance interval and steady-state rework mass balance')
def enc(x):return (json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
for name,obj in [('results.json',data),('validation.json',v)]:
 if '--check' in sys.argv:assert (D/name).read_bytes()==enc(obj)
 else:(D/name).write_bytes(enc(obj))
print(json.dumps(dict(checks=len(checks),scenarios=len(rows),flat=rows[0],tilt2=geometry(L,t,2,0),tilt5=geometry(L,t,5,0),windows=windows,rework_example=flows[-1])))
