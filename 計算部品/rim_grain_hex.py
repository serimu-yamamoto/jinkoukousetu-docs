"""Hex8 linear elasticity for the cycle105 annular grain; E=1, dimensions mm.
Clamped bottom; uniform prescribed top displacement in one axis, other axes free.
No contact, large strain, viscoelasticity, buckling, flow or material qualification.
"""
import math
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
SIGNS=np.array([[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],
                [-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]],float)
GP=np.array([[x,y,z] for x in [-1/math.sqrt(3),1/math.sqrt(3)]
 for y in [-1/math.sqrt(3),1/math.sqrt(3)] for z in [-1/math.sqrt(3),1/math.sqrt(3)]])
DN=np.array([np.array([SIGNS[:,j]*np.prod(1+SIGNS[:,[k for k in range(3) if k!=j]]*p[[k for k in range(3) if k!=j]],axis=1)/8 for j in range(3)]) for p in GP])
def elements(coords,nu):
    mu=1/(2*(1+nu));lam=nu/((1+nu)*(1-2*nu))
    D=np.zeros((6,6));D[:3,:3]=lam;D[np.arange(3),np.arange(3)]+=2*mu;D[3:,3:]=np.eye(3)*mu
    jac=np.einsum('gij,ejk->egik',DN,coords);det=np.linalg.det(jac)
    if np.min(det)<=0:raise ValueError('Inverted element')
    grad=np.einsum('egij,gjk->egik',np.linalg.inv(jac),DN)
    B=np.zeros((len(coords),8,6,24))
    for a in range(3):B[:,:,a,a::3]=grad[:,:,a,:]
    for row,a,b in [(3,0,1),(4,1,2),(5,2,0)]:
        B[:,:,row,a::3]=grad[:,:,b,:];B[:,:,row,b::3]=grad[:,:,a,:]
    K=np.einsum('egai,ab,egbj,eg->eij',B,D,B,det,optimize=True)
    return K,det.sum(axis=1)
def mesh(nr,nt,nz,fraction):
    assert nt%18==0 and nz%6==0
    period=nt//6;web=int(round(period*fraction));ids={};xyz=[];cells=[]
    start=-math.pi*fraction/6
    def node(ir,it,iz):
        key=(ir,it%nt,iz)
        if key not in ids:
            r=.7+.3*ir/nr;t=start+2*math.pi*(it%nt)/nt
            ids[key]=len(xyz);xyz.append([r*math.cos(t),r*math.sin(t),.6*iz/nz])
        return ids[key]
    for iz in range(nz):
      for it in range(nt):
        if nz//6<=iz<5*nz//6 and it%period>=web:continue
        for ir in range(nr):
          cells.append([node(ir,it,iz),node(ir+1,it,iz),node(ir+1,it+1,iz),node(ir,it+1,iz),
                        node(ir,it,iz+1),node(ir+1,it,iz+1),node(ir+1,it+1,iz+1),node(ir,it+1,iz+1)])
    return np.array(xyz),np.array(cells)
def solve(nr,nt,nz,fraction,nu=.3):
    xyz,cells=mesh(nr,nt,nz,fraction);rr=[];cc=[];vv=[];volume=0.
    for j in range(0,len(cells),128):
        cell=cells[j:j+128];K,v=elements(xyz[cell],nu);volume+=float(v.sum())
        dofs=(3*cell[:,:,None]+np.arange(3)).reshape(len(cell),24)
        rr.append(np.repeat(dofs,24,axis=1).ravel());cc.append(np.tile(dofs,(1,24)).ravel());vv.append(K.ravel())
    N=3*len(xyz);K=coo_matrix((np.concatenate(vv),(np.concatenate(rr),np.concatenate(cc))),shape=(N,N)).tocsr()
    root=np.flatnonzero(np.isclose(xyz[:,2],0));top=np.flatnonzero(np.isclose(xyz[:,2],.6))
    fixedroot=(3*root[:,None]+np.arange(3)).ravel();amp=6e-7
    out=dict(mesh=[nr,nt,nz],web_fraction=fraction,nu=nu,nodes=len(xyz),elements=len(cells),mesh_volume_mm3=volume)
    for name,axis in [('normal',2),('lateral',0)]:
        driven=3*top+axis;fixed=np.r_[fixedroot,driven];free=np.setdiff1d(np.arange(N),fixed)
        u=np.zeros(N);u[driven]=amp
        u[free]=spsolve(K[free,:][:,free],-K[free,:][:,fixed]@u[fixed])
        force=K@u;F=float(force[driven].sum());norm=max(abs(F),1e-30)
        out[name]=dict(stiffness_E1=F/amp,relative_residual=float(np.max(abs(force[free]))/norm),
            force_balance=float(np.max(abs(force.reshape(-1,3).sum(axis=0)))/norm),
            energy=float(.5*u@force),energy_reaction_ratio=float((u@force)/(F*amp)))
    return out
def capillary(width_mm,height_mm=None,sigma=.06794,angle_deg=60.):
    if height_mm is None: perimeter_area=4/(width_mm/1000)
    else:perimeter_area=2*(1/(width_mm/1000)+1/(height_mm/1000))
    magnitude=sigma*perimeter_area*abs(math.cos(math.radians(angle_deg)))
    return dict(width_mm=width_mm,height_mm=height_mm,assumed_angle_deg=angle_deg,
        pressure_magnitude_Pa=magnitude,equivalent_head_mm=1000*magnitude/(1000*9.81))
