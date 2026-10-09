"""Uncalibrated static contact-set audit. Fixed point contacts, no bed dynamics."""
from pathlib import Path
import sys,json,math,copy,hashlib,itertools
D=Path(__file__).resolve().parent;ROOT=D.parents[1]
if (ROOT/'.git/research100-deps').exists():sys.path.insert(0,str(ROOT/'.git/research100-deps'))
P=ROOT/'GPT往復/粒間接触検証_自由回転と濡れ_20261007'
sys.path.insert(0,str(P))
import numpy as np
from scipy.optimize import linprog
from cluster import basis,wrench_lp
from pair_geometry import support_points
I=json.loads((D/'inputs.json').read_text(encoding='utf-8'))
F=json.loads((P/'cluster_results.json').read_text(encoding='utf-8'))['fixtures']
R=.24;a=.022

def solve(points,normals,mu,Ftop,active,edges=32,outer=False,peak=False):
    dirs=[];columns=[]
    factor=1/math.cos(math.pi/edges) if outer else 1.
    for j in active:
        B=basis(normals[j]);p=np.array(points[j])
        for phi in np.arange(edges)*2*math.pi/edges:
            f=B@np.array([mu*factor*math.cos(phi),mu*factor*math.sin(phi),1.])
            dirs.append(f);columns.append(np.r_[f,np.cross(p/R,f)])
    A=np.array(columns).T;b=-np.r_[Ftop,np.cross(np.array(points[0])/R,Ftop)]
    objective=np.ones(A.shape[1]);Au=None;bu=None
    if peak:
        A=np.column_stack([A,np.zeros(6)]);objective=np.zeros(A.shape[1]);objective[-1]=1
        Au=np.zeros((len(active),A.shape[1]));bu=np.zeros(len(active))
        for k in range(len(active)):Au[k,k*edges:(k+1)*edges]=1;Au[k,-1]=-1
    sol=linprog(objective,A_eq=A,b_eq=b,A_ub=Au,b_ub=bu,bounds=(0,None),method='highs')
    ans={'success':bool(sol.success),'status':int(sol.status),'outer':outer,'edges':edges,'objective':'maximum_support_normal' if peak else 'sum_support_normal'}
    if sol.success:
        weights=sol.x[:len(active)*edges].reshape(-1,edges)
        ff=np.einsum('ij,ijk->ik',weights,np.array(dirs).reshape(-1,edges,3))
        fn=np.array([f@np.array(normals[j]) for f,j in zip(ff,active)])
        ratios=[float(np.linalg.norm(f-n*np.array(normals[j]))/max(n,1e-30)) for f,n,j in zip(ff,fn,active)]
        ans.update(forces=ff.tolist(),normal_components=fn.tolist(),actual_friction_ratios=ratios,sum_normal=float(fn.sum()),max_normal=float(fn.max()),residual=float(np.linalg.norm(A@sol.x-b)),objective_value=float(sol.fun))
    return ans

def classify(inner,outer):
    return 'feasible_inner' if inner['success'] else ('infeasible_outer' if outer['status']==2 else 'unresolved')

def main():
    checks=[]
    def ck(name,ok):
        if not ok:raise AssertionError(name)
        checks.append(name)
    for dep in I['dependencies']:
        data=(ROOT/dep['path']).read_bytes().replace(b'\r\n',b'\n')
        ck('dep-'+dep['path'],hashlib.sha256(data).hexdigest()==dep['sha256_LF'])
    rows=[];moment=[]
    for fixture in F:
        if not fixture['neighbor_geometry_valid']:continue
        for remove,mu,load in itertools.product(I['removed_support'],I['internal_friction'],I['loads']):
            active=[j for j in [1,2,3] if j!=remove]
            phi=math.radians(load['heading_deg']);ft=np.array([-load['q']*math.cos(phi),-load['q']*math.sin(phi),-1.])
            inside=solve(fixture['points'],fixture['normals'],mu,ft,active,edges=I['cone_edges'])
            outside=solve(fixture['points'],fixture['normals'],mu,ft,active,edges=I['cone_edges'],outer=True)
            row=dict(model=fixture['model'],pose=fixture['pose_id'],removed_support=remove,mu=mu,**load,active_supports=active,inner=inside,outer=outside,classification=classify(inside,outside),helper=False)
            if inside['success']:
                ck('residual-'+str(len(rows)),inside['residual']<1e-8)
                ck('cone-'+str(len(rows)),max(inside['actual_friction_ratios'])<=mu+1e-8)
            ck('cone-inclusion-'+str(len(rows)),not inside['success'] or outside['success'])
            rows.append(row)
            if remove is not None and mu==I['internal_friction'][0]:
                p1,p2=np.array(fixture['points'])[active];axis=(p2-p1)/np.linalg.norm(p2-p1)
                tau=float(axis@np.cross((np.array(fixture['points'][0])-p1)/R,ft))
                ck('moment-implies-infeasibility-'+str(len(moment)),abs(tau)<1e-8 or not outside['success'])
                moment.append(dict(model=fixture['model'],pose=fixture['pose_id'],removed_support=remove,**load,axis_moment_per_NR=tau,minimum_total_couple_mN_mm_at_2mN=abs(tau)*2*R))
    c=next(f for f in F if f['model']=='C3' and f['pose_id']==3)
    points=copy.deepcopy(c['points']);normals=copy.deepcopy(c['normals'])
    helper=support_points('C3',np.array([0.,0.,-1.]),R,a,np.array(c['central_rotation']))[1]
    ck('unique-helper-point',len(helper)==1)
    points.append(helper[0].tolist());normals.append([0.,0.,1.]);hr=[]
    for remove,mu,load in itertools.product(I['removed_support'],I['internal_friction'],I['loads']):
        active=[j for j in [1,2,3,4] if j!=remove]
        phi=math.radians(load['heading_deg']);ft=np.array([-load['q']*math.cos(phi),-load['q']*math.sin(phi),-1.])
        inner=solve(points,normals,mu,ft,active,edges=32);outer=solve(points,normals,mu,ft,active,edges=32,outer=True)
        peak=solve(points,normals,mu,ft,active,edges=32,peak=True)
        if inner['success']:
            ck('helper-residual-'+str(len(hr)),inner['residual']<1e-8)
            ck('helper-cone-'+str(len(hr)),max(inner['actual_friction_ratios'])<=mu+1e-8)
            ck('peak-objective-'+str(len(hr)),peak['max_normal']<=inner['max_normal']+1e-8)
        hr.append(dict(removed_support=remove,mu=mu,**load,active_supports=active,inner=inner,outer=outer,min_peak=peak,classification=classify(inner,outer),helper_is_ideal=True))
    # Compare the archived solver for a zero-tangential top load at fixed mu_top=0.
    independent=[]
    for fixture in F:
        if not fixture['neighbor_geometry_valid']:continue
        for mu in I['internal_friction']:
            old=wrench_lp(np.array(fixture['points']),np.array(fixture['normals']),0,mu,R,edges=32)
            new=next(r for r in rows if r['model']==fixture['model'] and r['pose']==fixture['pose_id'] and r['removed_support'] is None and r['mu']==mu and r['q']==0)['inner']
            ck('archived-formulation-'+str(len(independent)),old['success']==new['success'])
            err=None
            if old['success']:
                err=abs(old['total_support_normal']-new['sum_normal']);ck('archived-normal-'+str(len(independent)),err<1e-7)
            independent.append(dict(model=fixture['model'],pose=fixture['pose_id'],mu=mu,same_feasibility=True,total_normal_error=err))
    # Analytic vertical three-point support benchmark, independent of friction cones.
    pts=[[0,0,1],[-1,-1,0],[1,-1,0],[0,1,0]];ns=[[0,0,-1],[0,0,1],[0,0,1],[0,0,1]]
    bench=solve(pts,ns,0,np.array([0.,0.,-1.]),[1,2,3])
    ck('analytic-barycentric',np.max(np.abs(np.array(bench['normal_components'])-[.25,.25,.5]))<1e-9)
    snapshots=json.loads((ROOT/I['dependencies'][-1]['path']).read_text(encoding='utf-8'))['corrected_path_endpoints']
    opened=[]
    for r in snapshots:
        if r['sideways_per_forward']==-.1 and r['travel_mm']>0:
            lower=[r['plate_gap_mm']]+[q['clearance_lower_mm'] for q in r['support_distances']]
            ck('all-open-'+str(r['travel_mm']),min(lower)>0)
            opened.append(dict(travel_um=r['travel_mm']*1000,all_four_gap_lower_um=[x*1000 for x in lower],all_contact_forces_zero_for_unilateral_nonadhesive_model=True,static_load_support=False,not_a_continuous_path_certificate=True))
    # Refined points/normals can change forces but not the generic two-point moment condition.
    ref=json.loads((P/'numerical_audit.json').read_text(encoding='utf-8'))['refined_C3_pose3'];refined=[]
    for remove in I['removed_support']:
        active=[j for j in [1,2,3] if j!=remove]
        x=solve(ref['points'],ref['normals'],.6,np.array([0.,0.,-1.]),active,edges=64)
        base=next(r for r in rows if r['model']=='C3' and r['pose']==3 and r['removed_support']==remove and r['mu']==.6 and r['q']==0)['inner']
        ck('refined-feasibility-'+str(remove),x['success']==base['success'])
        refined.append(dict(removed_support=remove,refined=x,base=base))
    # Cone polygon resolution checks on representative original and helper states.
    convergence=[]
    for helper_on in [False,True]:
        pp,nn=(points,normals) if helper_on else (c['points'],c['normals'])
        for remove in [None,1,2,3]:
            active=[j for j in ([1,2,3,4] if helper_on else [1,2,3]) if j!=remove]
            ans=[solve(pp,nn,.6,np.array([0.,0.,-1.]),active,edges=e) for e in [16,32,64]]
            ck('cone-refinement-'+str(helper_on)+'-'+str(remove),len({r['success'] for r in ans})==1)
            convergence.append(dict(helper=helper_on,removed_support=remove,results=ans))
    out=dict(physical_tests=0,success_probability=None,scope='Fixed-geometry static necessary conditions; no stiffness compatibility, time path, 50 C or force-selected dynamics.',base_cases=rows,ideal_helper_point_mm=points[-1],ideal_helper_normal=normals[-1],helper_cases=hr,two_support_moment=moment,archived_solver_comparisons=independent,analytic_benchmark=bench,opened_snapshots=opened,refined_contact_cases=refined,cone_resolution=convergence)
    val=dict(passed=True,checks=len(checks),names=checks,physical_tests=0,success_probability=None)
    for name,obj in [('results.json',out),('validation.json',val)]:
        content=json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
        if '--check' in sys.argv:
            assert (D/name).read_text(encoding='utf-8')==content,name
        else:(D/name).write_text(content,encoding='utf-8',newline='\n')
    print(json.dumps(dict(base_cases=len(rows),helper_cases=len(hr),moment_cases=len(moment),checks=val['checks'],byte_check='--check' in sys.argv)))
if __name__=='__main__':main()
