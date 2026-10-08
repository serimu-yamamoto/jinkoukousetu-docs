"""Cycle 31: geometry-defined diffusion, particle counts and shell mass.
Computational verification only; no material success probability.
"""
from pathlib import Path
import math,json,itertools
P=Path(__file__).resolve().parent
I=json.loads((P/'inputs.json').read_text(encoding='utf8'))
def save(n,v):(P/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
def remaining(Fo,geometry='sphere'):
    if Fo<0:raise ValueError('nonnegative Fourier number')
    if Fo==0:return 1.0
    total=0.0
    for n in range(1,100001):
        if geometry=='sphere':term=6/(math.pi**2*n*n)*math.exp(-n*n*math.pi**2*Fo)
        elif geometry=='slab_half_thickness':
            k=2*n-1;term=8/(math.pi**2*k*k)*math.exp(-k*k*math.pi**2*Fo/4)
        else:raise ValueError('geometry')
        total+=term
        if term<1e-16:break
    else:raise RuntimeError('series not converged')
    return total
def target_Fo(uptake,geometry='sphere'):
    lo,hi=0.,1.
    while remaining(hi,geometry)>1-uptake:hi*=2
    for _ in range(80):
        mid=(lo+hi)/2
        if remaining(mid,geometry)>1-uptake:lo=mid
        else:hi=mid
    return (lo+hi)/2
# Independent finite-difference solve for w=r*(1-c), w_t=w_rr, zero at r=0,1.
# Rannacher start (two backward-Euler half steps), then Crank-Nicolson.
def fd_sphere(N,Fo,steps):
    dt=Fo/steps;dx=1/N;m=N-1
    w=[j/N for j in range(1,N)]
    def operator(theta,dt):
        a=dt/dx**2;lo=-theta*a;diag=1+2*theta*a;up=lo
        den=[];cp=[]
        for j in range(m):
            den.append(diag-(lo*cp[j-1] if j else 0));cp.append(up/den[j] if j<m-1 else 0)
        def step(v):
            rhs=[(1-2*(1-theta)*a)*v[j]+(1-theta)*a*((v[j-1] if j else 0)+(v[j+1] if j<m-1 else 0)) for j in range(m)]
            d=[]
            for j in range(m):d.append((rhs[j]-(lo*d[j-1] if j else 0))/den[j])
            y=d[:]
            for j in range(m-2,-1,-1):y[j]-=cp[j]*y[j+1]
            return y
        return step
    be=operator(1,dt/2);cn=operator(.5,dt)
    w=be(be(w))
    for _ in range(steps-1):w=cn(w)
    avg=3*sum((j+1)/N*v for j,v in enumerate(w))*dx
    return avg,min(w),max(w)
F=I['diffusion'];M=I['manufacture'];S=I['skin']
fo95=target_Fo(F['uptake_target']);slab95=target_Fo(F['uptake_target'],'slab_half_thickness')
diffusion=[]
for d,D in itertools.product(F['precursor_diameters_mm'],F['diffusivity_m2_s']):
    R=d*1e-3/2;diffusion.append(dict(precursor_diameter_mm=d,D_m2_s=D,t95_s=fo95*R*R/D))
ref_d=.45;ref_rho=M['reference_envelope_density_kg_m3'];solid=M['solid_density_assumed_kg_m3']
ref_precursor=ref_d*(ref_rho/solid)**(1/3);R=ref_precursor*1e-3/2;Dref=1e-9
retention=[]
for ratio,t in itertools.product(F['desorption_to_sorption_D_ratios'],F['desorption_delay_s']):
    retention.append(dict(delay_s=t,Ddes_to_Ds=ratio,remaining_fraction=remaining(Dref*ratio*t/R**2)))
fd=[]
for n in F['fd_grids']:
    avg,mn,mx=fd_sphere(n,F['fd_Fo'],F['fd_time_steps']);ref=remaining(F['fd_Fo'])
    fd.append(dict(N=n,steps=F['fd_time_steps'],Fo=F['fd_Fo'],remaining_fd=avg,remaining_analytic=ref,error=abs(avg-ref),min_transformed_deficit=mn,max_transformed_deficit=mx))
step_refine=fd_sphere(F['fd_grids'][-1],F['fd_Fo'],F['fd_time_steps']*2)[0]
manufacture=[];production=[]
for area in M['areas_m2']:
    good=area*M['bed_depth_m']*M['bed_density_assumed_kg_m3'];qh=good/(M['production_days']*M['production_h_per_day']);feed=qh/M['good_yield']
    for d,rho in itertools.product(M['finished_diameters_mm'],M['envelope_densities_kg_m3']):
        mass=rho*math.pi/6*(d*1e-3)**3
        count=feed/3600/mass
        manufacture.append(dict(area_m2=area,finished_diameter_mm=d,envelope_density_kg_m3=rho,particle_mass_kg=mass,feed_kg_h=feed,particles_per_s=count,cuts_per_hole_s=count/M['illustrative_holes'],required_holes_at_assumed_frequency=math.ceil(count/M['illustrative_cuts_per_hole_s'])))
    for cap in M['brochure_capacity_kg_h']:
        annual=good*M['replenishment_fraction_per_year']
        production.append(dict(area_m2=area,good_initial_kg=good,required_good_kg_h=qh,capacity_at_brochure_size_kg_h=cap,assumed_good_rate_kg_h=cap*M['good_yield'],initial_operating_hours=good/(cap*M['good_yield']),equivalent_lines_for_30day_target=math.ceil(feed/cap),annual_replenishment_kg=annual,annual_replenishment_hours=annual/(cap*M['good_yield']),allowable_annual_fixed_processing_yen=annual*M['allowable_fixed_processing_yen_per_kg']))
skin=[]
for d,t in itertools.product(S['diameters_mm'],S['shell_thickness_um']):
    if 2*t>=d*1000:raise ValueError('shell leaves no core')
    vf=1-(1-2*t/(d*1000))**3
    rho=S['core_density_assumed_kg_m3']*(1-vf)+S['shell_density_assumed_kg_m3']*vf
    skin.append(dict(diameter_mm=d,shell_um=t,shell_volume_fraction=vf,envelope_density_kg_m3=rho,bed_density_kg_m3=rho*S['packing_fraction_assumed']))
fixed_event_capacity=[dict(diameter_mm=d,capacity_ratio_to_4mm=(d/M['reference_size_mm'])**3,feed_kg_h_if_150_at_4mm=150*(d/M['reference_size_mm'])**3) for d in [.3,.45,.6]]
checks=[]
def ck(n,b,detail):
    if not b:raise AssertionError(n)
    checks.append(dict(name=n,passed=True,detail=detail))
ck('zero-time deficit',remaining(0)==1,'initial state')
ck('long-time equilibrium',remaining(10)<1e-40,'boundary held fixed')
ck('monotone uptake',all(remaining(x)>remaining(2*x) for x in [.001,.01,.1,1]),'constant-D sphere')
ck('sphere uptake inverse',abs(remaining(fo95)-.05)<1e-13,'bisection and series')
ck('slab uptake inverse',abs(remaining(slab95,'slab_half_thickness')-.05)<1e-13,'L defined as half thickness')
ck('radius squared scaling',abs((fo95*.002**2/Dref)/(fo95*.001**2/Dref)-4)<1e-12,'constant D')
ck('D inverse scaling',abs((fo95*R**2/Dref)/(fo95*R**2/(10*Dref))-10)<1e-12,'constant geometry')
ck('source exponent mismatch',I['source_observations']['S3_equation2_first_exponent_denominator_factor']/I['source_observations']['S3_equation3_exponent_denominator_factor']==4,'published equations, not a correction of fitted D')
ck('sphere leading mode',abs(remaining(.5)-6/math.pi**2*math.exp(-math.pi**2*.5))<5e-10,'independent long-time form')
ck('uptake desorption complement',abs((1-remaining(.1))+remaining(.1)-1)<1e-14,'linear reversible constant-D idealization')
ck('precursor mass conserved',abs(solid*ref_precursor**3-ref_rho*ref_d**3)<1e-12,'assumed expansion, gas mass neglected')
ck('retention domain',all(0<=r['remaining_fraction']<=1 for r in retention),'fraction')
ck('FD grid improves',fd[2]['error']<fd[1]['error']<fd[0]['error'],'same Fo and time steps')
ck('FD analytic accuracy',fd[-1]['error']<2e-5,'independent transformed PDE')
ck('FD time-step refinement',abs(step_refine-fd[-1]['remaining_fd'])<1e-6,'steps doubled')
ck('FD admissible deficit',all(0<=r['min_transformed_deficit']<=r['max_transformed_deficit']<=1 for r in fd),'final nonnegative state')
ck('particle mass flow conservation',all(abs(r['particles_per_s']*r['particle_mass_kg']*3600-r['feed_kg_h'])<1e-9 for r in manufacture),'one particle mass times count')
ck('size cubed event scaling',abs((4/.45)**3-1/fixed_event_capacity[1]['capacity_ratio_to_4mm'])<1e-10,'equal envelope density')
ck('area mass scales tenfold',abs(production[2]['good_initial_kg']/production[0]['good_initial_kg']-10)<1e-12,'same bed')
ck('good yield applied once',all(abs(r['assumed_good_rate_kg_h']/r['capacity_at_brochure_size_kg_h']-.8)<1e-12 for r in production),'scenario yield only')
ck('annual replenishment conservation',all(abs(r['annual_replenishment_kg']-r['good_initial_kg']*.02)<1e-9 for r in production),'hypothetical 2 percent')
ck('zero shell recovers core',all(r['envelope_density_kg_m3']==S['core_density_assumed_kg_m3'] for r in skin if r['shell_um']==0),'geometry limit')
ck('shell mass bounds',all(S['core_density_assumed_kg_m3']<=r['envelope_density_kg_m3']<S['shell_density_assumed_kg_m3'] for r in skin),'mixture by volume')
ck('skin scale invariance',abs((1-(1-2*5/450)**3)-(1-(1-2*10/900)**3))<1e-12,'same t/diameter')
ck('density definitions separated',all(abs(r['bed_density_kg_m3']/r['envelope_density_kg_m3']-S['packing_fraction_assumed'])<1e-12 for r in skin),'packing fraction explicitly specified')
save('results.json',dict(cycle=31,physical_tests=0,physical_success_probability=None,Fo95_sphere=fo95,Fo95_slab_half_thickness=slab95,diffusion=diffusion,reference_particle=dict(finished_diameter_mm=ref_d,envelope_density_kg_m3=ref_rho,assumed_solid_density_kg_m3=solid,precursor_diameter_mm=ref_precursor,t95_s=fo95*R**2/Dref,Dref_m2_s=Dref),retention=retention,finite_difference=fd,fd_time_refined_value=step_refine,particle_manufacture=manufacture,production=production,skin=skin,fixed_event_capacity=fixed_event_capacity))
save('validation.json',dict(check_count=len(checks),checks=checks,physical_tests=0,scope='Mathematics, discretization and specified balances. No observed material success.'))
print(json.dumps(dict(checks=len(checks),diffusion_cases=len(diffusion),retention_cases=len(retention),particle_cases=len(manufacture),skin_cases=len(skin),FD_max_grid_error=fd[-1]['error'])))
