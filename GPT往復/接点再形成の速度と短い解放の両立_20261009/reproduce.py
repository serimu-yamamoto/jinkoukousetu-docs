"""Cycle 88. Contact renewal diagnostic; no material properties fitted or tested."""
from pathlib import Path
from collections import deque
import json,math,hashlib
P=Path(__file__).resolve().parent
R=P.parents[1]
def read(n):return json.loads((P/n).read_text(encoding='utf8'))
def write(n,x):(P/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
def steady(dc,v,tau):
    r=v*tau/dc
    q=1/(1+r)
    return dict(sliding_wait_ratio=r,attached_fraction=q,mean_residual_over_initial_peak=.5*q,
                dimensionless_event_flux=1/(1+r))
def trace(r,M,end_u=30,sample_every=10,rebinding=True):
    # Age grid x/dc=j/M. Births occur at the end of each increment.
    du=1/M
    h=-math.expm1(-du/r) if rebinding else 0.
    cells=deque([1.]+[0.]*(M-1))
    q,U,m1,m2=1.,0.,0.,0.
    work,released=0.,0.
    max_balance,max_mass,max_negative=0.,0.,0.
    samples=[dict(u=0.,force_ratio=0.,attached_fraction=1.,work=0.,released=0.,stored=0.)]
    tail=[]
    steps=round(end_u*M)
    for j in range(1,steps+1):
        work+=du*m1+.5*du*du*q
        m2+=2*du*m1+du*du*q
        m1+=du*q
        expired=cells.pop()
        m1-=expired;m2-=expired;q-=expired;U+=expired
        released+=.5*expired
        born=U*h
        U-=born;q+=born;cells.appendleft(born)
        err=work-released-.5*m2
        max_balance=max(max_balance,abs(err))
        max_mass=max(max_mass,abs(q+U-1))
        max_negative=max(max_negative,-min(m1,m2,q,U))
        if j>steps-20*M:tail.append(m1)
        if j%sample_every==0:
            samples.append(dict(u=j*du,force_ratio=m1,attached_fraction=q,work=work,
                                released=released,stored=.5*m2))
    return dict(r=r,grid_cells=M,end_u=end_u,
                final_force_ratio=m1,tail_average_force_ratio=math.fsum(tail)/len(tail),
                max_energy_balance_error=max_balance,max_mass_error=max_mass,
                negative_roundoff=max_negative,samples=samples)
def run():
    I=read('inputs.json');checks=[]
    def ck(n,b):
        if not b:raise AssertionError(n)
        checks.append(dict(name=n,passed=True))
    def near(a,b,rel=1e-10,abs_=1e-12):return math.isclose(a,b,rel_tol=rel,abs_tol=abs_)
    for s in I['prior_paths']:
        t=(R/s['path']).read_text(encoding='utf8').replace('\r\n','\n').rstrip()+'\n'
        ck('prior_hash_'+Path(s['path']).stem,hashlib.sha256(t.encode()).hexdigest()==s['sha256_lf'])
    results=[]
    for dc_um in I['release_distance_um_assumed']:
        for v in I['local_slip_speed_m_s_assumed']:
            for tau in I['off_wait_s_assumed']:
                results.append(dict(release_distance_um_assumed=dc_um,local_slip_speed_m_s_assumed=v,
                                    off_wait_s_assumed=tau,**steady(dc_um*1e-6,v,tau),
                                    actual_snow_equivalence=None,actual_50C_rates=None))
    ck('60_steady_cases',len(results)==60)
    ck('attached_bounds',all(0<x['attached_fraction']<1 for x in results))
    ck('renewal_flux_balance',all(near(x['attached_fraction'],x['dimensionless_event_flux']) for x in results))
    ck('half_force_from_uniform_attached_age',all(near(x['mean_residual_over_initial_peak'],x['attached_fraction']/2) for x in results))
    # Independent event-time calculation: one spring accumulates energy Fc*dc/2 per cycle.
    ck('cycle_work_force_identity',all(near((.5*x['release_distance_um_assumed']*1e-6)/
       (x['release_distance_um_assumed']*1e-6+x['local_slip_speed_m_s_assumed']*x['off_wait_s_assumed']),
       x['mean_residual_over_initial_peak']) for x in results))
    A=1/(2*I['residual_ratio_max_assumed'])-1
    B=-math.log1p(-I['recovered_fraction_min_assumed'])
    windows=[]
    for dc_um in I['release_distance_um_assumed']:
        for v in I['local_slip_speed_m_s_assumed']:
            for T in I['rest_time_s_assumed']:
                lower=dc_um*1e-6*A/v
                upper=T/B
                windows.append(dict(release_distance_um_assumed=dc_um,local_slip_speed_m_s_assumed=v,
                 rest_time_s_assumed=T,minimum_sliding_wait_s=lower,maximum_rest_wait_s=upper,
                 one_rate_necessary_window_exists=lower<=upper,availability_assumed=1,
                 empirical_pass_or_fail=None))
    ck('48_inverse_cases',len(windows)==48)
    ck('inverse_residual_boundary',all(near(steady(x['release_distance_um_assumed']*1e-6,
      x['local_slip_speed_m_s_assumed'],x['minimum_sliding_wait_s'])['mean_residual_over_initial_peak'],
      I['residual_ratio_max_assumed']) for x in windows))
    ck('inverse_rest_boundary',all(near(-math.expm1(-x['rest_time_s_assumed']/x['maximum_rest_wait_s']),
       I['recovered_fraction_min_assumed']) for x in windows))
    availability=[]
    for eta in I['availability_assumed']:
        for T in I['rest_time_s_assumed']:
            q=eta*-math.expm1(-T/I['reset_wait_s_assumed'])
            availability.append(dict(available_partner_fraction_assumed=eta,rest_time_s_assumed=T,
              reset_wait_s_assumed=I['reset_wait_s_assumed'],reformed_fraction_after_full_release=q,
              meets_provisional_fraction=(eta>I['recovered_fraction_min_assumed'] and q>=I['recovered_fraction_min_assumed']),
              actual_recovered_bed_strength=None))
    ck('16_partner_cases',len(availability)==16)
    ck('partner_ceiling',all(x['reformed_fraction_after_full_release']<=x['available_partner_fraction_assumed'] for x in availability))
    ck('95_percent_availability_insufficient_at_finite_time',all(not x['meets_provisional_fraction'] for x in availability if x['available_partner_fraction_assumed']<=.95))
    gates=[]
    for dc_um in I['release_distance_um_assumed']:
        for v in I['local_slip_speed_m_s_assumed']:
            alpha_max=min(1.,v*I['reset_wait_s_assumed']/(dc_um*1e-6*A))
            gates.append(dict(release_distance_um_assumed=dc_um,local_slip_speed_m_s_assumed=v,
              reset_wait_s_assumed=I['reset_wait_s_assumed'],maximum_sliding_to_rest_attachment_rate_ratio=alpha_max,
              required_rate_suppression_factor=1/alpha_max,
              equivalent_mean_no_capture_slip_distance_um=A*dc_um,
              mechanism_demonstrated=False,actual_alpha=None))
    ck('12_gating_constraints',len(gates)==12)
    ck('gating_boundary',all(steady(x['release_distance_um_assumed']*1e-6,x['local_slip_speed_m_s_assumed'],
       x['reset_wait_s_assumed']/x['maximum_sliding_to_rest_attachment_rate_ratio'])['mean_residual_over_initial_peak']<=I['residual_ratio_max_assumed']*(1+1e-12) for x in gates))
    numeric=[];curves=[]
    for r in I['dimensionless_ratios_for_numeric']:
        for M in I['grid_cells']:
            end=max(100,20*(1+r))
            z=trace(r,M,end,sample_every=max(1,round(end*M/300)))
            target=.5/(1+r)
            err=abs(z['tail_average_force_ratio']/target-1)
            h=-math.expm1(-1/(M*r))
            discrete=h*(M-1)/(2*(1+(M-1)*h))
            numeric.append(dict(r=r,grid_cells=M,analytic_continuum_force=target,
             discrete_stationary_force=discrete,simulated_tail_force=z['tail_average_force_ratio'],
             relative_continuum_error=err,max_energy_balance_error=z['max_energy_balance_error'],
             max_mass_error=z['max_mass_error'],negative_roundoff=z['negative_roundoff'],
             simulation_steps=round(end*M)))
    ck('8_age_grid_cases',len(numeric)==8)
    ck('cohort_mass_conservation',max(x['max_mass_error'] for x in numeric)<1e-9)
    ck('cohort_energy_conservation',max(x['max_energy_balance_error'] for x in numeric)<1e-8)
    ck('nonnegative_population_and_moments',max(x['negative_roundoff'] for x in numeric)<1e-9)
    ck('cohort_agrees_with_discrete_stationary_solution',all(near(x['simulated_tail_force'],x['discrete_stationary_force'],1e-6) for x in numeric))
    ck('cohort_converges_to_continuum',all(
      next(x['relative_continuum_error'] for x in numeric if x['r']==r and x['grid_cells']==400)<
      next(x['relative_continuum_error'] for x in numeric if x['r']==r and x['grid_cells']==200) for r in I['dimensionless_ratios_for_numeric']))
    ck('400_cells_continuum_error_under_0_3_percent',max(x['relative_continuum_error'] for x in numeric if x['grid_cells']==400)<.003)
    one=trace(1.,400,10,sample_every=20,rebinding=False)
    ck('single_release_work_half_and_no_residual',near(one['samples'][-1]['work'],.5,1e-8) and abs(one['final_force_ratio'])<1e-10)
    for r in [.1,1.,10.]:
        curves.append(dict(label='r='+str(r),**trace(r,400,20,sample_every=20)))
    curves.append(dict(label='no_rebinding',**trace(1.,400,20,sample_every=20,rebinding=False)))
    ck('rapid_rebinding_adds_work',curves[0]['samples'][-1]['work']>curves[-1]['samples'][-1]['work']*10)
    low=next(x for x in windows if x['release_distance_um_assumed']==100 and x['local_slip_speed_m_s_assumed']==.001 and x['rest_time_s_assumed']==.5)
    fast=next(x for x in windows if x['release_distance_um_assumed']==100 and x['local_slip_speed_m_s_assumed']==.01 and x['rest_time_s_assumed']==.5)
    ck('same_rate_low_speed_conflict',not low['one_rate_necessary_window_exists'] and fast['one_rate_necessary_window_exists'])
    ck('no_measured_probability',I['physical_experiments']==0 and I['success_probability'] is None)
    for name,data in [('steady_renewal.json',results),('rate_windows.json',windows),
       ('partner_availability.json',availability),('gating_requirements.json',gates),
       ('numerical_validation.json',numeric),('transient_curves.json',curves),('checks.json',checks)]:write(name,data)
    summary=dict(cycle=88,numeric_checks=len(checks),calculation_rows=len(results)+len(windows)+len(availability)+len(gates)+len(numeric),
       curve_sample_rows=sum(len(x['samples']) for x in curves),physical_experiments=0,success_probability=None,
       provider_contacts_sent=0,orders_placed=0,equipment_secured=False,actual_50C_rates=None,
       actual_total_manufacturing_cost_yen=None,actual_snow_residual_target=None,
       numerical_model='equal independent linear contacts; deterministic slip release; exponential waiting; rigid imposed local slip',
       not_included=['ski-base friction','force-chain geometry','normal contact coupling','strain softening inside individual arms','wet adhesion','creep','aging','snow equivalence'])
    write('summary.json',summary);print(json.dumps(summary))
if __name__=='__main__':run()
