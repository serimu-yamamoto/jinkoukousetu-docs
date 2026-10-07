"""Cycle12 core derived from cycle11 curved-rod calculation, commit f44df33. Units N, mm.
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

def build_frame(inp,brace_angle=None,brace_a=None,nquad=None,closed_hoop=False,balanced=False,extra_splits=None):
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

    loadpoints=[np.array([R*math.cos(th),sy*R*math.sin(th),0.]) for sy in [-1,1]]+[np.array([R*math.cos(th),0.,sy*R*math.sin(th)]) for sy in [-1,1]]
    tips=[int(np.argmin(np.linalg.norm(nodes-p,axis=1))) for p in loadpoints]
    L=np.zeros((nd,12))
    for j,k in enumerate(tips):L[k*6:k*6+3,j*3:j*3+3]=I3
    qs=np.zeros((nd,12));qs[free]=np.linalg.solve(Kscaled[np.ix_(free,free)],(scaling[:,None]*L)[free]);U=scaling[:,None]*qs;C=L.T@U
    for e in elements:
        p0=nodes[e['i']];ns=m['interior_points'];tt=np.linspace(0,1,ns)
        if e['kind']=='hoop':lo=math.atan2(p0[2],p0[1]);ph=lo+tt*e['L']/R;p=np.stack([np.zeros(ns),R*np.cos(ph),R*np.sin(ph)],axis=1);t=np.stack([np.zeros(ns),-np.sin(ph),np.cos(ph)],axis=1)
        else:
            isxy=np.max(np.abs(e['p'][:,2]))<1e-12;lo=math.atan2(p0[1] if isxy else p0[2],p0[0]);ph=lo+tt*e['L']/R
            p=np.stack([R*np.cos(ph),R*np.sin(ph) if isxy else np.zeros(ns),np.zeros(ns) if isxy else R*np.sin(ph)],axis=1)
            t=np.stack([-np.sin(ph),np.cos(ph) if isxy else np.zeros(ns),np.zeros(ns) if isxy else np.cos(ph)],axis=1)
        e['sample_points']=p;e['sample_tangents']=t;e['sample_s']=tt*e['L']
    return dict(nodes=nodes,tips=tips,L=L,U=U,C=(C+C.T)/2,K=K,free=free,elements=elements,inp=inp)

def response(model,force12):
    from scipy.integrate import cumulative_trapezoid
    u=model['U']@force12;nodes_u=u.reshape(-1,6);normstrain=0.;shearstrain=0.;maxrot=0.;maxdisp=0.;endpoint_error=0.;deformed=[]
    for e in model['elements']:
        wrench=np.linalg.solve(e['C'],e['B']@u[e['ids']]);F=wrench[:3];M=wrench[3:];p=e['sample_points'];t=e['sample_tangents'];s=e['sample_s'];sec=e['sec']
        moment=M+np.cross(e['end']-p,F);N=t@F;T=np.sum(t*moment,axis=1);Mb=moment-T[:,None]*t;V=F-N[:,None]*t
        eps=np.abs(N)/(sec['E']*sec['A'])+np.linalg.norm(Mb,axis=1)*sec['a']/(sec['E']*sec['I'])
        gam=np.abs(T)*sec['a']/(sec['G']*sec['J'])+4*np.linalg.norm(V,axis=1)/(3*sec['G']*sec['A'])
        curvature=T[:,None]*t/(sec['G']*sec['J'])+Mb/(sec['E']*sec['I'])
        rotation=nodes_u[e['i'],3:]+cumulative_trapezoid(curvature,s,axis=0,initial=0)
        du=np.cross(rotation,t)+N[:,None]*t/(sec['E']*sec['A'])+V/(sec['kappa']*sec['G']*sec['A'])
        displacement=nodes_u[e['i'],:3]+cumulative_trapezoid(du,s,axis=0,initial=0)
        endpoint_error=max(endpoint_error,float(np.linalg.norm(displacement[-1]-nodes_u[e['j'],:3])))
        normstrain=max(normstrain,float(max(eps)));shearstrain=max(shearstrain,float(max(gam)));maxrot=max(maxrot,float(np.linalg.norm(rotation,axis=1).max()));maxdisp=max(maxdisp,float(np.linalg.norm(displacement,axis=1).max()));deformed.append(p+displacement)
    force=model['L']@force12;res=(model['K']@u-force)[model['free']];m=model['inp']['mechanics'];R=model['inp']['geometry']['R_mm'];ratio=max(normstrain/m['strain_diagnostic'],shearstrain/m['shear_strain_diagnostic'],maxrot/m['rotation_diagnostic_rad'],maxdisp/(R*m['displacement_diagnostic_over_R']))
    return dict(displacements=u,nominal_normal_strain=normstrain,nominal_shear_strain_upper=shearstrain,max_interior_rotation_rad=maxrot,max_interior_displacement_mm=maxdisp,endpoint_integration_discrepancy_mm=endpoint_error,linear_diagnostic_ratio=ratio,inside_diagnostic=ratio<=1,relative_equilibrium_residual=float(np.linalg.norm(res)/max(np.linalg.norm(force),1e-30)),energy_N_mm=float(u@model['K']@u/2),work_N_mm=float(u@force),deformed_centerlines=np.vstack(deformed))
