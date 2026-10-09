"""Connected shrinking patches with finite axial gap springs.
Reuses the verified tridiagonal solver and geometry of cycle129.
Ice growth, ice constitutive properties and fracture are not predicted.
"""
import math
from shrinkage_patches import geometry,check_positive,solve_tridiagonal
def prepared(E,t,k,eps,L,g,N,beta):
    check_positive(E,t,k,L)
    if not math.isfinite(eps) or eps>0 or not math.isfinite(beta) or beta<0:raise ValueError("shrink strain<=0 and bridge ratio>=0")
    z=geometry(L,g,N);lam=math.sqrt(E*t/k);a=z['half_patch_m'];c=2*a/lam
    if c>300:raise ValueError("large aspect ratio")
    return z,lam,a,E*t,beta*E*t/L
def condensed(E,t,k,eps,L,g,N,beta,qbar):
    z,lam,a,Et,Kb=prepared(E,t,k,eps,L,g,N,beta)
    if not math.isfinite(qbar):raise ValueError("finite load required")
    q=qbar/z['coverage'];c=2*a/lam;fac=Et/(lam*math.sinh(c));dd=fac*math.cosh(c);oo=-fac
    diag=[0.]*(2*N);off=[0.]*(2*N-1);rhs=[0.]*(2*N)
    for i in range(N):
        j=2*i;diag[j]+=dd;diag[j+1]+=dd;off[j]+=oo;rhs[j]-=Et*eps;rhs[j+1]+=Et*eps
        if i<N-1:diag[j+1]+=Kb;diag[j+2]+=Kb;off[j+1]-=Kb
    w=solve_tridiagonal(diag,off,rhs);peak_tau=0.;peak_stress=0.;energy=0.;waterless_reaction=0.
    for i in range(N):
        wl,wr=w[2*i:2*i+2];A=(wl+wr)/(2*math.cosh(a/lam));B=(wr-wl)/(2*math.sinh(a/lam))
        tp=[-a,a];sp=[-a,a]
        if A and abs(B/A)<1:
            x=lam*math.atanh(-B/A)
            if -a<x<a:tp.append(x)
        if B and abs(A/B)<1:
            x=lam*math.atanh(-A/B)
            if -a<x<a:sp.append(x)
        peak_tau=max(peak_tau,*[abs(q+k*(A*math.cosh(x/lam)+B*math.sinh(x/lam))) for x in tp])
        peak_stress=max(peak_stress,*[E*((A*math.sinh(x/lam)+B*math.cosh(x/lam))/lam-eps) for x in sp])
        integral_w=(wl+wr)*lam*math.tanh(a/lam)
        waterless_reaction+=k*integral_w
        energy+=.5*(dd*(wl*wl+wr*wr)+2*oo*wl*wr)-Et*eps*(wr-wl)+Et*eps*eps*a+q*integral_w+q*q*a/k
    jumps=[w[2*i+2]-w[2*i+1] for i in range(N-1)]
    bridge_energy=sum(.5*Kb*j*j for j in jumps);energy+=bridge_energy
    return dict(geometry=z,q_local_Pa=q,bridge_K_Pa=Kb,
                peak_interface_shear_Pa=peak_tau,peak_tensile_Pa=peak_stress,
                total_stored_J_per_m_width=energy,bridge_stored_J_per_m_width=bridge_energy,
                bridge_extensions_m=jumps,shrink_reaction_N_per_m_width=waterless_reaction,
                endpoint_w_m=w,bridge_force_N_per_m_width=[Kb*j for j in jumps])
def full_fe(E,t,k,eps,L,g,N,beta,qbar,n):
    z,lam,a,Et,Kb=prepared(E,t,k,eps,L,g,N,beta)
    if not isinstance(n,int) or n<2 or not math.isfinite(qbar):raise ValueError("invalid mesh/load")
    q=qbar/z['coverage'];nn=N*(n+1);diag=[0.]*nn;off=[0.]*(nn-1);rhs=[0.]*nn;dx=2*a/n
    for p in range(N):
        base=p*(n+1)
        for i in range(n):
            j=base+i;diag[j]+=Et/dx+k*dx/3;diag[j+1]+=Et/dx+k*dx/3;off[j]+=-Et/dx+k*dx/6
            rhs[j]-=Et*eps;rhs[j+1]+=Et*eps
        if p<N-1:
            j=base+n;diag[j]+=Kb;diag[j+1]+=Kb;off[j]-=Kb
    w=solve_tridiagonal(diag,off,rhs);energy=0.;reaction=0.;peak_stress=0.
    for p in range(N):
        base=p*(n+1)
        for i in range(n):
            j=base+i;ul=w[j]+q/k;ur=w[j+1]+q/k;strain=(w[j+1]-w[j])/dx-eps
            peak_stress=max(peak_stress,E*strain)
            energy+=.5*Et*strain*strain*dx+.5*k*dx*(ul*ul+ul*ur+ur*ur)/3
            reaction+=k*dx*(w[j]+w[j+1])/2
        if p<N-1:
            j=base+n;energy+=.5*Kb*(w[j+1]-w[j])**2
    ends=[w[p*(n+1)+i] for p in range(N) for i in [0,n]]
    return dict(peak_interface_shear_Pa=max(abs(q+k*x) for x in w),
                peak_tensile_Pa=peak_stress,total_stored_J_per_m_width=energy,
                shrink_reaction_N_per_m_width=reaction,endpoint_w_m=ends)
