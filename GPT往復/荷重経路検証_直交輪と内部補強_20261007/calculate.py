"""R2/R3: curved-rod frame, bracing collision, and cost. SI-derived equations in N, mm.
The inputs are assumptions, not measured 50 C properties. Linear results beyond
small deformation are reported as sensitivity only, never as physical deflections.
"""
from pathlib import Path
import sys,json,math,itertools
H=Path(__file__).resolve().parent;ROOT=H.parent.parent
if (ROOT/'.deps').exists():sys.path.insert(0,str(ROOT/'.deps'))
import numpy as np
I3=np.eye(3)
def skew(v):
    x,y,z=v;return np.array([[0,-z,y],[z,0,-x],[-y,x,0.]])
def section(a,E,nu,kappa):
    return dict(A=math.pi*a*a,I=math.pi*a**4/4,J=math.pi*a**4/2,E=E,G=E/(2*(1+nu)),kappa=kappa,a=a)
def compliance(points,tangents,weights,end,sec):
    C=np.zeros((6,6))
    for p,t,ds in zip(points,tangents,weights):
        tt=np.outer(t,t)
        D=np.zeros((6,6));D[:3,:3]=tt/(sec['E']*sec['A'])+(I3-tt)/(sec['kappa']*sec['G']*sec['A'])
        D[3:,3:]=tt/(sec['G']*sec['J'])+(I3-tt)/(sec['E']*sec['I'])
        B=np.zeros((6,6));B[:3,:3]=I3;B[3:,:3]=skew(end-p);B[3:,3:]=I3
        C+=B.T@D@B*ds
    return (C+C.T)/2

def arc_data(R,lo,hi,plane,n):
    x,w=np.polynomial.legendre.leggauss(n);ph=(lo+hi)/2+x*(hi-lo)/2
    def pos(a):return np.array([R*math.cos(a),R*math.sin(a),0.]) if plane=='xy' else np.array([R*math.cos(a),0.,R*math.sin(a)])
    points=np.stack([pos(a) for a in ph]);tangents=np.stack([[-math.sin(a),math.cos(a),0] if plane=='xy' else [-math.sin(a),0,math.cos(a)] for a in ph])
    return pos(lo),pos(hi),points,tangents,w*(hi-lo)*R/2

def straight_data(p0,p1,n):
    x,w=np.polynomial.legendre.leggauss(n);l=np.linalg.norm(p1-p0);t=(p1-p0)/l
    return p0,p1,p0+(x[:,None]+1)*(p1-p0)/2,np.tile(t,(n,1)),w*l/2

def frame(inp,brace_angle=None,brace_a=None,nquad=None,closed_hoop=False,balanced=False,extra_splits=None):
    g=inp['geometry'];m=inp['mechanics'];R=g['R_mm'];a=g['wire_radius_mm'];th=math.radians(g['opening_deg']/2);nquad=nquad or m['quadrature_points']
    nodes=[];elements=[]
    def node(p):
        for i,q in enumerate(nodes):
            if np.linalg.norm(p-q)<1e-10:return i
        nodes.append(p.copy());return len(nodes)-1
    def element(data,rad,kind):
        p0,p1,p,t,w=data;ia=node(p0);ib=node(p1);sec=section(rad,m['E_MPa'],m['nu'],m['shear_factor']);C=compliance(p,t,w,p1,sec)
        B=np.zeros((6,12));B[:3,:3]=-I3;B[:3,3:6]=skew(p1-p0);B[:3,6:9]=I3;B[3:,3:6]=-I3;B[3:,9:]=I3
        elements.append(dict(i=ia,j=ib,C=C,B=B,K=B.T@np.linalg.solve(C,B),kind=kind,sec=sec,p=p,t=t,w=w,end=p1,L=float(sum(w))))
    splits=[th,math.pi,2*math.pi-th]
    if closed_hoop:splits += [math.pi/2,3*math.pi/2]
    if extra_splits:splits += [math.radians(z) for z in extra_splits]
    if brace_angle is not None:splits+= [math.radians(brace_angle),2*math.pi-math.radians(brace_angle)]
    splits=sorted(set(splits))
    for plane in ['xy','xz']:
        for lo,hi in zip(splits[:-1],splits[1:]):element(arc_data(R,lo,hi,plane,nquad),a,'arc')
    if brace_angle is not None:
        z=math.radians(brace_angle);xx=R*math.cos(z);rr=R*math.sin(z)
        corners=[np.array([xx,rr,0]),np.array([xx,0,rr]),np.array([xx,-rr,0]),np.array([xx,0,-rr])]
        for p0,p1 in zip(corners,corners[1:]+corners[:1]):element(straight_data(p0,p1,nquad),brace_a,'brace')
    if closed_hoop:
        xg,wg=np.polynomial.legendre.leggauss(nquad)
        for lo,hi in zip(np.arange(4)*math.pi/2,np.arange(1,5)*math.pi/2):
            ph=(lo+hi)/2+xg*(hi-lo)/2
            p=np.stack([np.zeros_like(ph),R*np.cos(ph),R*np.sin(ph)],axis=1)
            t=np.stack([np.zeros_like(ph),-np.sin(ph),np.cos(ph)],axis=1)
            p0=np.array([0.,R*math.cos(lo),R*math.sin(lo)]);p1=np.array([0.,R*math.cos(hi),R*math.sin(hi)])
            element((p0,p1,p,t,wg*(hi-lo)*R/2),brace_a,'hoop')
    nodes=np.array(nodes);nd=6*len(nodes);K=np.zeros((nd,nd))
    for el in elements:
        ids=np.r_[np.arange(el['i']*6,el['i']*6+6),np.arange(el['j']*6,el['j']*6+6)];el['ids']=ids;K[np.ix_(ids,ids)]+=el['K']
    fixed=node(np.array([-R,0.,0.]));tip=node(np.array([R*math.cos(th),R*math.sin(th),0.]));free=np.array([i for i in range(nd) if i//6!=fixed])
    # Scale rotations so conditioning is not dominated by units.
    scaling=np.tile([1,1,1,1/R,1/R,1/R],len(nodes));Kscaled=scaling[:,None]*K*scaling[None,:]
    eig=np.linalg.eigvalsh(Kscaled[np.ix_(free,free)])
    assert eig.min()>0
    def solve_force(direction):
        f=np.zeros(nd)
        loadnodes=[tip]
        if balanced:
            loadpoints=[np.array([R*math.cos(th),sy*R*math.sin(th),0.]) for sy in [-1,1]]+[np.array([R*math.cos(th),0.,sy*R*math.sin(th)]) for sy in [-1,1]]
            loadnodes=[int(np.argmin(np.linalg.norm(nodes-p,axis=1))) for p in loadpoints]
        for nn in loadnodes:f[nn*6:nn*6+3]+=np.array(direction)*m['force_N']/len(loadnodes)
        rhs=f*scaling
        qs=np.zeros(nd);qs[free]=np.linalg.solve(Kscaled[np.ix_(free,free)],rhs[free]);u=qs*scaling
        maxstrain=0.;maxshearstrain=0.;maxshearupper=0.;ratios=[];element_out=[]
        for el in elements:
            delta=el['B']@u[el['ids']];wrench=np.linalg.solve(el['C'],delta);F=wrench[:3];M=wrench[3:];sec=el['sec']
            moments=M+np.cross(el['end']-el['p'],F);N=el['t']@F;T=np.sum(el['t']*moments,axis=1);Mb=np.sqrt(np.maximum(0,np.sum(moments*moments,axis=1)-T*T))
            # Slender-rod nominal strains, not curved-solid stress or material strength.
            eps=np.abs(N)/(sec['E']*sec['A'])+Mb*sec['a']/(sec['E']*sec['I']);gamma=np.abs(T)*sec['a']/(sec['G']*sec['J'])
            V=np.sqrt(np.maximum(0,float(F@F)-N*N));shearupper=gamma+4*V/(3*sec['A']*sec['G'])
            maxstrain=max(maxstrain,float(max(eps)));maxshearstrain=max(maxshearstrain,float(max(gamma)));maxshearupper=max(maxshearupper,float(max(shearupper)))
            row=dict(kind=el['kind'],length_mm=el['L'],max_nominal_normal_strain=float(max(eps)),max_torsional_shear_strain=float(max(gamma)))
            if el['kind']=='brace':
                axial=float(np.mean(N));pinned=math.pi**2*sec['E']*sec['I']/el['L']**2
                row.update(axial_force_N=axial,Euler_pinned_N=pinned,Euler_clamped_N=4*pinned,compression_over_pinned=max(0,-axial)/pinned)
                ratios.append(max(0,-axial)/pinned)
            element_out.append(row)
        trans=u.reshape(-1,6)[:,:3];rot=u.reshape(-1,6)[:,3:];maxu=float(np.linalg.norm(trans,axis=1).max());maxrot=float(np.linalg.norm(rot,axis=1).max())
        factors=[m['strain_diagnostic']/maxstrain,m['shear_strain_diagnostic']/maxshearupper if maxshearupper else float('inf'),m['rotation_diagnostic_rad']/maxrot if maxrot else float('inf'),m['displacement_diagnostic_over_R']*R/maxu]
        diagF=m['force_N']*min(factors)
        bucklingF=m['force_N']/max(ratios) if ratios and max(ratios)>0 else None
        return dict(direction=direction,tip_displacement_mm=np.mean(trans[loadnodes],axis=0).tolist(),tip_directional_compliance_mm_N=float(np.dot(np.mean(trans[loadnodes],axis=0),direction)/m['force_N']),load_nodes=loadnodes,load_mode='equal four-tip forces' if balanced else 'one tip',max_displacement_mm=maxu,max_rotation_rad=maxrot,max_nominal_normal_strain=maxstrain,max_torsional_shear_strain=maxshearstrain,max_nominal_shear_strain_upper=maxshearupper,linear_diagnostic_force_mN=diagF*1000,first_pinned_Euler_force_mN=None if bucklingF is None else bucklingF*1000,energy_N_mm=float(u@K@u/2),work_N_mm=float(u@f),relative_residual=float(np.linalg.norm((K@u-f)[free])/np.linalg.norm(f)),elements=element_out,linear_prediction_not_physical_deformation=True)
    rigid_error=0.
    for axis in I3:
        rigid=np.zeros((len(nodes),6));rigid[:,:3]=np.cross(axis,nodes);rigid[:,3:]=axis
        for el in elements:rigid_error=max(rigid_error,float(np.linalg.norm(el['B']@rigid.flatten()[el['ids']])))
    responses=[solve_force(d) for d in m['force_directions']]
    Ctip=np.array([r['tip_displacement_mm'] for r in responses]).T/m['force_N']
    return dict(rigid_rotation_residual=rigid_error,nodes_mm=nodes.tolist(),tip_node=tip,back_node=fixed,elements_count=len(elements),responses=responses,tip_compliance_mm_N=Ctip.tolist(),scaled_condition_number=float(eig.max()/eig.min()),symmetry_relative=float(np.linalg.norm(Ctip-Ctip.T)/np.linalg.norm(Ctip)))

def brace_distance(inp,angle):
    g=inp['geometry'];R=g['R_mm'];q=g['q_mm'];phi=np.linspace(math.radians(g['opening_deg']/2),2*math.pi-math.radians(g['opening_deg']/2),g['distance_samples'])
    xx=R*math.cos(math.radians(angle));rr=R*math.sin(math.radians(angle));corners=np.array([[rr,0],[0,rr],[-rr,0],[0,-rr]])
    x=R*np.cos(phi);r=R*np.sin(phi);best=None
    for side in ['A_brace_B_arc','B_brace_A_arc']:
        s=np.clip(xx-x if side=='A_brace_B_arc' else x-xx,g['s_min_mm'],g['s_max_mm'])
        dx=(s+x-xx) if side=='A_brace_B_arc' else (x-xx-s)
        for plane in ['xy','xz']:
            yz=np.stack([r,np.zeros_like(r)],axis=1) if plane=='xy' else np.stack([np.zeros_like(r),r],axis=1)
            yz=yz+q if side=='A_brace_B_arc' else yz-q
            for j in range(4):
                a=corners[j];b=corners[(j+1)%4];v=b-a;t=np.clip((yz-a)@v/(v@v),0,1);nearest=a+t[:,None]*v
                d=np.sqrt(dx*dx+np.sum((yz-nearest)**2,axis=1));k=int(np.argmin(d))
                if best is None or d[k]<best['upper_mm']:
                    best=dict(upper_mm=float(d[k]),side=side,plane=plane,brace_edge=j,phi_deg=float(math.degrees(phi[k])),s_mm=float(s[k]),segment_fraction=float(t[k]))
    # Min over translations and segment points is 1-Lipschitz with respect to the
    # moving circular point. Grid covering radius bounds the continuous arc minimum.
    err=2*R*math.sin((phi[1]-phi[0])/4)
    best.update(lower_mm=max(0,best['upper_mm']-err),grid_cover_bound_mm=err,brace_brace_surface_lower_mm=g['s_min_mm'])
    return best

def cost(inp,angle,brad):
    g=inp['geometry'];c=inp['cost'];R=g['R_mm'];a=g['wire_radius_mm'];length=R*math.radians(360-g['opening_deg'])
    Vbase=2*(math.pi*a*a*length+4*math.pi*a**3/3)
    # Capsules are contained in joint neighborhoods; summing full capsules counts
    # overlap and is a conservative material-volume comparison, not final tooling.
    Vbrace=0 if angle is None else 4*(math.pi*brad*brad*(math.sqrt(2)*R*math.sin(math.radians(angle)))+4*math.pi*brad**3/3)
    V=Vbase+Vbrace;rho=V*1e-9*c['number_density_m3']*c['matrix_density_kg_m3'];mass=c['area_m2']*c['depth_m']*rho
    crf=c['discount']*(1+c['discount'])**c['years']/((1+c['discount'])**c['years']-1);fixed=c['initial_other_JPY']*crf+c['annual_other_JPY'];factor=crf+c['replacement']
    return dict(volume_upper_mm3=V,brace_volume_upper_mm3=Vbrace,bulk_kg_m3=rho,pilot_mass_kg=mass,annual_equivalent_JPY=fixed+mass*c['assumed_price_JPY_kg']*factor,finished_price_cap_JPY_kg=(c['annual_budget_JPY']-fixed)/(mass*factor))

def checks(inp):
    m=inp['mechanics'];s=section(.022,m['E_MPa'],m['nu'],m['shear_factor']);L=.4;d=straight_data(np.zeros(3),np.array([L,0,0]),64);C=compliance(d[2],d[3],d[4],d[1],s)
    straight={'axial':(C[0,0],L/(s['E']*s['A'])),'bending_plus_shear':(C[1,1],L**3/(3*s['E']*s['I'])+L/(s['kappa']*s['G']*s['A'])),'torsion':(C[3,3],L/(s['G']*s['J']))}
    d=arc_data(.24,0,math.pi/2,'xy',64);Cq=compliance(d[2],d[3],d[4],d[1],s);R=.24
    analytic=R**3*(math.pi/4/(s['E']*s['I'])+(3*math.pi/4-2)/(s['G']*s['J']))+R*math.pi/2/(s['kappa']*s['G']*s['A'])
    # Independent published rectangular quarter-circle example, not using its
    # rectangle parameters for the artificial grain.
    E=210000.;G=E/(2*(1+.296));R=1000.;w=25.;h=50.;F=1000.
    exact=F*R**3*(math.pi/4/(E*w*h**3/12)+(3*math.pi/4-2)/(G*.229*h*w**3))+F*R*math.pi/2/(5/6*G*w*h)
    return dict(straight={k:dict(numeric=float(v[0]),analytic=float(v[1]),relative=abs(float(v[0]/v[1]-1))) for k,v in straight.items()},circular_quarter=dict(numeric=float(Cq[2,2]),analytic=float(analytic),relative=abs(float(Cq[2,2]/analytic-1))),published_rectangle=dict(calculated_mm=exact,publication_rounded_mm=38.960,relative_to_rounded=abs(exact/38.960-1)))

def main():
    inp=json.loads((H/'inputs.json').read_text(encoding='utf-8'));base=frame(inp);rows=[]
    for angle in inp['geometry']['brace_angles_deg']:
        geom=brace_distance(inp,angle)
        for rad in inp['geometry']['brace_radii_mm']:
            gaplo=geom['lower_mm']-inp['geometry']['wire_radius_mm']-rad;gaphi=geom['upper_mm']-inp['geometry']['wire_radius_mm']-rad
            model=frame(inp,angle,rad)
            rows.append(dict(angle_deg=angle,brace_radius_um=rad*1000,distance=geom,surface_gap_lower_um=gaplo*1000,surface_gap_upper_um=gaphi*1000,geometry_result='clear_registered_path' if gaplo>0 else ('collision_counterexample' if gaphi<0 else 'unresolved'),cost=cost(inp,angle,rad),mechanics=model))
    partitioned=frame(inp,extra_splits=[60,90,120,240,270,300]);partition_error=float(np.linalg.norm(np.array(partitioned['tip_compliance_mm_N'])-np.array(base['tip_compliance_mm_N']))/np.linalg.norm(base['tip_compliance_mm_N']))
    fine=frame(inp,90,.006,nquad=128);mid=next(x for x in rows if x['angle_deg']==90 and x['brace_radius_um']==6)
    maxerr=max(abs(np.array(fine['tip_compliance_mm_N'])-np.array(mid['mechanics']['tip_compliance_mm_N'])).ravel())/np.max(np.abs(fine['tip_compliance_mm_N']))
    result=dict(metadata=inp['probability']|{'scope':inp['scope'],'base_commit':inp['base_commit']},base=dict(cost=cost(inp,None,0),mechanics=base),variants=rows,verification=checks(inp)|dict(quadrature64_128_relative=float(maxerr),partition_invariance_relative=partition_error),warning='Positive geometry clearance or linear stiffness improvement is not skiing performance, material strength, fatigue life, or probability.')
    assert result['verification']['circular_quarter']['relative']<1e-11
    assert all(x['relative']<1e-11 for x in result['verification']['straight'].values())
    assert maxerr<1e-9 and partition_error<1e-9
    assert max(r['relative_residual'] for model in [base]+[x['mechanics'] for x in rows] for r in model['responses'])<1e-9
    (H/'results.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({'variants':len(rows),'geometry_counts':{k:sum(x['geometry_result']==k for x in rows) for k in ['clear_registered_path','collision_counterexample','unresolved']},'physical_tests':0,'success_probability':None,'quarter_circle_check_relative':result['verification']['circular_quarter']['relative'],'quadrature_relative':maxerr},indent=2))
if __name__=='__main__':main()
