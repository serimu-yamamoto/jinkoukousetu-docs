"""Load-controlled unilateral contact of four rounded R4 endpoints.
Back junction is fixed; a comparison allows an ideal rotational support there.
Neither support is a calibrated granular bed. Local Hertz compliance is optional.
"""
import copy,json,math,itertools
from elastic_core import H,np,build_frame,response
from scipy.optimize import root,minimize

def normal(beta,phi):
    b=math.radians(beta);p=math.radians(phi);return np.array([math.cos(b),math.sin(b)*math.cos(p),math.sin(b)*math.sin(p)])
def support(n,R,a,opening):
    al=math.radians(opening/2)
    def arc(x,y):
        p=math.atan2(y,x)%(2*math.pi)
        return math.hypot(x,y) if al<=p<=2*math.pi-al else x*math.cos(al)+abs(y)*math.sin(al)
    return a+R*max(arc(n[0],n[1]),arc(n[0],n[2]),math.hypot(n[1],n[2]))

def solve_contact(C,g,F,k=0.,moment=None):
    # Convex dual: min .5 f'C f + g'f + (3/5)k sum f^(5/3),
    # subject to sum f=F, f>=0, and optionally A'f=0.
    for m in range(1,5):
        if moment is not None and m<3:continue
        for indices in itertools.combinations(range(4),m):
            ids=np.array(indices);Ca=C[np.ix_(ids,ids)];ga=g[ids]
            A=None if moment is None else moment[ids]
            nr=0 if A is None else 2
            mat=np.zeros((m+1+nr,m+1+nr));mat[:m,:m]=Ca;mat[:m,m]=-1;mat[m,:m]=1
            if A is not None:mat[:m,m+1:]=-A;mat[m+1:,:m]=A.T
            rhs=np.r_[-ga,F,np.zeros(nr)]
            try:z=np.linalg.solve(mat,rhs)
            except np.linalg.LinAlgError:continue
            if k:
                assert A is None
                z0=np.r_[z[:m]/F,z[m]/.24]
                def fun(y):
                    f=F*y[:m];h=k*np.sign(f)*np.abs(f)**(2/3)
                    return np.r_[(Ca@f+ga+h-y[m]*.24)/.24,sum(y[:m])-1]
                def jac(y):
                    f=F*y[:m];J=np.zeros((m+1,m+1));J[:m,:m]=(Ca+np.diag((2/3)*k*np.maximum(np.abs(f),1e-20)**(-1/3)))*F/.24;J[:m,m]=-1;J[m,:m]=1;return J
                sol=root(fun,z0,jac=jac,tol=1e-10)
                if np.max(np.abs(fun(sol.x)))>1e-8:continue
                z=np.r_[sol.x[:m]*F,sol.x[m]*.24]
            f=np.zeros(4);f[ids]=z[:m];delta=z[m];omega=np.zeros(2) if A is None else z[m+1:]
            gap=g+C@f+k*np.sign(f)*np.abs(f)**(2/3)-delta
            if moment is not None:gap-=moment@omega
            if min(f)<-max(1e-13,F*1e-9) or min(gap)<-1e-9:continue
            if max(abs(gap[ids]))>1e-8:continue
            f=np.maximum(f,0)
            return dict(forces_N=f,delta_mm=float(delta),gap_mm=gap,omega=omega,active=int(sum(f>F*1e-7)),effective_contacts=float(F*F/(f@f)),load_sum_relative=abs(float(sum(f)/F-1)),complementarity_N_mm=float(np.max(np.abs(f*gap))),moment_residual=0. if moment is None else float(np.linalg.norm(moment.T@f)))
    raise RuntimeError('No admissible contact set')

def evaluate(model,beta,phi,F,offset=None,plane_E=None,free_rotation=False):
    inp=model['inp'];g0=inp['geometry'];m=inp['mechanics'];n=normal(beta,phi);tips=model['nodes'][model['tips']];offset=np.zeros(4) if offset is None else np.asarray(offset)/1000
    heights=tips@n+g0['wire_radius_mm']+offset;hmax=max(heights);gap=hmax-heights
    B=np.zeros((12,4))
    for i in range(4):B[i*3:i*3+3,i]=-n
    C=B.T@model['C']@B;k=0.;Estar=None
    if plane_E is not None:
        vp=inp['contacts']['plane_nu'];Estar=1/((1-m['nu']**2)/m['E_MPa']+(1-vp**2)/plane_E)
        k=(3/(4*Estar*math.sqrt(g0['wire_radius_mm'])))**(2/3)
    moment=None;rot_basis=None
    if free_rotation:
        v=np.array([0.,0.,1.]);e1=np.cross(n,v);e1/=np.linalg.norm(e1);e2=np.cross(n,e1);rot_basis=np.stack([e1,e2],axis=1)
        lever=tips-np.array([-g0['R_mm'],0.,0.]);moment=np.cross(lever,n)@rot_basis
    sol=solve_contact(C,gap,F,k,moment);f=sol['forces_N'];mech=response(model,B@f);delta=sol['delta_mm']
    deformed=mech.pop('deformed_centerlines');mech.pop('displacements')
    extra=None
    if plane_E is None and not free_rotation and np.max(np.abs(offset))==0:
        extra=float(hmax-delta-np.max(deformed@n+g0['wire_radius_mm']))
    patch=None
    if Estar:
        radii=(3*f*g0['wire_radius_mm']/(4*Estar))**(1/3);pressure=np.divide(3*f,2*math.pi*radii*radii,out=np.zeros(4),where=radii>0);patch=dict(max_Hertz_pressure_MPa=float(max(pressure)),effective_E_MPa=Estar,max_patch_over_tip_radius=float(max(radii)/g0['wire_radius_mm']),indentations_um=(k*f**(2/3)*1000).tolist(),small_patch_diagnostic=bool(max(radii)/g0['wire_radius_mm']<=.2))
    omega_mag=float(np.linalg.norm(sol['omega']))
    rotation_error=2*(g0['R_mm']+g0['wire_radius_mm'])*math.hypot(1-math.cos(omega_mag),math.sin(omega_mag)-omega_mag)
    qptest=None
    if beta in [.5,2] and phi==45 and abs(F-.0009)<1e-12 and not free_rotation and plane_E is None and np.max(abs(offset))==0:
        fun=lambda w:(.5*F*w@C@w+gap@w)/.24
        jac=lambda w:(F*C@w+gap)/.24
        opt=minimize(fun,np.ones(4)/4,jac=jac,bounds=[(0,1)]*4,constraints={'type':'eq','fun':lambda w:sum(w)-1,'jac':lambda w:np.ones(4)},method='SLSQP',options={'ftol':1e-14,'maxiter':500})
        qptest=dict(success=bool(opt.success),max_force_fraction_difference=float(np.max(np.abs(opt.x-f/F))))
    return dict(opening_deg=g0['opening_deg'],tilt_deg=beta,azimuth_deg=phi,total_force_mN=F*1000,offset_um=(offset*1000).tolist(),plane_E_MPa=plane_E,back_rotation_free_idealization=free_rotation,initial_gaps_um=(gap*1000).tolist(),normal=n.tolist(),forces_mN=(f*1000).tolist(),active_contacts=sol['active'],effective_contacts=sol['effective_contacts'],platen_travel_um=delta*1000,contact_gap_um=(sol['gap_mm']*1000).tolist(),ideal_support_rotation_rad=sol['omega'].tolist(),support_rotation_magnitude_rad=omega_mag,rigid_rotation_linearization_error_bound_um=1000*rotation_error,support_rotation_below_0_05rad=omega_mag<=.05,load_sum_relative=sol['load_sum_relative'],complementarity_N_mm=sol['complementarity_N_mm'],moment_residual_N_mm=sol['moment_residual'],mechanics=mech,hertz=patch,sampled_other_surface_gap_um=None if extra is None else extra*1000,rigid_body_support_exceeds_tip_plane_um=max(0,support(n,g0['R_mm'],g0['wire_radius_mm'],g0['opening_deg'])-hmax)*1000,independent_QP=qptest)

def main():
    inp=json.loads((H/'inputs.json').read_text(encoding='utf-8'));rows=[];height=[];hertz=[];free=[];verification=[];matrices=[]
    old=json.loads((H.parent/'荷重経路検証_直交輪と内部補強_20261007/hoop_results.json').read_text(encoding='utf-8'))
    for opening in inp['geometry']['openings_deg']:
        cur=copy.deepcopy(inp);cur['geometry']['opening_deg']=opening;model=build_frame(cur,brace_a=cur['geometry']['wire_radius_mm'],closed_hoop=True)
        for beta,phi,FmN in itertools.product(inp['contacts']['tilt_deg'],inp['contacts']['azimuth_deg'],inp['contacts']['total_force_mN']):rows.append(evaluate(model,beta,phi,FmN/1000))
        for offsets in itertools.product(inp['contacts']['height_offset_um'],repeat=4):height.append(evaluate(model,0,0,.0009,offset=offsets))
        for beta,phi,FmN,Ep in itertools.product(inp['contacts']['hertz_case_tilt_deg'],inp['contacts']['hertz_case_azimuth_deg'],inp['contacts']['hertz_case_force_mN'],inp['contacts']['plane_E_MPa']):hertz.append(evaluate(model,beta,phi,FmN/1000,plane_E=Ep))
        for beta,phi in itertools.product([0,.5,1,2],inp['contacts']['azimuth_deg']):free.append(evaluate(model,beta,phi,.0009,free_rotation=True))
        baseline=next(x for x in rows if x['opening_deg']==opening and x['tilt_deg']==0 and x['azimuth_deg']==0 and x['total_force_mN']==1)
        oldbase=next(x for x in old['balanced_models'] if x['opening_deg']==opening)['hoop']['responses'][0]
        verification.append(dict(opening_deg=opening,balanced_compliance_relative=abs(baseline['platen_travel_um']/oldbase['tip_directional_compliance_mm_N']-1),max_force_imbalance_mN=float(max(baseline['forces_mN'])-min(baseline['forces_mN']))))
        matrices.append(dict(opening_deg=opening,tip_nodes=model['nodes'][model['tips']].tolist(),tip_compliance_mm_N=model['C'].tolist(),max_reciprocity_relative=float(np.linalg.norm(model['C']-model['C'].T)/np.linalg.norm(model['C']))))
    allrows=rows+height+hertz+free
    assert max(x['balanced_compliance_relative'] for x in verification)<1e-10
    assert max(x['load_sum_relative'] for x in allrows)<1e-7
    assert max(x['complementarity_N_mm'] for x in allrows)<1e-10
    out=dict(metadata={'physical_tests':0,'success_probability':None,'scope':'Single grain, assumed material, specified support; not a bed or a skiing trial.'},tilt_cases=rows,height_cases=height,hertz_cases=hertz,ideal_rotation_cases=free,verification=verification,tip_compliance=matrices)
    (H/'contact_results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'tilt_cases':len(rows),'height_cases':len(height),'hertz_cases':len(hertz),'rotation_cases':len(free),'physical_tests':0,'success_probability':None},indent=2))
if __name__=='__main__':main()
