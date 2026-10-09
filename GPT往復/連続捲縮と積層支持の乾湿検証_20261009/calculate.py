"""Cycle 70: uncalibrated one-mode curved-ribbon model and process balances."""
from pathlib import Path
import math,json,csv
D=Path(__file__).resolve().parent
pi=math.pi
a=100e-6; cell=500e-6; height=577.350269e-6
x1=48.15e-6;x2=.15*height; p1=5000.;p2=100000.
E=1e9; width=400e-6; density=1300.
def J(n,x):
    t=(x/2)**n;s=t
    for k in range(1,45):
        t*=-(x*x/4)/(k*(k+n));s+=t
    return s
def amplitude(z):
    lo=0.;hi=2.3
    for _ in range(70):
        mid=(lo+hi)/2
        if J(0,mid)>z:lo=mid
        else:hi=mid
    return (lo+hi)/2
def golden(f,lo,hi):
    g=(5**.5-1)/2;c=hi-g*(hi-lo);d=lo+g*(hi-lo);fc=f(c);fd=f(d)
    for _ in range(90):
        if fc<fd:hi,d,fd=d,c,fc;c=hi-g*(hi-lo);fc=f(c)
        else:lo,c,fc=c,d,fd;d=lo+g*(hi-lo);fd=f(d)
    return (lo+hi)/2
def factor(L,x):
    ell=math.hypot(a,x);A0=amplitude(a/L);A=amplitude(ell/L)
    return 4*pi*pi*(A0-A)*x/(L*L*J(1,A)*ell)
lo=math.hypot(a,x2)*(1+1e-9);hi=300e-6
for _ in range(85):
    mid=(lo+hi)/2
    if factor(mid,x2)/factor(mid,x1)>p2/p1:lo=mid
    else:hi=mid
L=(lo+hi)/2;EI=p2*cell*cell/factor(L,x2);A0=amplitude(a/L)
t=(12*EI/(E*width))**(1/3)
def finite(x,n=1):
    ell=math.hypot(a,x);tn=t/n**(1/3);EA=E*width*tn*n
    def energy(A):
        eps=ell/(L*J(0,A))-1
        return EI*pi*pi/L*(A-A0)**2+.5*EA*L*eps*eps
    A=golden(energy,amplitude(min(ell/L,1)),A0)
    eps=ell/(L*J(0,A))-1;T=EA*eps/J(0,A)
    return dict(x_um=x*1e6,layers=n,amplitude_rad=A,axial_strain=eps,
      pressure_kPa=2*T*x/ell/(cell*cell)/1000,energy_two_halves_J=2*energy(A),
      bending_strain_estimate=tn*pi*abs(A-A0)/L,
      tensile_surface_strain_estimate=eps+tn*pi*abs(A-A0)/L)
curves=[]
for n in [1,8,64]:
    for k in range(51):curves.append(finite(x2*k/50,n))
N=2000*.45*.5/(cell*cell*height); hours=100*16;seconds=hours*3600
layers=[]
for n in [1,8,64]:
    tn=t/n**(1/3);mass=2*L*width*tn*n*N*density
    layers.append(dict(layers=n,thickness_each_um=tn*1e6,axial_EA_N=E*width*tn*n,
      material_kg=mass,material_multiplier=n**(2/3),fully_coupled_to_free_EI_ratio=n*n,
      low_pressure_kPa=finite(x1,n)['pressure_kPa'],**{('high_'+k):v for k,v in finite(x2,n).items() if k not in ['layers','x_um']}))
tau=1-323.15/647.096;gamma=.2358*tau**1.256*(1-.625*tau)
wet=[]
for n in [1,8,64]:
    tn=t/n**(1/3)
    for gap in [2e-6,5e-6,20e-6]:
        for angle in [0,60,90]:
            pressure=2*gamma*max(math.cos(angle*pi/180),0)/gap
            delta=5*pressure*L**4/(32*E*tn**3)
            wet.append(dict(layers=n,gap_um=gap*1e6,contact_angle_deg_assumed=angle,
              ideal_meniscus_pressure_kPa=pressure/1000,flat_pinned_beam_diagnostic_deflection_um=delta*1e6,
              deflection_over_gap=delta/gap,not_actual_curved_layer_solution=True))
factory=[]
for n in [1,8,64]:
    for yield_ in [.5,.8,1]:
        area=N*cell*cell*n/yield_
        factory.append(dict(layers=n,layout_yield_assumed=yield_,web_area_m2=area,
          one_meter_web_speed_m_min=area/hours/60,
          two_half_components_per_second=2*n*N/seconds,
          assembled_grains_per_second=N/seconds,
          area_cost_JPY_at_10JPY_m2_assumed=10*area))
source_speed=4200;source_dtex=110;source_throughput=source_speed*60*source_dtex*1e-7
checks=[]
def ck(name,v):
    checks.append(dict(name=name,passed=bool(v)));assert v,name
for z in [0,.4,1.046]:
    numerical=sum(math.cos(z*math.cos((k+.5)*2*pi/20000)) for k in range(20000))/20000
    ck('Bessel J0 vs geometric integral '+str(z),abs(numerical-J(0,z))<1e-10)
ck('initial chord closure',abs(L*J(0,A0)-a)<1e-12)
ck('inverse low point only',abs(EI*factor(L,x1)/cell**2/p1-1)<1e-10)
ck('inverse high point only',abs(EI*factor(L,x2)/cell**2/p2-1)<1e-10)
ck('not measured 100kPa after axial compliance',finite(x2)['pressure_kPa']<80)
for n in [1,8,64]:
    tn=t/n**(1/3)
    ck('free layers preserve total EI '+str(n),abs(n*E*width*tn**3/12/EI-1)<1e-12)
    ck('minimum energy not above inextensible trial '+str(n),finite(x2,n)['energy_two_halves_J']<=2*EI*pi*pi/L*(amplitude(math.hypot(a,x2)/L)-A0)**2*(1+1e-9))
    h=1e-9
    dU=(finite(x1+h,n)['energy_two_halves_J']-finite(x1-h,n)['energy_two_halves_J'])/(2*h)
    ck('energy derivative equals transverse force '+str(n),abs(dU/(finite(x1,n)['pressure_kPa']*1000*cell**2)-1)<2e-5)
ck('water surface tension positive',.067<gamma<.069)
ck('linked eight layer rigidity factor is 64',layers[1]['fully_coupled_to_free_EI_ratio']==64)
ck('64 layers sixteen times material',abs(layers[2]['material_multiplier']-16)<1e-12)
ck('2000 m2 bed grain volume accounting',abs(N*cell*cell*height-450)<1e-8)
ck('source yarn throughput arithmetic',abs(source_throughput-2.772)<1e-12)
ck('factory area equals width speed time',all(abs(z['one_meter_web_speed_m_min']*60*hours-z['web_area_m2'])<1e-6 for z in factory))
ck('all curve fields finite',all(math.isfinite(v) for row in curves for v in row.values()))
outputs={'support_curves':curves,'layers':layers,'wet_layers':wet,'factory':factory}
for name,rows in outputs.items():
    with (D/(name+'.csv')).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
result=dict(cycle=70,physical_tests=0,success_probability=None,
  status='UNCALIBRATED_ONE_MODE_MODEL_AND_MANUFACTURING_BALANCE',
  assumed_E_Pa=E,assumed_density_kg_m3=density,material_selected=False,
  inverse_inextensible=dict(contour_half_length_um=L*1e6,initial_amplitude_rad=A0,EI_N_m2=EI,width_um=width*1e6,thickness_um=t*1e6),
  layer_results=layers,pure_water_surface_tension_50C_N_m=gamma,
  manufacturing=dict(grain_count=N,days=100,hours_per_day=16,source_yarn_dtex=source_dtex,source_winding_m_min=source_speed,source_yarn_kg_h=source_throughput,source_throughput_is_particle_output=False),
  rows={n:len(v) for n,v in outputs.items()})
for name,value in [('results',result),('checks',dict(count=len(checks),all_passed=all(c['passed'] for c in checks),checks=checks))]:
    (D/(name+'.json')).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(dict(checks=len(checks),rows=sum(len(v) for v in outputs.values()),physical_tests=0,success_probability=None)))
