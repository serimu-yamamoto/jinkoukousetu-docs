"""Delivery and mathematical checks. These are not physical-material pass tests."""
from pathlib import Path
import sys,json,ast,math,re,struct,copy,importlib.metadata as metadata
H=Path(__file__).resolve().parent;root=H.parent.parent
if (root/'.deps').exists():sys.path.insert(0,str(root/'.deps'))
import numpy as np
from closed_hoop import distance
I=json.loads((H/'inputs.json').read_text(encoding='utf-8'));R=json.loads((H/'results.json').read_text(encoding='utf-8'));C=json.loads((H/'hoop_results.json').read_text(encoding='utf-8'));G=json.loads((H/'geometry_validation.json').read_text(encoding='utf-8'))
checks=[]
def check(name,value,detail):
    assert value,name
    checks.append({'name':name,'passed':True,'scope':detail})
models=[R['base']['mechanics']]+[x['mechanics'] for x in R['variants']]+[x['mechanics'] for x in C['models']]+[x[k] for x in C['balanced_models'] for k in ['hoop','unbraced']]
check('linear_member_analytic_identities',all(x['relative']<1e-11 for x in R['verification']['straight'].values()) and R['verification']['circular_quarter']['relative']<1e-11,'Straight axial, bending/shear, torsion and circular quarter-arc.')
check('independent_published_reference',R['verification']['published_rectangle']['relative_to_rounded']<2e-4,'Rounded rectangular reference only; not commercial solver execution.')
check('quadrature_and_partition_invariance',R['verification']['quadrature64_128_relative']<1e-9 and R['verification']['partition_invariance_relative']<1e-9,'Integration and split of an otherwise unchanged curved rod.')
check('rigid_rotation_compatibility',max(x['rigid_rotation_residual'] for x in models)<1e-10,'No internal deformation under infinitesimal rigid rotation.')
check('reciprocity_and_equilibrium',max(x['symmetry_relative'] for x in models)<1e-9 and max(q['relative_residual'] for x in models for q in x['responses'])<1e-9,'Assembled linear equations only.')
check('energy_work_identity',all(abs(2*q['energy_N_mm']-q['work_N_mm'])<1e-9*max(abs(q['work_N_mm']),1e-20) for x in models for q in x['responses']),'Linear strain energy is half of final load times displacement.')
check('declared_design_counts',len(R['variants'])==45 and len(C['models'])==20 and sum(x['geometry_result']=='collision_counterexample' for x in R['variants'])==44,'Enumeration counts are not probability.')
cur=copy.deepcopy(I);cur['geometry']['opening_deg']=150;lo=distance(cur);cur['geometry']['distance_samples']=131073;fine=distance(cur)
check('distance_cover_interval',fine['lower_mm']<=lo['upper_mm']+1e-12 and lo['lower_mm']<=fine['upper_mm']+1e-12,'Independent finer angular covering intervals overlap; translation minimum remains analytical.')
for rec in G:
    cand=next(x for x in C['models'] if x['opening_deg']==rec['opening_deg'] and x['hoop_radius_um']==22)
    assert rec['volume_mm3']<cand['cost']['volume_upper_mm3']
    assert rec['connected_components']==1 and rec['every_edge_two_faces'] and rec['consistent_orientation'] and rec['nonzero_face_areas']
    assert all(x['intersection_volume_mm3']<1e-12 for x in rec['registered_intersection_samples'])
check('geometry_and_conservative_volume',True,'Two connected meshes, oriented closed faces, 12 supplemental static intersection samples, and conservative analytical material volumes.')
dtype=np.dtype([('normal','<f4',(3,)),('v','<f4',(3,3)),('attr','<u2')]);stls=[]
for p in H.glob('*.stl'):
    b=p.read_bytes();n=struct.unpack_from('<I',b,80)[0];assert len(b)==84+50*n
    a=np.frombuffer(b,dtype=dtype,offset=84,count=n);v=a['v'].astype(float);normal=a['normal'].astype(float);cross=np.cross(v[:,1]-v[:,0],v[:,2]-v[:,0]);mag=np.linalg.norm(cross,axis=1)
    assert np.isfinite(v).all() and np.isfinite(normal).all() and np.all(mag>0)
    assert np.max(np.abs(np.linalg.norm(normal,axis=1)-1))<2e-4
    assert np.min(np.sum(normal*cross/mag[:,None],axis=1))>.999
    stls.append({'path':p.name,'triangles':n,'bytes':len(b)})
check('stl_serialization',len(stls)==2,'Binary length, finite coordinates, nonzero triangles, unit and consistent normals.')
def finite(x):
    if isinstance(x,float):assert math.isfinite(x)
    elif isinstance(x,dict):
        for v in x.values():finite(v)
    elif isinstance(x,list):
        for v in x:finite(v)
jsons=[p for p in H.glob('*.json') if p.name!='validation.json']
for p in jsons:finite(json.loads(p.read_text(encoding='utf-8')))
for p in H.glob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
report=H.parent/'GPT回答_多方向探索第11巡_閉じた補強輪による支持と局所変形の分離_20261007.md';links=0
for p in [*H.glob('*.md'),report]:
    for target in re.findall(r'!?\[[^\]]*\]\(([^\s)]+)\)',p.read_text(encoding='utf-8')):
        if target.startswith(('http:','https:','#')):continue
        dest=p.parent/target.split('#')[0]
        if dest.name=='validation.json':continue
        assert dest.exists(),(p.name,target);links+=1
check('files_and_links',True,'Finite JSON, Python syntax and relative links in new documents.')
check('no_physical_probability',I['probability']['physical_tests']==0 and I['probability']['success_probability'] is None and C['metadata']['success_probability'] is None,'No experiments have been performed; geometry and algebra are not physical success.')
versions={x:metadata.version(x) for x in ['numpy','scipy','matplotlib','manifold3d']}
(H/'requirements.txt').write_text('\n'.join(k+'=='+v for k,v in versions.items())+'\n',encoding='utf-8')
output={'checks':checks,'STLs':stls,'relative_links':links,'versions':versions,'finer_distance_interval_mm':fine,'physical_tests':0,'success_probability':None}
(H/'validation.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'checks':len(checks),'passed':all(x['passed'] for x in checks),'STLs':len(stls),'relative_links':links,'physical_tests':0,'success_probability':None},indent=2))
