"""Small-strain shear-transfer model for disconnected shrinking patches.
No material calibration, freeze kinetics or failure criterion is supplied.
"""
import math
def check_positive(*xs):
    if any(not math.isfinite(x) or x<=0 for x in xs):raise ValueError("positive finite required")
def geometry(length,gap,count):
    check_positive(length)
    if not math.isfinite(gap) or gap<0 or not isinstance(count,int) or count<1:raise ValueError("invalid geometry")
    wet=length-(count-1)*gap
    if wet<=0:raise ValueError("no patch area")
    return dict(wet_length_m=wet,coverage=wet/length,half_patch_m=wet/(2*count))
def analytic(E,t,k,eps,a,q):
    check_positive(E,t,k,a)
    if not math.isfinite(eps) or not math.isfinite(q):raise ValueError("invalid strain/load")
    lam=math.sqrt(E*t/k);alpha=a/lam
    if alpha>300:raise ValueError("unsupported extreme aspect ratio")
    peak_stress=E*abs(eps)*(1-1/math.cosh(alpha))
    shrink_tau=E*t*abs(eps)/lam*math.tanh(alpha)
    stored=E*t*eps**2*(a-lam*math.tanh(alpha))+q*q*a/k
    return dict(lambda_m=lam,alpha=alpha,peak_tensile_Pa=peak_stress,
                peak_abs_interface_shear_Pa=abs(q)+shrink_tau,
                shrink_shear_Pa=shrink_tau,stored_J_per_m_width=stored)
def displacement(x,E,t,k,eps,a,q):
    z=analytic(E,t,k,eps,a,q);lam=z['lambda_m']
    return q/k+eps*lam*math.sinh(x/lam)/math.cosh(a/lam)
def stress(x,E,t,k,eps,a,q):
    z=analytic(E,t,k,eps,a,q);lam=z['lambda_m']
    return E*eps*(math.cosh(x/lam)/math.cosh(a/lam)-1)
def solve_tridiagonal(diag,off,rhs):
    n=len(diag)
    if len(off)!=n-1 or len(rhs)!=n:raise ValueError("shape")
    d=list(diag);b=list(rhs)
    for i in range(1,n):
        if d[i-1]<=0:raise ValueError("nonpositive pivot")
        ratio=off[i-1]/d[i-1];d[i]-=ratio*off[i-1];b[i]-=ratio*b[i-1]
    if d[-1]<=0:raise ValueError("nonpositive pivot")
    u=[0.]*n;u[-1]=b[-1]/d[-1]
    for i in range(n-2,-1,-1):u[i]=(b[i]-off[i]*u[i+1])/d[i]
    return u
def finite_elements(E,t,k,eps,a,q,n):
    analytic(E,t,k,eps,a,q)
    if not isinstance(n,int) or n<2:raise ValueError("invalid mesh")
    dx=2*a/n;Et=E*t;diag=[0.]*(n+1);off=[0.]*n;rhs=[0.]*(n+1)
    for i in range(n):
        d=Et/dx+k*dx/3;o=-Et/dx+k*dx/6
        diag[i]+=d;diag[i+1]+=d;off[i]=o
        rhs[i]+=q*dx/2-Et*eps;rhs[i+1]+=q*dx/2+Et*eps
    u=solve_tridiagonal(diag,off,rhs);xs=[-a+i*dx for i in range(n+1)]
    sig=[E*((u[i+1]-u[i])/dx-eps) for i in range(n)]
    reaction=sum(k*dx*(u[i]+u[i+1])/2 for i in range(n))
    energy=sum(.5*Et*((u[i+1]-u[i])/dx-eps)**2*dx
               +.5*k*dx*(u[i]**2+u[i]*u[i+1]+u[i+1]**2)/3 for i in range(n))
    residual=[]
    for i in range(n+1):
        v=diag[i]*u[i]-rhs[i]
        if i>0:v+=off[i-1]*u[i-1]
        if i<n:v+=off[i]*u[i+1]
        residual.append(v)
    return dict(x=xs,u=u,stress_mid=sig,
                peak_abs_interface_shear_Pa=max(abs(k*z) for z in u),
                reaction_N_per_m_width=reaction,stored_J_per_m_width=energy,
                residual_max=max(abs(x) for x in residual))
