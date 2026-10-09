"""Variable-width ligament Q4 model; derived from cycle94's verified element.
Small-strain, 2D plane stress, clamped root. E and out-of-plane thickness are 1.
This is not a particle-bed or 50 C material model.
"""
import math
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
from scipy.integrate import quad

def width(s, wt=.5, wb=.375, tau=.1, rho=.1):
    if s <= tau: return wt
    if rho == 0 or s >= tau+rho: return wb
    f=(1-math.cos(math.pi*(s-tau)/rho))/2
    return wt-(wt-wb)*f

def integrals(tau=.1,rho=.1,wt=.5,wb=.375,g=.25,n=2):
    points=sorted(set([0.,tau,tau+rho,1.]))
    def integ(f):
        return sum(quad(f,a,b,epsabs=1e-11,epsrel=1e-11)[0]
                   for a,b in zip(points[:-1],points[1:]) if b>a)
    period=wt+g/n
    a=lambda s: period-width(s,wt,wb,tau,rho)
    return dict(axial_ratio=1/integ(lambda s:wt/width(s,wt,wb,tau,rho)),
                bending_ratio=1/(3*integ(lambda s:s*s*(wt/width(s,wt,wb,tau,rho))**3)),
                volume_ratio=integ(lambda s:width(s,wt,wb,tau,rho)/wt),
                local_flow_resistance_ratio=g**3/n*integ(lambda s:1/a(s)**3))

def element(coords,nu=.3):
    D=np.array([[1,nu,0],[nu,1,0],[0,0,(1-nu)/2]])/(1-nu**2)
    K=np.zeros((8,8));det_min=float('inf')
    for xi in [-1/math.sqrt(3),1/math.sqrt(3)]:
        for eta in [-1/math.sqrt(3),1/math.sqrt(3)]:
            dn=np.array([[-(1-eta),(1-eta),(1+eta),-(1+eta)],
                         [-(1-xi),-(1+xi),(1+xi),(1-xi)]])/4
            jac=dn@coords;det=float(np.linalg.det(jac))
            if det <= 0: raise ValueError('Inverted element')
            grad=np.linalg.solve(jac,dn)
            B=np.zeros((3,8));B[0,0::2]=grad[0];B[1,1::2]=grad[1]
            B[2,0::2]=grad[1];B[2,1::2]=grad[0]
            K+=B.T@D@B*det;det_min=min(det_min,det)
    return K,det_min

def solve(height,tau,rho,nu,nx,ny,uniform=False):
    wt=.5;wb=wt if uniform else .375
    # y=0 is root, y=height is loaded top; s measures depth from top.
    coords=np.array([[(ix/nx-.5)*width(1-iy/ny,wt,wb,tau,rho),height*iy/ny]
                     for iy in range(ny+1) for ix in range(nx+1)])
    rr=[];cc=[];vv=[];mindet=float('inf')
    for iy in range(ny):
        for ix in range(nx):
            n0=iy*(nx+1)+ix
            ids=np.array([n0,n0+1,n0+nx+2,n0+nx+1])
            dofs=np.array([[2*i,2*i+1] for i in ids]).ravel()
            ke,det=element(coords[ids],nu);mindet=min(mindet,det)
            rr.extend(np.repeat(dofs,8));cc.extend(np.tile(dofs,8));vv.extend(ke.ravel())
    N=2*len(coords);K=coo_matrix((vv,(rr,cc)),shape=(N,N)).tocsr()
    root=np.arange(2*(nx+1));top=np.arange(ny*(nx+1),(ny+1)*(nx+1))
    out=dict(min_jacobian=mindet,ndof=N)
    amplitude=1e-6*height
    for name,axis in [('normal',1),('lateral',0)]:
        driven=2*top+axis;fixed=np.r_[root,driven]
        free=np.setdiff1d(np.arange(N),fixed)
        u=np.zeros(N);u[driven]=amplitude
        u[free]=spsolve(K[free,:][:,free],-K[free,:][:,fixed]@u[fixed])
        force=K@u;reaction=float(force[driven].sum());stiffness=reaction/amplitude
        norm=max(abs(reaction),1e-30)
        out[name]=dict(stiffness=stiffness,energy=float(.5*u@force),
            relative_free_residual=float(np.max(np.abs(force[free]))/norm),
            relative_force_balance=float(np.max(np.abs(force.reshape(-1,2).sum(axis=0)))/norm),
            relative_cross_reaction=float(abs(force[2*top+(1-axis)].sum())/norm))
    return out
