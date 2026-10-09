"""Normalized small-strain contact-fabric and central-particle relaxation.
Preloaded bilateral links, fixed outer endpoints; not a DEM model of a ski bed."""
import numpy as np
def strain_basis():
    out=np.zeros((6,3,3))
    for i in range(3):out[i,i,i]=1.
    for i,(a,b) in enumerate([(1,2),(0,2),(0,1)],3):out[i,a,b]=out[i,b,a]=.5
    return out
def skew(v):
    x,y,z=v
    return np.array([[0,-z,y],[z,0,-x],[-y,x,0.]])
def cone_points(half_angle_deg,tilt_deg=0.,n_mu=8,n_phi=32):
    if not 0<=half_angle_deg<=90:raise ValueError('cap angle out of range')
    c=np.cos(np.deg2rad(half_angle_deg))
    if half_angle_deg==0:n=np.array([[0.,0.,1.]]);w=np.ones(1)
    else:
        z,g=np.polynomial.legendre.leggauss(n_mu)
        z=c+(z+1)*(1-c)/2;g=g/2
        phi=2*np.pi*(np.arange(n_phi)+.5)/n_phi
        rows=[];weights=[]
        for a,b in zip(z,g):
            for p in phi:rows.append([np.sqrt(1-a*a)*np.cos(p),np.sqrt(1-a*a)*np.sin(p),a]);weights.append(b/n_phi)
        n=np.array(rows);w=np.array(weights)
    t=np.deg2rad(tilt_deg);Q=np.array([[np.cos(t),0,np.sin(t)],[0,1,0],[-np.sin(t),0,np.cos(t)]])
    n=n@Q.T
    # Antipodal links permit translation/rotation equilibrium of the central particle.
    return np.concatenate([n,-n]),np.concatenate([w/2,w/2])
def operators(n,w,kappa):
    if not 0<kappa<=1:raise ValueError('kappa must be in (0,1]')
    E=strain_basis()
    V=np.einsum('pij,nj->nip',E,n)
    K=kappa*np.eye(3)[None,:,:]+(1-kappa)*np.einsum('ni,nj->nij',n,n)
    D=np.array([np.concatenate([-np.eye(3),skew(.5*x)],axis=1) for x in n])
    C=np.einsum('n,nip,nij,njq->pq',w,V,K,V)
    B=np.einsum('n,nip,nij,nja->pa',w,V,K,D)
    H=np.einsum('n,nia,nij,njb->ab',w,D,K,D)
    Hinv=np.linalg.pinv(H,rcond=1e-12,hermitian=True)
    relaxed=C-B@Hinv@B.T
    return dict(C=(C+C.T)/2,relaxed=(relaxed+relaxed.T)/2,B=B,H=H,Hinv=Hinv,V=V,K=K,D=D,n=n,w=w)
def condensed_state(op,strain):
    strain=np.asarray(strain,dtype=float)
    q=-op['Hinv']@op['B'].T@strain
    d=np.einsum('nip,p->ni',op['V'],strain)+np.einsum('nia,a->ni',op['D'],q)
    f=np.einsum('nij,nj->ni',op['K'],d)
    energy=.5*np.einsum('n,ni,ni->',op['w'],d,f)
    residual=np.einsum('n,nia,ni->a',op['w'],op['D'],f)
    return dict(q=q,energy=float(energy),force_torque_residual=float(np.max(np.abs(residual))))
def metrics(C):
    A=float(C[2,2]);G=float(C[4,4]);B=float(C[2,4])
    scale=max(float(np.max(np.abs(C))),1e-30)
    free=A-B*B/G if G>scale*1e-10 else None
    S=np.diag([1.,1.,1.,np.sqrt(2),np.sqrt(2),np.sqrt(2)])
    eig=np.linalg.eigvalsh(S@C@S)
    return dict(Czz=A,Gxz=G,coupling=B,ratio_Czz_Gxz=A/G if G>scale*1e-10 else None,
      normal_stiffness_if_only_xz_shear_relaxed=free,
      shear_strain_per_normal_strain_at_zero_xz_stress=-B/G if G>scale*1e-10 else None,
      shear_stress_per_normal_stress_at_zero_xz_strain=B/A if A>scale*1e-10 else None,
      mandel_eigenvalues=eig.tolist(),mandel_rank=int(np.sum(eig>max(float(eig[-1]),1e-30)*1e-9)))
def axisymmetric_closed(half_angle_deg,kappa):
    c=np.cos(np.deg2rad(half_angle_deg));m2=(1+c+c*c)/3
    m4=(1+c+c*c+c**3+c**4)/5
    A=kappa*m2+(1-kappa)*m4
    G=kappa*(1+m2)/8+(1-kappa)*(m2-m4)/2
    return dict(Czz=float(A),Gxz=float(G),ratio=float(A/G))

def regular_star(name,tilt_deg=0.):
    from itertools import product
    if name=='six_axes':n=np.concatenate([np.eye(3),-np.eye(3)])
    elif name=='eight_diagonals':n=np.array(list(product([-1.,1.],repeat=3)))/np.sqrt(3)
    elif name=='twelve_icosahedral':
        g=(1+np.sqrt(5))/2
        n=np.array([[0,a,b*g] for a,b in product([-1.,1.],repeat=2)]+[[a,b*g,0] for a,b in product([-1.,1.],repeat=2)]+[[b*g,0,a] for a,b in product([-1.,1.],repeat=2)])
        n=n/np.linalg.norm(n,axis=1)[:,None]
    else:raise ValueError(name)
    t=np.deg2rad(tilt_deg);Q=np.array([[np.cos(t),0,np.sin(t)],[0,1,0],[-np.sin(t),0,np.cos(t)]])
    n=n@Q.T
    return n,np.ones(len(n))/len(n)
def random_star_average(name,kappa):
    n,w=regular_star(name);mu,gw=np.polynomial.legendre.leggauss(4)
    def rz(t):return np.array([[np.cos(t),-np.sin(t),0],[np.sin(t),np.cos(t),0],[0,0,1.]])
    avg=np.zeros((6,6));total=0.
    for z,g in zip(mu,gw/2):
        s=np.sqrt(1-z*z);Ry=np.array([[z,0,s],[0,1.,0],[-s,0,z]])
        for a in 2*np.pi*(np.arange(8)+.5)/8:
            for b in 2*np.pi*(np.arange(8)+.5)/8:
                Q=rz(a)@Ry@rz(b);wt=g/64
                avg+=wt*operators(n@Q.T,w,kappa)['relaxed'];total+=wt
    return avg,float(total)
