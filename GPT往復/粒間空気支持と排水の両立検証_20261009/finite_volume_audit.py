"""Independent finite-volume check of the SAME assumed PDE; not physical validation."""
from pathlib import Path
import sys,json
D=Path(__file__).resolve().parent
sys.path.insert(0,str(D.parents[1]/'.deps'))
import numpy as np
from reproduce import P,air_gain,writej
def axis_modes(n,length,diffusion):
    dx=length/n
    a=np.diag(np.full(n,2.))+np.diag(np.full(n-1,-1.),1)+np.diag(np.full(n-1,-1.),-1)
    a[0,0]=1.;a[-1,-1]=3.
    values,vectors=np.linalg.eigh(a*diffusion/(dx*dx))
    return values,vectors
def fv(p,n):
    fac=p['p0']/(p['phi']*p['mu_air'])
    ly,vy=axis_modes(n,p['width']/2,p['ky']*fac)
    lz,vz=axis_modes(n,p['H'],p['kz']*fac)
    wy=vy.mean(axis=0)*(vy.T@np.ones(n))
    wz=vz[0,:]*(vz.T@np.ones(n))
    lam=ly[:,None]+lz[None,:]
    T=p['L']/p['V'];z=lam*T
    f=1+np.expm1(-z)/z
    return p['p0']/(p['phi']*p['H']*T)*float(np.sum(wy[:,None]*wz[None,:]*f/lam))
def main():
    rows=[]
    for case,ch in [('reference',{}),('vertical_drain',{'ky':5.663155510250313e-13,'kz':5.663155510250312e-12}),('shallow',{'H':.01})]:
        p={**P,**ch};ref=air_gain(p,256)
        errors=[]
        for n in [16,32,64]:
            val=fv(p,n);err=abs(val-ref)/ref
            errors.append(err)
            rows.append(dict(case=case,cells_each_axis=n,spectral_reference=ref,finite_volume=val,relative_error=err))
        assert errors[-1]<.001 and errors[0]>errors[1]>errors[2],(case,errors)
    writej('numerical_audit.json',{'scope':'same PDE; independent spatial discretization and exact time integration; no measured validation',
        'rows':rows,'case_count':3,'checks':6,'all_passed':True})
    print(json.dumps({'cases':3,'checks':6,'max_64cell_relative_error':max(r['relative_error'] for r in rows if r['cells_each_axis']==64)}))
if __name__=='__main__':main()
