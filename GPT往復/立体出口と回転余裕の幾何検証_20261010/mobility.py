"""First-order mobility of archived 3D fixtures; not force/dynamics or a bed model."""
from pathlib import Path
import sys,json,math,itertools,hashlib
D=Path(__file__).resolve().parent;ROOT=D.parents[1]
local=ROOT/'.git/research99-deps'
if local.exists():sys.path.insert(0,str(local))
P=ROOT/'GPT往復/粒間接触検証_自由回転と濡れ_20261007'
sys.path.insert(0,str(P))
import numpy as np
from scipy.optimize import linprog
from scipy.spatial.transform import Rotation
from pair_geometry import support_points
from cluster import distance_bracket
I=json.loads((P/'inputs.json').read_text(encoding='utf-8'))
F=json.loads((P/'cluster_results.json').read_text(encoding='utf-8'))['fixtures']
R=I['geometry']['R_mm'];a=I['geometry']['wire_radius_mm']
def matrices(f,angle,cap):
    pts=np.array(f['points']);ns=np.array(f['normals'])
    direction=np.array([math.cos(angle),math.sin(angle),0.])
    rows=[];rhs=[]
    for j,(p,n) in enumerate(zip(pts,ns)):
        # x=[vz,R*omega_x,R*omega_y,R*omega_z,plate rise rate].
        c=np.r_[n[2],np.cross(p/R,n),1. if j==0 else 0.]
        rows.append(-c);rhs.append(float(n@direction))
    return np.array(rows),np.array(rhs),direction
def mobility(f,angle,cap):
    rows,rhs,direction=matrices(f,angle,cap)
    bounds=[(None,None)]+[(-cap,cap)]*3+[(0,None)]
    sol=linprog([0,0,0,0,1],A_ub=rows,b_ub=rhs,bounds=bounds,method='highs')
    ans=dict(model=f['model'],pose=f['pose_id'],heading_deg=round(math.degrees(angle),8),rotation_component_cap=cap,success=bool(sol.success),status=int(sol.status))
    if sol.success:
        residual=rhs-rows@sol.x
        v=direction+np.array([0,0,sol.x[0]]);w=sol.x[1:4]
        ans.update(translation_per_mm=v.tolist(),rotation_scaled=w.tolist(),rise_per_mm=float(sol.x[4]),min_linear_gap_rate=float(residual.min()),constraint_gap_rates=residual.tolist())
    return ans
def enumerate_vertices(f,angle,cap):
    A,b,_=matrices(f,angle,cap)
    for j in [1,2,3]:
        for sign in [-1,1]:
            row=np.zeros(5);row[j]=sign;A=np.vstack([A,row]);b=np.r_[b,cap]
    row=np.zeros(5);row[4]=-1;A=np.vstack([A,row]);b=np.r_[b,0]
    best=math.inf
    for ids in itertools.combinations(range(len(b)),5):
        M=A[list(ids)]
        if abs(np.linalg.det(M))<1e-12:continue
        v=np.linalg.solve(M,b[list(ids)])
        if np.max(A@v-b)<1e-8:best=min(best,v[4])
    return best
def main():
    inp=json.loads((D/'inputs.json').read_text(encoding='utf-8'));checks=[];rows=[];relief=[]
    def check(n,c):
        if not c:raise AssertionError(n)
        checks.append(n)
    for dep in inp['dependencies']:
        data=(ROOT/dep['path']).read_bytes().replace(b'\r\n',b'\n')
        check('dependency-'+dep['path'],hashlib.sha256(data).hexdigest()==dep['sha256_LF'])
    for f in F:
        if not f['neighbor_geometry_valid']:continue
        for deg in inp['headings_deg']:
            angle=math.radians(deg)
            for cap in inp['rotation_component_caps']:
                ans=mobility(f,angle,cap);rows.append(ans)
                if ans['success']:
                    check('linear-feasible-'+str(len(rows)),ans['min_linear_gap_rate']>-1e-8)
            # Fixed orientation and fixed center height: required local normal relief.
            direction=np.array([math.cos(angle),math.sin(angle),0.])
            demand=np.maximum(0,-np.array(f['normals'])[1:]@direction)
            relief.append(dict(model=f['model'],pose=f['pose_id'],heading_deg=deg,normal_relief_per_forward_mm=demand.tolist(),at_20_um_normal_relief_um=(20*demand).tolist(),max_at_20_um_um=float(20*demand.max())))
            # More allowed rotation cannot worsen the LP minimum.
            selected=rows[-len(inp['rotation_component_caps']):]
            vals=[r['rise_per_mm'] for r in selected if r['success']]
            check('nested-feasible-'+str(len(relief)),all(x>=y-1e-8 for x,y in zip(vals,vals[1:])))
    independent=[]
    for model in ['R4','C3','S3']:
        f=next(f for f in F if f['model']==model and f['pose_id']==3)
        for deg in [0,90]:
            for cap in [0,0.5]:
                ans=next(r for r in rows if r['model']==model and r['pose']==3 and r['heading_deg']==deg and r['rotation_component_cap']==cap)
                vertex=enumerate_vertices(f,math.radians(deg),cap)
                err=abs(vertex-ans['rise_per_mm'])
                check('vertex-enumeration-'+str(len(independent)),err<1e-7)
                independent.append(dict(model=model,heading_deg=deg,cap=cap,lp=ans['rise_per_mm'],vertices=vertex,error=err))
    # Conditional sensitivity using S1's steady elongated-grain mean rotation fit.
    # This is not a branch-particle trajectory and not a guaranteed rotation time.
    rotation=[]
    for S in inp['alignment_S']:
        k=(1-S**2.6)/2
        for theta in inp['rotation_angles_deg']:
            for h in inp['shear_band_mm']:
                travel=h*math.radians(theta)/k
                check('rotation-units-'+str(len(rotation)),abs(k*travel/h-math.radians(theta))<1e-12)
                rotation.append(dict(S=S,k=k,angle_deg=theta,shear_band_mm=h,conditional_travel_mm=travel))
    out=dict(physical_tests=0,success_probability=None,scope=inp['scope'],mobility=rows,relief=relief,independent_lp=independent,rotation_sensitivity=rotation)
    val=dict(passed=True,checks=len(checks),names=checks.copy(),physical_tests=0,success_probability=None)
    for name,obj in [('mobility_results.json',out),('validation.json',val)]:
        data=json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False)+'\n'
        if '--check' in sys.argv:
            check('byte-'+name,(D/name).read_text(encoding='utf-8')==data)
        else:(D/name).write_text(data,encoding='utf-8',newline='\n')
    print(json.dumps(dict(mobility_rows=len(rows),relief_rows=len(relief),rotation_rows=len(rotation),checks=val['checks'],independent_lp=len(independent),byte_check='--check' in sys.argv)))
if __name__=='__main__':main()
