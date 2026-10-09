"""Cycle 74: kinematic dry-air screening, NOT ski/material validation.
Run with Python 3.10+. No third-party packages for this file.
"""
from pathlib import Path
from math import pi, cos, expm1, exp, cosh, isfinite
import csv, json, hashlib
D=Path(__file__).resolve().parent
P=dict(M=70.,g=9.81,theta_deg=30.,L=1.5,width=.1,n_skis=2,
       H=.05,phi=.9,p0=101325.,mu_air=1.95e-5,Ed=20000.,
       ky=3e-12,kz=3e-12,V=10.,mu_solid=.1,mu_water=.001,rho_water=1000.)
N=128
def writej(name,data):
    (D/name).write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
def writecsv(name,rows):
    with (D/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
def F(z):
    if z<1e-3:return z/2-z*z/6+z**3/24-z**4/120+z**5/720
    return 1+expm1(-z)/z
def air_gain(p,N=N):
    b=p['width']/2;H=p['H'];T=p['L']/p['V']
    fac=p['p0']/(p['phi']*p['mu_air'])
    total=0.
    for n in range(N):
        nn=2*n+1;qy=nn*pi/(2*b);an=8/(pi*pi*nn*nn)
        for m in range(N):
            mm=2*m+1;qz=mm*pi/(2*H);bm=4*(-1 if m%2 else 1)/(pi*mm)
            lam=fac*(p['ky']*qy*qy+p['kz']*qz*qz)
            total+=an*bm*F(lam*T)/lam
    return p['p0']/(p['phi']*H*T)*total
def steady_gain(p,N=N):
    # Coefficient mean top pressure / compression rate delta/T.
    b=p['width']/2;H=p['H'];s=0.
    for n in range(N):
        nn=2*n+1;q=nn*pi/(2*b);an=8/(pi*pi*nn*nn)
        z=q*H*(p['ky']/p['kz'])**.5
        sech=1/cosh(z) if z<700 else 0
        s+=an*(1-sech)/(p['ky']*q*q)
    return p['mu_air']/H*s
def steady_double(p,N=N):
    b=p['width']/2;H=p['H'];s=0
    for n in range(N):
        nn=2*n+1;q=nn*pi/(2*b);an=8/(pi*pi*nn*nn)
        for m in range(N):
            mm=2*m+1;r=mm*pi/(2*H);bm=4*(-1 if m%2 else 1)/(pi*mm)
            s+=an*bm/(p['ky']*q*q+p['kz']*r*r)
    return p['mu_air']/H*s
def solve(**changes):
    p={**P,**changes}
    G=air_gain(p);Ks=p['Ed']/(2*p['H'])
    pn=p['M']*p['g']*cos(p['theta_deg']*pi/180)/(p['n_skis']*p['width']*p['L'])
    delta=pn/(Ks+G);fa=G/(Ks+G);strain=delta/p['H']
    q=p['kz']*p['rho_water']*p['g']/p['mu_water']*3.6e6
    return {**p,'pn_Pa':pn,'air_gain_Pa_per_m':G,'air_load_fraction':fa,
            'delta_mm':1000*delta,'strain':strain,'pressure_upper_ratio':strain/p['phi'],
            'mu_diagnostic':p['mu_solid']*(1-fa)+delta/p['L'],
            'clean_saturated_drain_mm_h':q,
            'within_small_strain_and_pressure_screen':strain<=.1 and strain/p['phi']<=.1}
def main():
    writej('inputs.json',{'status':'hypothetical parameters, no physical experiment','parameters':P,
        'modes_each_axis':N,'air_model_state':'dry; saturated water calculation separate',
        'winter_storm_design_intensity':'unmeasured site-specific; 100/200 mm/h scenarios only'})
    baseline=solve()
    velocity=[solve(V=v,width=w,n_skis=n) for w,n in[(.1,2),(.25,1)] for v in[.5,1,2,5,10,20]]
    stiffness=[solve(ky=k,kz=k,Ed=e) for k in[1e-12,3e-12,6e-12,1e-11,1e-10,1e-8] for e in[1e4,2e4,5e4,1e5]]
    depth=[solve(H=h,ky=3e-12*r,kz=3e-12) for h in[.01,.02,.03,.05,.1] for r in[.1,1,10]]
    rain=[]
    for rainrate in[100.,200.]:
        for reserve in[1.,2.]:
            for retention in[1.,.5]:
                targetk=(rainrate*reserve/retention)/3.6e6*P['mu_water']/(P['rho_water']*P['g'])
                for anis in[1.,.1]:
                    r=solve(ky=targetk*anis,kz=targetk)
                    rain.append({'rain_mm_h':rainrate,'reserve_factor':reserve,'k_retained_after_clog':retention,
                                 'ky_over_kz':anis,**r,
                                 'drain_after_clog_mm_h':r['clean_saturated_drain_mm_h']*retention})
    fusion=[]
    for rr in [100.,200.]:
        for retain in [1.,.5]:
            kk=rr*2/retain/3.6e6*P['mu_water']/(P['rho_water']*P['g'])
            for ee in [2e4,2.5e4,4e4]:
                r=solve(ky=kk,kz=kk,Ed=ee)
                required=(.04-r['delta_mm']/1000/P['L'])/(1-r['air_load_fraction'])
                fusion.append({'rain_mm_h':rr,'margin':2.,'permeability_retention':retain,**r,'mu_solid_required_for_diagnostic_004':required,'mu_solid_required_with_extra_001':(.03-r['delta_mm']/1000/P['L'])/(1-r['air_load_fraction'])})
    pores=[]
    for kk in [3e-12,5.663155510250312e-12,2.2652622041001248e-11]:
        for tort in [1.,3.,5.]:
            radius=(8*tort*kk/P['phi'])**.5
            pores.append(dict(intrinsic_k_m2=kk,tortuosity_factor=tort,equivalent_tube_radius_um=radius*1e6,complete_wetting_meniscus_Pa=2*.072/radius))
    gaps=[]
    for radius in[20e-6,50e-6,100e-6]:
        kgap=radius**2/8
        for f in[.001,.01,.05,.1]:
            ky=(1-f)*1e-12+f*kgap
            gaps.append({'gap_radius_um':radius*1e6,'ideal_gap_area_fraction':f,'k_gap_m2':kgap,**solve(ky=ky)})
    geom=[{'use':'geometry stress screen; narrow edge cases NOT validated',**solve(width=w,M=m)}
          for w in[.005,.02,.05,.1] for m in[40.,70.,110.]]
    source=[dict(speed_m_s=v,air_fraction=f,air_fraction_error=e,friction=mu,friction_error=er,
                 ratio_not_material_coefficient=mu/(1-f)) for v,f,e,mu,er in
            [(2.5,.580,.004,.44,.02),(3.3,.678,.001,.29,.02),(4.,.727,.003,.19,.02),
             (4.5,.760,.002,.14,.01),(5.,.796,.002,.06,.02)]]
    cost=[dict(whole_bed_kg=108000,additional_mass_fraction=f,added_kg=108000*f,
               hypothetical_resin_JPY_per_kg=c,yield_fraction=.8,
               raw_only_JPY_ex_tax=108000*f*c/.8)
          for f in[.02,.05,.1] for c in[500.,2000.]]
    datasets={'velocity.csv':velocity,'stiffness_permeability.csv':stiffness,
              'depth_anisotropy.csv':depth,'rain_tradeoff.csv':rain,'gap_bypass.csv':gaps,'pore_wetting_screen.csv':pores,
              'geometry_screen.csv':geom,'fusion_requirements.csv':fusion,'source_speed_subset.csv':source,'raw_cost.csv':cost}
    for fn,rows in datasets.items():writecsv(fn,rows)
    checks=[]
    def ck(name,ok,detail): checks.append(dict(name=name,passed=bool(ok),detail=detail))
    p=P
    for factor in[.1,1.,10.]:
        pp={**p,'ky':p['ky']*factor}
        single=steady_gain(pp,512);double=steady_double(pp,256)
        ck('steady_series_'+str(factor),abs(single-double)/single<1e-6,dict(single=single,double=double,relative_error=abs(single-double)/single))
    for num in[32,64,128]:
        gn=air_gain(p,num);gr=air_gain(p,256)
        ck('series_convergence_'+str(num),abs(gn-gr)/gr<.0001,dict(relative_error=abs(gn-gr)/gr))
    ck('force_closure',abs(baseline['pn_Pa']-baseline['delta_mm']/1000*(p['Ed']/(2*p['H'])+baseline['air_gain_Pa_per_m']))<1e-10,'global normal load only')
    ck('positive_fractions',all(0<r['air_load_fraction']<1 for rs in[velocity,stiffness,depth,rain,gaps,geom] for r in rs),'not success fractions')
    ck('speed_lift_monotonic',all(velocity[i]['air_load_fraction']<velocity[i+1]['air_load_fraction'] for i in range(5)),'six fixed-parameter ski speed cases')
    ck('stiffening_reduces_air_share',solve(Ed=1e5)['air_load_fraction']<solve(Ed=1e4)['air_load_fraction'],'fixed permeability; real coupling unmeasured')
    ck('leak_reduces_air_share',solve(ky=1e-10)['air_load_fraction']<solve(ky=1e-12)['air_load_fraction'],'fixed solid stiffness')
    ck('darcy_units',abs(baseline['clean_saturated_drain_mm_h']-105.948)<1e-9,baseline['clean_saturated_drain_mm_h'])
    ck('rain_margin_closure',all(abs(r['drain_after_clog_mm_h']-r['rain_mm_h']*r['reserve_factor'])<1e-9 for r in rain),'saturated gradient 1 only')
    ck('small_z_F',abs(F(1e-9)/(5e-10)-1)<1e-8,'cancellation avoided')
    # Bottom-leak-free limit and side-leak-free limit of steady coefficient.
    sides=steady_gain({**p,'kz':1e-25},512)
    side_exact=p['mu_air']*(p['width']/2)**2/(3*p['ky']*p['H'])
    ck('side_only_steady_limit',abs(sides-side_exact)/side_exact<1e-8,dict(series=sides,analytic=side_exact))
    bottom=steady_double({**p,'ky':1e-25},256)
    bottom_exact=p['mu_air']*p['H']/(2*p['kz'])
    ck('bottom_only_steady_limit',abs(bottom-bottom_exact)/bottom_exact<.001,dict(series=bottom,analytic=bottom_exact))
    veryslow=air_gain({**p,'V':1e-4});ss=steady_gain(p)*1e-4/p['L']
    ck('slow_drain_limit',abs(veryslow-ss)/ss<.001,dict(dynamic=veryslow,steady=ss))
    noleak=air_gain({**p,'ky':1e-25,'kz':1e-25},256);closed=p['p0']/(2*p['phi']*p['H'])
    ck('fast_closed_limit',abs(noleak-closed)/closed<.003,dict(series=noleak,analytic=closed))
    ck('source_speed_conditions_separated',len(source)==5 and source[3]['friction']==.14,'k=3 table; .04 at k=1.5 kept separate')
    ck('source_ratio_not_constant',max(r['ratio_not_material_coefficient'] for r in source)>3*min(r['ratio_not_material_coefficient'] for r in source),'diagnostic only; do not fit constant mu_solid from source')
    ck('cost_mass_arithmetic',all(abs(r['raw_only_JPY_ex_tax']*.8-r['added_kg']*r['hypothetical_resin_JPY_per_kg'])<1e-8 for r in cost),'not quotation')
    ck('finite_outputs',all(isfinite(v) for rs in datasets.values() for r in rs for v in r.values() if isinstance(v,(float,int))),'no NaN')
    ck('fusion_force_friction_closure',all(abs(r['mu_solid_required_for_diagnostic_004']*(1-r['air_load_fraction'])+r['delta_mm']/1000/P['L']-.04)<1e-12 for r in fusion),'not a measured coefficient')
    ck('pore_bundle_inversion',all(abs(P['phi']*(r['equivalent_tube_radius_um']/1e6)**2/(8*r['tortuosity_factor'])/r['intrinsic_k_m2']-1)<1e-12 for r in pores),'ideal geometry only')
    ck('capillary_units',all(abs(r['complete_wetting_meniscus_Pa']*r['equivalent_tube_radius_um']/1e6-.144)<1e-12 for r in pores),'complete wetting assumption, not measured suction')
    gapmax=(3e-12-1e-12)/((50e-6)**2/8-1e-12)
    results={'baseline':baseline,'rain_100_twofold_isotropic':next(r for r in rain if r['rain_mm_h']==100 and r['reserve_factor']==2 and r['k_retained_after_clog']==1 and r['ky_over_kz']==1),
        'rain_100_twofold_anisotropic':next(r for r in rain if r['rain_mm_h']==100 and r['reserve_factor']==2 and r['k_retained_after_clog']==1 and r['ky_over_kz']==.1),
        'gap_fraction_max_50um_ideal':gapmax,'source_ratio_range':[min(r['ratio_not_material_coefficient'] for r in source),max(r['ratio_not_material_coefficient'] for r in source)],
        'row_counts':{k:len(v) for k,v in datasets.items()},'total_rows':sum(map(len,datasets.values())),
        'physical_experiments':0,'probability_of_success':None,'interpretation':'mathematical screening; no experimental validation of proposed material'}
    writej('results.json',results);writej('checks.json',{'checks':checks,'passed':sum(x['passed'] for x in checks),'total':len(checks),'physical_validation':False})
    assert all(x['passed'] for x in checks),[x for x in checks if not x['passed']]
    print(json.dumps({'checks':len(checks),'rows':results['total_rows'],'baseline':baseline,'rain_isotropic':results['rain_100_twofold_isotropic'],'rain_anisotropic':results['rain_100_twofold_anisotropic'],'gap_fraction_max':gapmax},ensure_ascii=False))
if __name__=='__main__':main()
