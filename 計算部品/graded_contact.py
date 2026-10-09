"""Reusable graded compression-only contact, extending cycle102 geometry."""
from pathlib import Path
import importlib.util
s=importlib.util.spec_from_file_location('handover_base',Path(__file__).with_name('handover_contacts.py'))
base=importlib.util.module_from_spec(s);s.loader.exec_module(base)

def segments(u,gamma,a,edge):
    if not 0<=a<=.5 or not 0<=edge<=1:raise ValueError('invalid grading')
    xc=u+(1+gamma)/2;out=[]
    for label,lo,hi in base.overlap_intervals(u,gamma):
        cuts=[lo,hi]
        transition=1-a-xc if label=='A' else 1+gamma+a-xc
        if a and lo<transition<hi:cuts.append(transition)
        cuts=sorted(cuts)
        for left,right in zip(cuts,cuts[1:]):
            mid=(left+right)/2;x=mid+xc
            distance=1-x if label=='A' else x-1-gamma
            if not a or distance>=a:
                k=1.;slope=0.
            else:
                k=edge+(1-edge)*max(0.,distance)/a
                slope=-(1-edge)/a if label=='A' else (1-edge)/a
            out.append((label,left,right,k-slope*mid,slope))
    return out

def integrals(parts,q):
    rows=[]
    for label,left,right,c0,c1 in parts:
        if q>0:left=max(left,-1/q)
        elif q<0:right=min(right,-1/q)
        if right<=left:continue
        m=(left+right)/2;hh=(right-left)/2
        km=c0+c1*m;vm=1+q*m
        i0=2*hh*km*vm+2*hh**3*c1*q/3
        i1=m*i0+2*hh**3*(km*q+c1*vm)/3
        i2=2*hh*km*vm*vm+2*hh**3*(km*q*q+2*c1*vm*q)/3
        points=[left,right]
        if c1*q:
            vertex=-(c0*q+c1)/(2*c1*q)
            if left<vertex<right:points.append(vertex)
        peak=max(max(0.,(c0+c1*r)*(1+q*r)) for r in points)
        rows.append(dict(label=label,i0=i0,i1=i1,i2=i2,peak=peak,active_length=right-left))
    return rows

def solve(parts,force=1.,scale=1.):
    if force<=0 or scale<=0:raise ValueError('positive inputs')
    def moment(q):return sum(x['i1'] for x in integrals(parts,q))
    lo=-1.;hi=1.
    for _ in range(80):
        if moment(lo)<=0<=moment(hi):break
        if moment(lo)>0:lo*=2
        if moment(hi)<0:hi*=2
    else:raise ArithmeticError('no finite bracket')
    for _ in range(80):
        m=(lo+hi)/2
        if moment(m)<0:lo=m
        else:hi=m
    q=(lo+hi)/2;r=integrals(parts,q)
    S=sum(x['i0'] for x in r)
    if S<=0:raise ArithmeticError('no support')
    d=force/(scale*S);theta=q*d
    by={lab:sum(scale*d*x['i0'] for x in r if x['label']==lab) for lab in ['A','B']}
    return dict(delta=d,theta=theta,force=sum(by.values()),moment=scale*d*sum(x['i1'] for x in r),
                energy=.5*scale*d*d*sum(x['i2'] for x in r),peak_line_load=scale*d*max(x['peak'] for x in r),
                B_force=by['B'],active_length=sum(x['active_length'] for x in r))

def profile_segments(u,gamma,knots):
    """Piecewise-linear stiffness versus distance from each pad's inner edge."""
    import bisect
    if knots[0][0]!=0 or knots[-1][0]!=1:raise ValueError('profile endpoints')
    if any(b[0]<=a[0] for a,b in zip(knots,knots[1:])):raise ValueError('sorted distinct knots')
    xc=u+(1+gamma)/2;out=[];xs=[v[0] for v in knots]
    for label,left,right in base.overlap_intervals(u,gamma):
        cuts=[left,right]
        for s,k in knots[1:-1]:
            r=(1-s if label=='A' else 1+gamma+s)-xc
            if left<r<right:cuts.append(r)
        cuts=sorted(cuts)
        for a,b in zip(cuts,cuts[1:]):
            m=(a+b)/2;x=m+xc
            distance=1-x if label=='A' else x-1-gamma
            j=max(0,min(len(knots)-2,bisect.bisect_right(xs,distance)-1))
            s0,k0=knots[j];s1,k1=knots[j+1]
            ds=(k1-k0)/(s1-s0);km=k0+ds*(distance-s0)
            dr=-ds if label=='A' else ds
            out.append((label,a,b,km-dr*m,dr))
    return out
