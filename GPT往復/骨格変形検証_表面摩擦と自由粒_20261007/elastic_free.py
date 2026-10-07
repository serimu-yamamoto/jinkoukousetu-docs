"""Cycle14 generic free-grain core; constitutive integration derived from cycle12, commit 6af4fb7. Units N, mm.
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


from scipy.integrate import cumulative_trapezoid

def grain_arcs(model):
 e=np.eye(3);al=math.radians(75)
 if model=='R4':return [(e[0],e[1],al,2*math.pi-al),(e[0],e[2],al,2*math.pi-al),(e[1],e[2],0.,2*math.pi)]
 if model=='C3':return [(e[0],e[1],al,2*math.pi-al),(e[1],e[2],al,2*math.pi-al),(e[2],e[0],al,2*math.pi-al)]
 if model=='S3':return [(e[0],e[1],0.,2*math.pi),(e[1],e[2],0.,2*math.pi),(e[2],e[0],0.,2*math.pi)]
 raise ValueError(model)

def brace_segments(kind,R=.24):
 e=np.eye(3)
 if kind=='Y3':return [(np.zeros(3),-R*v) for v in e]
 if kind=='T6':
  out=[]
  for u,v,lo,hi in grain_arcs('C3'):
   for t in [lo,hi]:out.append((R*(math.cos(t)*u+math.sin(t)*v),-R*u))
  return out
 raise ValueError(kind)

def build(model,rotation,points,normals,R=.24,a=.022,E=300,nu=.45,kappa=.85,quad=64,interior=257,gauge=0,brace=None,brace_a=.014):
 Q=np.array(rotation);points=np.array(points);normals=np.array(normals);centres=points+a*normals;body=centres@Q;nodes=[];els=[]
 def node(p):
  for i,v in enumerate(nodes):
   if np.linalg.norm(v-p)<1e-8:return i
  nodes.append(p.copy());return len(nodes)-1
 for ai,(e1,e2,lo,hi) in enumerate(grain_arcs(model)):
  split=[lo,hi]+[z for z in [math.pi/2,math.pi,3*math.pi/2] if lo<z<hi]
  for c in body:
   if abs(c@np.cross(e1,e2))<1e-8:
    t=math.atan2(c@e2,c@e1)%(2*math.pi)
    if lo-1e-8<=t<=hi+1e-8:split.append(min(hi,max(lo,t)))
  split=sorted(split);unique=[split[0]]
  for t in split[1:]:
   if t-unique[-1]>1e-8:unique.append(t)
  def pos(ph):return (R*(np.cos(ph)[:,None]*e1+np.sin(ph)[:,None]*e2))@Q.T
  def tangent(ph):return (-np.sin(ph)[:,None]*e1+np.cos(ph)[:,None]*e2)@Q.T
  for left,right in zip(unique[:-1],unique[1:]):
   p0,p1=pos(np.array([left,right]));i=node(p0);j=node(p1);x,w=np.polynomial.legendre.leggauss(quad);ph=(left+right)/2+x*(right-left)/2;sec=section(a,E,nu,kappa);Ce=compliance(pos(ph),tangent(ph),w*(right-left)*R/2,p1,sec)
   B=np.zeros((6,12));B[:3,:3]=-I3;B[:3,3:6]=skew(p1-p0);B[:3,6:9]=I3;B[3:,3:6]=-I3;B[3:,9:]=I3
   tt=np.linspace(left,right,interior);els.append(dict(i=i,j=j,C=Ce,B=B,K=B.T@np.linalg.solve(Ce,B),sec=sec,points=pos(tt),tangents=tangent(tt),s=(tt-left)*R,arc=ai,angles=[left,right]))

 if brace:
  for bi,(p0b,p1b) in enumerate(brace_segments(brace,R)):
   p0=p0b@Q.T;p1=p1b@Q.T;i=node(p0);j=node(p1);L=np.linalg.norm(p1-p0);t=(p1-p0)/L;x,w=np.polynomial.legendre.leggauss(quad);pp=p0+(x[:,None]+1)/2*(p1-p0);sec=section(brace_a,E,nu,kappa);Ce=compliance(pp,np.tile(t,(quad,1)),w*L/2,p1,sec)
   B=np.zeros((6,12));B[:3,:3]=-I3;B[:3,3:6]=skew(p1-p0);B[:3,6:9]=I3;B[3:,3:6]=-I3;B[3:,9:]=I3
   ss=np.linspace(0,L,interior);els.append(dict(i=i,j=j,C=Ce,B=B,K=B.T@np.linalg.solve(Ce,B),sec=sec,points=p0+ss[:,None]*t,tangents=np.tile(t,(interior,1)),s=ss,arc=3+bi,angles=[0,L/R]))
 nodes=np.array(nodes);nd=6*len(nodes);K=np.zeros((nd,nd))
 for e in els:
  ids=np.r_[np.arange(e['i']*6,e['i']*6+6),np.arange(e['j']*6,e['j']*6+6)];e['ids']=ids;K[np.ix_(ids,ids)]+=e['K']
 load=np.zeros((nd,12));contact_nodes=[]
 for j,(p,c,n) in enumerate(zip(points,centres,normals)):
  i=int(np.argmin(np.linalg.norm(nodes-c,axis=1)));assert np.linalg.norm(nodes[i]-c)<1e-8;contact_nodes.append(i);load[6*i:6*i+3,j*3:j*3+3]+=I3;load[6*i+3:6*i+6,j*3:j*3+3]+=skew(p-c)
 scale=np.tile([1,1,1,1/R,1/R,1/R],len(nodes));Ks=scale[:,None]*K*scale[None,:];free=np.array([i for i in range(nd) if i//6!=gauge]);U=np.zeros((nd,12));U[free]=np.linalg.solve(Ks[np.ix_(free,free)],(scale[:,None]*load)[free]);U=scale[:,None]*U
 diag=1/np.sqrt(np.diag(K));Kn=diag[:,None]*K*diag[None,:];spectrum=np.linalg.eigvalsh(Kn);maxeig=float(spectrum[-1]);null=int(np.count_nonzero(np.abs(spectrum)<1e-8*maxeig));assert null==6, (model,null,spectrum[:12],min(e['angles'][1]-e['angles'][0] for e in els))
 return dict(K=K,U=U,load=load,nodes=nodes,elements=els,points=points,normals=normals,contact_nodes=contact_nodes,gauge=gauge,free=free,R=R,a=a,E=E,nu=nu,rigid_nullity=null,compliance=load.T@U)

def evaluate(m,forces,profiles=False):
 f=np.array(forces).reshape(12);F=f.reshape(4,3);u=m['U']@f;nu=u.reshape(-1,6);force=m['load']@f;res=m['K']@u-force;allp=[];alld=[];allrot=[];normal=0.;shear=0.;enderr=0.;worst=None;response=[]
 for ei,e in enumerate(m['elements']):
  wrench=np.linalg.solve(e['C'],e['B']@u[e['ids']]);ff=wrench[:3];M=wrench[3:];p=e['points'];t=e['tangents'];s=e['s'];sec=e['sec'];mm=M+np.cross(p[-1]-p,ff);N=t@ff;T=np.sum(t*mm,axis=1);Mb=mm-T[:,None]*t;V=ff-N[:,None]*t
  sig=np.abs(N)/sec['A']+np.linalg.norm(Mb,axis=1)*sec['a']/sec['I'];tau=np.abs(T)*sec['a']/sec['J']+4*np.linalg.norm(V,axis=1)/(3*sec['A'])
  rot=nu[e['i'],3:]+cumulative_trapezoid(T[:,None]*t/(sec['G']*sec['J'])+Mb/(sec['E']*sec['I']),s,axis=0,initial=0)
  du=np.cross(rot,t)+N[:,None]*t/(sec['E']*sec['A'])+V/(sec['kappa']*sec['G']*sec['A']);disp=nu[e['i'],:3]+cumulative_trapezoid(du,s,axis=0,initial=0)
  er=float(np.linalg.norm(disp[-1]-nu[e['j'],:3]));enderr=max(enderr,er)
  if sig.max()>normal:normal=float(sig.max());worst=dict(element=ei,arc=e['arc'],point_mm=p[int(sig.argmax())].tolist())
  shear=max(shear,float(tau.max()));allp.append(p);alld.append(disp);allrot.append(rot)
  if profiles:response.append(dict(points=p.tolist(),displacements=disp.tolist(),rotations=rot.tolist(),normal_stress_MPa=sig.tolist(),shear_stress_upper_MPa=tau.tolist()))
 allp=np.vstack(allp);alld=np.vstack(alld);allrot=np.vstack(allrot)
 # Remove one least-squares rigid motion before reporting shape deformation.
 B=np.vstack([np.column_stack([I3,-skew(p)]) for p in allp]);rigid=np.linalg.lstsq(B,alld.reshape(-1),rcond=None)[0];deformed=alld-(B@rigid).reshape(-1,3);relrot=allrot-rigid[3:]
 totalF=F.sum(axis=0);totalM=np.cross(m['points'],F).sum(axis=0);den=max(np.linalg.norm(force),1e-30);pdisp=[]
 for p,i in zip(m['points'],m['contact_nodes']):pdisp.append(nu[i,:3]+np.cross(nu[i,3:],p-m['nodes'][i]))
 maxdisp=float(np.linalg.norm(deformed,axis=1).max());maxrot=float(np.linalg.norm(relrot,axis=1).max());G=m['E']/(2*(1+m['nu']));ratio=max(normal/m['E']/.01,shear/G/.02,maxdisp/(m['R']*.05),maxrot/.05)
 ans=dict(peak_nominal_normal_stress_MPa=normal,peak_nominal_shear_stress_upper_MPa=shear,peak_nominal_normal_strain=normal/m['E'],peak_nominal_shear_strain_upper=shear/G,max_rigid_removed_displacement_mm=maxdisp,max_rigid_removed_rotation_rad=maxrot,linear_diagnostic_ratio=ratio,inside_linear_diagnostic=ratio<=1,required_uniform_E_for_diagnostic_MPa=m['E']*ratio,energy_N_mm=float(u@m['K']@u/2),work_N_mm=float(u@force),nodal_equilibrium_relative=float(np.linalg.norm(res[m['free']])/den),gauge_reaction_force_N=res[m['gauge']*6:m['gauge']*6+3].tolist(),gauge_reaction_moment_N_mm=res[m['gauge']*6+3:m['gauge']*6+6].tolist(),total_applied_force_N=totalF.tolist(),total_applied_moment_N_mm=totalM.tolist(),endpoint_integration_error_mm=enderr,contact_displacements_mm=np.array(pdisp).tolist(),worst_stress_location=worst,scope='Prescribed statically admissible contact forces; not the force distribution selected by friction and displacement compatibility.')
 if profiles:ans['profiles']=response;ans['fitted_rigid_motion']=rigid.tolist()
 return ans
