"""Numerical audits, not physical validation or a probability estimate."""
import ast,json,math,re,copy
from pathlib import Path
from urllib.parse import unquote
from elastic_core import H,np
from contact_model import support,normal
from gravity import analytic_min

def read(name):return json.loads((H/name).read_text(encoding='utf-8'))
def finite(x):
    if isinstance(x,float):assert math.isfinite(x)
    elif isinstance(x,dict):
        for v in x.values():finite(v)
    elif isinstance(x,list):
        for v in x:finite(v)
def main():
    C=read('contact_results.json');G=read('gravity_results.json');T=read('threshold_results.json');I=read('inputs.json');checks=[]
    def check(name,condition,details=None):
        assert condition,name
        checks.append(dict(name=name,passed=True,details=details))
    keys=['tilt_cases','height_cases','hertz_cases','ideal_rotation_cases'];rows=sum([C[k] for k in keys],[])
    check('case_counts',[len(C[k]) for k in keys]==[336,32,96,24],dict(zip(keys,[len(C[k]) for k in keys])))
    maxsum=max(abs(sum(x['forces_mN'])/x['total_force_mN']-1) for x in rows)
    mingap=min(min(x['contact_gap_um']) for x in rows);minforce=min(min(x['forces_mN']) for x in rows)
    comp=max(x['complementarity_N_mm'] for x in rows)
    check('unilateral_contact',maxsum<1e-7 and mingap>=-1e-7 and minforce>=-1e-10 and comp<1e-10,dict(max_relative_force_sum=maxsum,min_gap_um=mingap,min_force_mN=minforce,max_complementarity_N_mm=comp))
    eq=max(x['mechanics']['relative_equilibrium_residual'] for x in rows)
    work=max(abs(2*x['mechanics']['energy_N_mm']/x['mechanics']['work_N_mm']-1) for x in rows)
    check('equilibrium_and_energy',eq<1e-9 and work<1e-9,dict(max_equilibrium_relative=eq,max_energy_work_relative=work))
    recip=max(x['max_reciprocity_relative'] for x in C['tip_compliance']);eigs=[np.linalg.eigvalsh(x['tip_compliance_mm_N']).min() for x in C['tip_compliance']]
    check('positive_tip_compliance',recip<1e-10 and min(eigs)>0,dict(max_reciprocity=recip,minimum_eigenvalues=eigs))
    qp=[x['independent_QP'] for x in rows if x['independent_QP']]
    check('independent_convex_QP',len(qp)==4 and all(x['success'] and x['max_force_fraction_difference']<1e-8 for x in qp),qp)
    check('cycle11_balanced_limit',max(x['balanced_compliance_relative'] for x in C['verification'])<1e-10,C['verification'])
    valid=[x for x in rows if x['mechanics']['inside_diagnostic'] and x['sampled_other_surface_gap_um'] is not None]
    ming=min(x['sampled_other_surface_gap_um'] for x in valid)
    check('sampled_plane_gap_inside_linear_diagnostic',ming>-1e-5,dict(min_gap_um=ming,scope='Only sampled centreline points, rigid plane, zero height offset. Not continuous global contact validation.'))
    check('interior_resolution',max(x['relative'] for x in T['interior_refinement'].values())<1e-4 and T['endpoint_error_fine_mm']<T['endpoint_error_coarse_mm']/10,T['interior_refinement'])
    # Independent direct centreline point support; a spherical tube adds a.
    rng=np.random.default_rng(12102026);dirs=rng.normal(size=(192,3));dirs/=np.linalg.norm(dirs,axis=1)[:,None]
    R=I['geometry']['R_mm'];a=I['geometry']['wire_radius_mm'];maxerr=0.;minglobal=1e9
    for row in G['models']:
        op=row['opening_deg'];al=math.radians(op/2);ph=np.linspace(al,2*math.pi-al,8193);th=np.linspace(0,2*math.pi,8193)
        pts=np.vstack([np.column_stack([R*np.cos(ph),R*np.sin(ph),np.zeros_like(ph)]),np.column_stack([R*np.cos(ph),np.zeros_like(ph),R*np.sin(ph)]),np.column_stack([np.zeros_like(th),R*np.cos(th),R*np.sin(th)])])
        exact=np.array([support(n,R,a,op) for n in dirs]);direct=(pts@dirs.T).max(axis=0)+a
        err=exact-direct;bound=R*(2*math.pi/8192)/2
        check('direct_support_'+str(op),err.min()>-1e-12 and err.max()<bound,dict(max_difference_mm=float(err.max()),arc_cover_bound_mm=bound,directions=len(dirs),points_per_circle=8193))
        cx=row['mesh_centroid_mm'][0];minimum=row['mesh_centroid_analysis']['minimum']['height_mm'];margin=float(np.min(exact-cx*dirs[:,0]-minimum));minglobal=min(minglobal,margin)
        check('gravity_sample_audit_'+str(op),margin>=-1e-12 and row['centroid_transverse_asymmetry_mm']<1e-10,dict(min_sample_margin_above_analytic_mm=margin,scope='Sampling audit of analytic result; not dynamic settling'))
        assert abs(row['weight_N']-row['mass_kg']*I['gravity']['g_m_s2'])<1e-18
        assert abs(row['isolated_wind_scale']['force_N']-.5*1.2*80**2*math.pi*((R+a)/1000)**2)<1e-18
        assert abs(row['friction_coefficient_needed_without_other_retention_at_30deg']-1/math.sqrt(3))<1e-12
    check('dimensions_and_scales',True,dict(units='N mm MPa; mass uses mm3 to m3 factor 1e-9'))
    for x in [C['metadata'],G['metadata'],T]:assert x['physical_tests']==0 and x['success_probability'] is None
    for path in H.glob('*.json'):finite(json.loads(path.read_text(encoding='utf-8')))
    for path in H.glob('*.py'):ast.parse(path.read_text(encoding='utf-8'))
    check('finite_data_and_python_syntax',True)
    check('no_physical_or_probability_claim',True,dict(physical_tests=0,success_probability=None))
    docs=list(H.glob('*.md'))+[H.parent/'GPT回答_多方向探索第12巡_接触の偏りと自整列の成立条件_20261007.md']
    count=0
    for path in docs:
        for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
            if re.match(r'^[a-z]+:',target) or target.startswith('#'):continue
            link=unquote(target.split('#')[0]);assert (path.parent/link).exists(),str(path)+': '+target;count+=1
    check('delivery_relative_links',True,dict(links=count))
    out=dict(physical_tests=0,success_probability=None,numerical_audit_only=True,checks=checks,checks_passed=len(checks))
    (H/'validation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(checks_passed=len(checks),physical_tests=0,success_probability=None)))
if __name__=='__main__':main()
