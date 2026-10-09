"""Small-strain 3D post comparison using existing Hex8 elements; dimensions mm, E=1."""
import math
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import splu
from rim_grain_hex import elements
def post_mesh(n,kind,r=.025,h=.04):
    if type(n) is not int or n<2 or n%2:raise ValueError("even n>=2 required")
    if kind not in ("short","single","stepped"):raise ValueError("unknown geometry")
    if not all(math.isfinite(v) and v>0 for v in (r,h)):raise ValueError("invalid dimensions")
    xy=[];grid={}
    for j in range(n+1):
      for i in range(n+1):
        u=-1+2*i/n;v=-1+2*j/n
        grid[i,j]=len(xy);xy.append([r*u*math.sqrt(1-v*v/2),r*v*math.sqrt(1-u*u/2)])
    core=[[grid[i,j],grid[i+1,j],grid[i+1,j+1],grid[i,j+1]] for j in range(n) for i in range(n)]
    perimeter=[grid[i,0] for i in range(n)]+[grid[n,j] for j in range(n)]+[grid[i,n] for i in range(n,0,-1)]+[grid[0,j] for j in range(n,0,-1)]
    ann=[];previous=perimeter
    for ir in range(1,n//2+1):
      ring=[]
      for p in perimeter:
        ring.append(len(xy));xy.append([q*(1+2*ir/n) for q in xy[p]])
      for j in range(len(ring)):
        k=(j+1)%len(ring);ann.append([previous[j],ring[j],ring[k],previous[k]])
      previous=ring
    ids={};xyz=[];cells=[];top=[]
    def node(p,z):
      key=(p,z)
      if key not in ids:ids[key]=len(xyz);xyz.append([*xy[p],h*z/n])
      return ids[key]
    nz=n if kind=="short" else 2*n
    for iz in range(nz):
      quads=core+ann if kind=="stepped" and iz<n else core
      for q in quads:
        bottom=[node(p,iz) for p in q];upper=[node(p,iz+1) for p in q]
        cells.append(bottom+upper)
        if iz==nz-1:top.append(upper)
    return np.array(xyz),np.array(cells,dtype=int),np.array(top,dtype=int)
def top_weights(xyz,faces):
    weights=np.zeros(len(xyz));sign=np.array([[-1,-1],[1,-1],[1,1],[-1,1]],float)
    for a in [-1/math.sqrt(3),1/math.sqrt(3)]:
      for b in [-1/math.sqrt(3),1/math.sqrt(3)]:
        N=(1+sign[:,0]*a)*(1+sign[:,1]*b)/4
        dN=np.array([sign[:,0]*(1+sign[:,1]*b)/4,sign[:,1]*(1+sign[:,0]*a)/4])
        jac=np.einsum('ij,ejk->eik',dN,xyz[faces,:2]);area=np.linalg.det(jac)
        if np.min(area)<=0:raise ValueError("bad top face")
        for j in range(4):np.add.at(weights,faces[:,j],N[j]*area)
    return weights
def solve_post(n,kind,nu=.35,r=.025,h=.04):
    if not math.isfinite(nu) or not -1<nu<.5:raise ValueError("invalid Poisson ratio")
    xyz,cells,faces=post_mesh(n,kind,r,h);rr=[];cc=[];vv=[];volume=0.
    eps=np.diag([.001,-.0002,.0003]);patch_energy=0.
    for start in range(0,len(cells),128):
      c=cells[start:start+128];K,v=elements(xyz[c],nu);volume+=float(v.sum())
      dofs=(3*c[:,:,None]+np.arange(3)).reshape(len(c),24)
      rr.append(np.repeat(dofs,24,axis=1).ravel());cc.append(np.tile(dofs,(1,24)).ravel());vv.append(K.ravel())
      affine=(xyz[c]@eps.T).reshape(len(c),24);patch_energy+=float(.5*np.einsum('ei,eij,ej->',affine,K,affine))
    size=3*len(xyz)
    K=coo_matrix((np.concatenate(vv),(np.concatenate(rr),np.concatenate(cc))),shape=(size,size)).tocsc()
    root=np.flatnonzero(np.isclose(xyz[:,2],0,atol=1e-14));fixed=(3*root[:,None]+np.arange(3)).ravel()
    free=np.setdiff1d(np.arange(size),fixed);w=top_weights(xyz,faces);area=float(w.sum());amp=1e-7
    f=np.zeros((size,3))
    for a in range(3):f[a::3,a]=w*amp/area
    u=np.zeros_like(f);u[free]=splu(K[free,:][:,free]).solve(f[free])
    internal=K@u;reaction=internal-f;out={}
    for a,name in enumerate(["x","y","z"]):
      work=float(f[:,a]@u[:,a]);energy=float(.5*u[:,a]@internal[:,a])
      displacement=float(w@u[a::3,a]/area)
      balance=reaction[:,a].reshape(-1,3)+f[:,a].reshape(-1,3)
      out[name]=dict(compliance_times_E_per_mm=displacement/amp,
        relative_free_residual=float(np.max(abs(reaction[free,a]))/amp),
        force_balance=float(np.max(abs(balance.sum(axis=0)))/amp),
        moment_balance=float(np.max(abs(np.cross(xyz,balance).sum(axis=0)))/(amp*2*h)),
        energy_reaction_ratio=2*energy/work,
        top_displacement_spread_ratio=float(np.sqrt(w@((u[a::3,a]-displacement)**2)/area)/abs(displacement)),
        max_displacement_over_height=float(np.max(np.linalg.norm(u[:,a].reshape(-1,3),axis=1))/(h if kind=="short" else 2*h)))
    mu=1/(2*(1+nu));lam=nu/((1+nu)*(1-2*nu));density=.5*lam*np.trace(eps)**2+mu*np.sum(eps*eps)
    exact_volume=math.pi*r*r*h*({"short":1,"single":2,"stepped":5}[kind])
    return dict(kind=kind,n=n,nodes=len(xyz),elements=len(cells),nu=nu,volume_mm3=volume,
      exact_volume_mm3=exact_volume,relative_volume_error=volume/exact_volume-1,
      affine_patch_energy_ratio=patch_energy/(volume*density),
      top_area_relative_error=area/(math.pi*r*r)-1,
      top_load_centre_mm=[float(w@xyz[:,j]/area) for j in (0,1)],
      components=out)
