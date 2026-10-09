"""Reusable frictionless handover models. Uncalibrated, small-rotation surrogate."""
import math

def positive_integrals(intervals,q):
    """Integrals of max(1+q*r,0), r*..., its square; lengths/peaks by patch."""
    rows=[]
    for label,a,b in intervals:
        if q>0:a=max(a,-1/q)
        elif q<0:b=min(b,-1/q)
        if b<=a:
            rows.append(dict(label=label,active_length=0.,i0=0.,i1=0.,i2=0.,peak=0.))
            continue
        j0=b-a;j1=(b*b-a*a)/2;j2=(b**3-a**3)/3
        rows.append(dict(label=label,active_length=j0,i0=j0+q*j1,
                         i1=j1+q*j2,i2=j0+2*q*j1+q*q*j2,
                         peak=max(1+q*a,1+q*b),a=a,b=b))
    return rows

def overlap_intervals(u,gamma):
    """L=1, pad A=[0,1], B=[1+g,2+g], window=[u,u+1+g]."""
    if not 0<=u<=1 or gamma<0:raise ValueError('outside stroke')
    xc=u+(1+gamma)/2
    out=[]
    for label,a,b in [('A',0.,1.),('B',1+gamma,2+gamma)]:
        lo=max(u,a);hi=min(u+1+gamma,b)
        if hi>lo:out.append((label,lo-xc,hi-xc))
    return out

def normal_contact(intervals,force=1.,density=1.,rotation_free=True):
    """Rigid footprint over independent compression-only linear columns.
    density=k_per_area*b. r=distance from normal-load line. No tangential force.
    """
    if force<=0 or density<=0:raise ValueError('positive force/stiffness required')
    if rotation_free:
        if min(a for _,a,b in intervals)>=0 or max(b for _,a,b in intervals)<=0:
            return dict(status='no_finite_equilibrium')
        def moment(q):return sum(v['i1'] for v in positive_integrals(intervals,q))
        lo=-1.;hi=1.
        for _ in range(80):
            if moment(lo)<=0<=moment(hi):break
            if moment(lo)>0:lo*=2
            if moment(hi)<0:hi*=2
        else:raise ArithmeticError('failed to bracket rocking contact')
        for _ in range(90):
            mid=(lo+hi)/2
            if moment(mid)<0:lo=mid
            else:hi=mid
        q=(lo+hi)/2
    else:q=0.
    rows=positive_integrals(intervals,q)
    area=sum(v['i0'] for v in rows)
    delta=force/(density*area);theta=q*delta
    reactions=[dict(label=v['label'],force=density*delta*v['i0'],
                    moment=density*delta*v['i1'],
                    active_length=v['active_length'],
                    peak_line_load=density*delta*v['peak']) for v in rows]
    U=.5*density*delta*delta*sum(v['i2'] for v in rows)
    return dict(status='equilibrium',delta=delta,theta=theta,q=q,
                force=sum(r['force'] for r in reactions),
                moment=sum(r['moment'] for r in reactions),
                energy=U,active_length=sum(v['active_length'] for v in rows),
                peak_line_load=max(v['peak'] for v in rows)*density*delta,
                reactions=reactions)

def cam_state(w,eta,c):
    """Two prescribed vertical compliant contact profiles; k=F0=delta0=1.
    y/upwards; eta=F/F0; c=common profile compensation.
    Requires a rotation constraint; moments not represented.
    """
    hA=1-w+c*w*(1-w);hB=w+c*w*(1-w)
    if hA-hB>=eta:y=hA-eta
    elif hB-hA>=eta:y=hB-eta
    else:y=(hA+hB-eta)/2
    a=max(0.,hA-y);b=max(0.,hB-y)
    da=-1+c*(1-2*w);db=1+c*(1-2*w)
    Q=a*da+b*db
    U=.5*(a*a+b*b)
    return dict(w=w,y=y,A=a,B=b,Q=Q,potential=U+eta*y,
                total_normal=a+b,energy=U,hA=hA,hB=hB)
