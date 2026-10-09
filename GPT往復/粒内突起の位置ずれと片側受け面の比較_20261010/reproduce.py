from pathlib import Path
import sys,json,math,hashlib
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;R=D.parents[1];sys.path.insert(0,str(R/'計算部品'))
from stop_misalignment import circle_overlap,nominal_pressure_multiplier,rearrangement,beam_compliance
from drying_stop_geometry import stop_geometry
a=json.loads((D/'inputs.json').read_text());h=a['assumed'];checks=[]
def ck(n,v):
 if not v:raise AssertionError(n)
 checks.append(n)
def eq(x,y):return math.isclose(x,y,rel_tol=1e-9,abs_tol=1e-20)
def numeric(r,R,d,n):
 lo=max(-r,d-R);hi=min(r,d+R)
 if hi<=lo:return 0.
 def fun(x):
  return 2*min(math.sqrt(max(0.,r*r-x*x)),math.sqrt(max(0.,R*R-(x-d)**2)))
 split=(d*d+r*r-R*R)/(2*d) if d else hi
 knots=[lo]+([split] if lo<split<hi else [])+[hi];total=0.
 for left,right in zip(knots[:-1],knots[1:]):
  dx=(right-left)/n
  total+=(fun(left)+fun(right)+sum((4 if j%2 else 2)*fun(left+j*dx) for j in range(1,n)))*dx/3
 return total
r=h['post_radius_um']*1e-6;land=h['landing_radius_um']*1e-6;patch=math.prod(h['patch_um'])*1e-12;rows=[];errors=[]
baseline=stop_geometry(h['patch_um'][0]*1e-6,h['patch_um'][1]*1e-6,30e-6,100e-6,r,h['height_each_um']*1e-6,h['pairs'])
for du in h['offsets_um']:
 d=du*1e-6;pair=circle_overlap(r,r,d);one=circle_overlap(r,land,d)
 ck('receiving area remains full '+str(du),eq(one,math.pi*r*r))
 ck('circle symmetry '+str(du),eq(circle_overlap(r,land,d),circle_overlap(land,r,d)))
 ck('quadratic area scaling '+str(du),eq(circle_overlap(2*r,2*r,2*d),4*pair))
 if pair>0:
  coarse=numeric(r,r,d,h['simpson_n'][0]);fine=numeric(r,r,d,h['simpson_n'][1])
  e0=abs(coarse/pair-1);e1=abs(fine/pair-1)
  ck('independent area integration '+str(du),e1<1e-5)
  ck('area quadrature convergence '+str(du),e1<e0)
  errors.append(dict(offset_um=du,coarse_relative_error=e0,fine_relative_error=e1))
 p4=nominal_pressure_multiplier(patch,pair,4);p1=nominal_pressure_multiplier(patch,pair,1)
 q4=nominal_pressure_multiplier(patch,one,4);q1=nominal_pressure_multiplier(patch,one,1)
 if p4 is not None:ck('one surviving pair takes quadruple load '+str(du),eq(p1,4*p4))
 ck('one surviving single post takes quadruple load '+str(du),eq(q1,4*q4))
 rows.append(dict(offset_um=du,paired_overlap_fraction=pair/(math.pi*r*r),one_sided_overlap_fraction=one/(math.pi*r*r),paired_pressure_factor4=p4,paired_pressure_factor1=p1,single_pressure_factor4=q4,single_pressure_factor1=q1,contact_lost=pair==0))
ck('zero offset recovers cycle123',eq(rows[0]['paired_pressure_factor4'],baseline['nominal_stop_stress_multiplier']))
ck('2r offset loses paired path',rows[-1]['contact_lost'])
ck('overlap decreases monotonically',all(x['paired_overlap_fraction']>y['paired_overlap_fraction'] for x,y in zip(rows[:-1],rows[1:])))
z=rearrangement(h['height_each_um']*1e-6,r,h['pairs'])
ck('same material inventory',eq(z['paired_volume_m3'],baseline['added_solid_volume_m3']))
ck('lateral flexibility penalty',eq(z['single_lateral_compliance_times_EI']/z['paired_lateral_compliance_times_EI'],4))
ck('receiver footprint9 times post',eq(land**2/r**2,9))
for fun,args in [(circle_overlap,(r,r,-1)),(circle_overlap,(r,float('nan'),0)),(nominal_pressure_multiplier,(1,1,0)),(nominal_pressure_multiplier,(1,-1,1)),(rearrangement,(1,1,1.5))]:
 try:fun(*args)
 except ValueError:ck('invalid '+str(args),True)
 else:raise AssertionError('invalid input accepted')
bh=h['height_each_um']*1e-6;nu=h['poisson'];kap=h['circular_shear_factor']
short=beam_compliance([(bh,r)],nu,kap);single=beam_compliance([(2*bh,r)],nu,kap)
stepped=beam_compliance([(bh,2*r),(bh,r)],nu,kap)
pair={k:2*v for k,v in short.items()}
ck('uniform bending component ratio4',eq(single['bending_times_E']/pair['bending_times_E'],4))
ck('uniform shear component unchanged',eq(single['shear_times_E'],pair['shear_times_E']))
ck('uniform axial component unchanged',eq(single['axial_times_E'],pair['axial_times_E']))
ck('step volume ratio2.5',eq(stepped['volume_m3']/pair['volume_m3'],2.5))
ck('step bending ratio23over32',eq(stepped['bending_times_E']/pair['bending_times_E'],23/32))
ck('step shear ratio5over8',eq(stepped['shear_times_E']/pair['shear_times_E'],5/8))
ck('step axial ratio5over8',eq(stepped['axial_times_E']/pair['axial_times_E'],5/8))
# Independent midpoint integration of bending strain-energy coefficient.
for name,segs,ref in [('single',[(2*bh,r)],single),('stepped',[(bh,2*r),(bh,r)],stepped)]:
 L=sum(s[0] for s in segs);x0=0;val=0.
 for length,radius in segs:
  dx=length/8192
  val+=sum((L-(x0+(j+.5)*dx))**2/(math.pi*radius**4/4)*dx for j in range(8192))
  x0+=length
 ck('independent beam energy integration '+name,abs(val/ref['bending_times_E']-1)<1e-8)
beam=dict(poisson_assumed=nu,shear_factor_assumed=kap,
 pair=pair,single=single,stepped=stepped,
 single_lateral_ratio=single['lateral_times_E']/pair['lateral_times_E'],
 stepped_lateral_ratio=stepped['lateral_times_E']/pair['lateral_times_E'],
 step_added_fraction_of_reference_plates=baseline['local_added_solid_fraction']*2.5,
 scope='ideal segmented beam components only; short post3D compliance and effective grain stiffness unknown')

deps=['計算部品/drying_stop_geometry.py','GPT往復/乾湿で潰れない粒内ストッパーの成立条件_20261010/model.md','GPT往復/濡れ後の復帰と排水検証_20261009/sources.json']
data=dict(cycle=124,physical_trials=0,success_probability=None,dependency_hashes={p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in deps},rows=rows,quadrature_errors=errors,height_rearrangement=z,beam_comparison=beam,receiver_footprint_fraction=h['pairs']*math.pi*land**2/patch,limits=a['limits'])
v=dict(count=len(checks),passed=True,checks=checks,physical_validation=False)
def enc(x):return (json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
for name,x in [('results.json',data),('validation.json',v)]:
 if '--check' in sys.argv:assert (D/name).read_bytes()==enc(x)
 else:(D/name).write_bytes(enc(x))
print(json.dumps(dict(checks=len(checks),rows=rows,max_fine_quadrature_error=max(x['fine_relative_error'] for x in errors),receiver_fraction=data['receiver_footprint_fraction'],beam_ratios={k:v for k,v in beam.items() if 'ratio' in k or 'fraction' in k}),ensure_ascii=False))
