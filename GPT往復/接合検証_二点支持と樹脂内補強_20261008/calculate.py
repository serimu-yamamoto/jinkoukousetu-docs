"""Cycle 20. Local linear supports only: no measured material, ski, or probability model."""
import json, math, itertools
from pathlib import Path
PTH=Path(__file__).resolve().parent
P=json.loads((PTH/'inputs.json').read_text(encoding='utf-8'))
b,j,g=P['branch'],P['joints'],P['grain']
def zeros(n,m=None): return [[0.0]*(n if m is None else m) for _ in range(n)]
def mv(a,x): return [sum(v*y for v,y in zip(row,x)) for row in a]
def solve(a,b):
    n=len(b); a=[list(row)+[float(v)] for row,v in zip(a,b)]
    for c in range(n):
        k=max(range(c,n),key=lambda k:abs(a[k][c]))
        if abs(a[k][c])<1e-300: raise ValueError('singular')
        a[c],a[k]=a[k],a[c]
        v=a[c][c]; a[c]=[x/v for x in a[c]]
        for k in range(n):
            if k!=c:
                v=a[k][c]; a[k]=[x-v*y for x,y in zip(a[k],a[c])]
    return [row[-1] for row in a]
def beam(EI,L,shear_rigidity=math.inf):
    # Scaled slope coordinates u=[v, L*theta, v, L*theta] improve conditioning.
    phi=0 if math.isinf(shear_rigidity) else 12*EI/(shear_rigidity*L*L)
    c=EI/((1+phi)*L**3)
    return [[c*x for x in row] for row in [[12,6,-12,6],[6,4+phi,-6,2-phi],[-12,-6,12,-6],[6,2-phi,-6,4+phi]]]
def crossbar(s,EI,kv,kr,shear_rigidity=math.inf):
    # Nodes x=-s,0,+s. Internal outer frame is a rigid reference, not fixed to ground in a grain model.
    K=zeros(6); ke=beam(EI,s,shear_rigidity)
    for ids in ([0,1,2,3],[2,3,4,5]):
        for x,ix in enumerate(ids):
            for y,iy in enumerate(ids): K[ix][iy]+=ke[x][y]
    for v,rot in [(0,1),(4,5)]: K[v][v]+=kv; K[rot][rot]+=kr/s**2
    free=[0,1,4,5]; fixed=[2,3]
    solutions=[]
    for prescribed in ([1,0],[0,1]):
        rhs=[-sum(K[i][k]*u for k,u in zip(fixed,prescribed)) for i in free]
        uf=solve([[K[i][k] for k in free] for i in free],rhs)
        u=[0.0]*6
        for i,x in zip(fixed,prescribed):u[i]=x
        for i,x in zip(free,uf):u[i]=x
        solutions.append(u)
    reactions=[mv(K,u) for u in solutions]
    kz=reactions[0][2]; kth=reactions[1][3]*s*s
    cross=reactions[1][2]*s
    return dict(kz=kz,kth=kth,cross=cross,K=K,ke=ke,unit_v=solutions[0],unit_scaled_rotation=solutions[1],free=free)
L=b['span_um']*1e-6; d=b['diameter_um']*1e-6; Eb=b['modulus_MPa']*1e6
Ib=math.pi*d**4/64; F=b['force_multiplier']*math.pi*b['force_gamma_N_m']*d
delta_fixed=F*L**3/(192*Eb*Ib)
m0=math.pi/6*(g['equivalent_diameter_um']*1e-6)**3*g['apparent_density_kg_m3']
op,bu=P['operation'],P['budget']
M0=op['area_m2']*op['depth_m']*op['bulk_density_kg_m3']; r=bu['discount'];n=bu['years']
crf=r*(1+r)**n/((1+r)**n-1)
base=(M0*bu['material_JPY_kg']+bu['nonmaterial_capital_JPY'])*crf+bu['annual_fixed_JPY']+M0*bu['material_JPY_kg']*bu['annual_material_replacement_fraction']
rows=[];excluded=[];checks=[]
def check(label,valid):
    if not valid: raise AssertionError(label)
    checks.append(label)
def near(x,y,rtol=2e-8,atol=1e-12): return abs(x-y)<=atol+rtol*max(abs(x),abs(y))
for emp,aum,hum,sum_ in itertools.product(j['wet_moduli_MPa'],j['equal_area_disk_radii_um'],j['layer_thicknesses_um'],j['half_separations_um']):
    a=aum*1e-6;h=hum*1e-6;s=sum_*1e-6;E=emp*1e6;A=math.pi*a*a
    for tum in ([0] if s==0 else j['carrier_thicknesses_um']):
        t=tum*1e-6;rp=a if s==0 else a/math.sqrt(2)
        key=f'E{emp}_a{aum}_h{hum}_s{sum_}_t{tum}'
        if 0<s<rp:
            excluded.append(dict(id=key,reason='two pad disks overlap'));continue
        Vpad=A*h;Vframe=0
        if s==0:
            J=math.pi*a**4/4;kz=E*A/h;kth=E*J/h;kth_rigid=kth;cb=None
        else:
            kv=E*(A/2)/h;kr=E*(math.pi*rp**4/4)/h
            EI=j['carrier_modulus_MPa']*1e6*j['carrier_width_um']*1e-6*t**3/12
            Gframe=j['carrier_modulus_MPa']*1e6/(2*(1+j['carrier_poisson_ratio']))
            shear_rigidity=j['shear_correction_factor']*Gframe*j['carrier_width_um']*1e-6*t
            cb=crossbar(s,EI,kv,kr,shear_rigidity)
            kz,kth=cb['kz'],cb['kth']
            J=A*s*s+math.pi*a**4/8;kth_rigid=E*J/h
            Vframe=2*s*j['carrier_width_um']*1e-6*t
            check(key+'_reflection_decouples',abs(cb['cross'])<1e-7*math.sqrt(kz*kth))
            for u in [cb['unit_v'],cb['unit_scaled_rotation']]:
                rr=mv(cb['K'],u);scale=max(map(abs,rr))
                check(key+'_outer_equilibrium_'+str(len(checks)),max(abs(rr[i]) for i in cb['free'])<max(scale*2e-9,1e-15))
        alpha=kth*L/(2*Eb*Ib)
        end_moment=F*L/8*alpha/(alpha+1)
        v=F/(2*kz);theta=end_moment/kth
        delta_bend=delta_fixed*(alpha+4)/(alpha+1)
        delta_total=delta_bend+v
        if cb is None:
            pad_strain=(abs(v)+a*abs(theta))/h; maxrot=abs(theta)
        else:
            u=[v*x+s*theta*y for x,y in zip(cb['unit_v'],cb['unit_scaled_rotation'])]
            pad_strain=max((abs(u[iv])+rp*abs(u[it]/s))/h for iv,it in [(0,1),(4,5)])
            maxrot=max(abs(u[it]/s) for it in [1,3,5])
        mpad=Vpad*j['pad_density_kg_m3'];mframe=Vframe*j['carrier_density_kg_m3']
        row=dict(carrier_slenderness=None if s==0 else s/t,carrier_slenderness_screen=(s==0 or s/t>=P['criteria']['slenderness_diagnostic_min']),id=key,pad_E_MPa=emp,a_um=aum,h_um=hum,half_separation_um=sum_,carrier_t_um=tum,pad_radius_um=rp*1e6,pad_volume_um3=Vpad*1e18,carrier_volume_um3=Vframe*1e18,kz_N_m=kz,kth_Nm_rad=kth,rigid_carrier_kth_Nm_rad=kth_rigid,alpha=alpha,branch_bending_to_fixed_ratio=delta_bend/delta_fixed,total_deflection_to_fixed_ratio=delta_total/delta_fixed,total_deflection_um=delta_total*1e6,end_moment_Nm=end_moment,peak_pad_normal_stress_MPa=pad_strain*E/1e6,max_pad_normal_strain=pad_strain,max_rotation_rad=maxrot,pad_mass_kg=mpad,carrier_mass_kg=mframe,geometric_linear_diagnostic=(pad_strain<=P['criteria']['normal_strain_diagnostic_limit'] and maxrot<=P['criteria']['rotation_diagnostic_limit_rad'] and delta_total/L<=.1),support_units_max_if_all_added_mass_1percent=g['total_added_fraction_cap']*m0/((1-g['total_added_fraction_cap'])*(mpad+mframe)),cost_cases=[])
        for N in g['support_units']:
            q=N*(mpad+mframe)/m0
            extra=M0*q
            delta_annual=extra*P['cost']['initial_and_replacement_unit_JPY_kg']*(crf+bu['annual_material_replacement_fraction'])
            remaining=bu['annual_budget_JPY']-base-delta_annual
            row['cost_cases'].append(dict(units=N,added_mass_relative_to_parent=q,added_support_fraction_of_final=q/(1+q),pad_fraction_of_final=N*mpad/(m0*(1+q)),resulting_bed_density_kg_m3=op['bulk_density_kg_m3']*(1+q),extra_bed_mass_kg=extra,incremental_material_annual_JPY=delta_annual,remaining_annual_budget_JPY=remaining,all_in_reform_fee_JPY_kg_at_1percent=remaining/((M0+extra)*.01*op['closures_per_year'])))
        rows.append(row)
# Independent local checks: force-only pins, nearly rigid arms, energy and closed-form pad integration.
for s in [5e-6,10e-6,20e-6]:
    kv=10.;EI=1e-13
    cb=crossbar(s,EI,kv,0.)
    closed_kz=2/(1/kv+s**3/(3*EI))
    check('pin_tip_translation_'+str(s),near(cb['kz'],closed_kz))
    check('pin_tip_rotation_'+str(s),near(cb['kth'],closed_kz*s*s,atol=1e-20))
    for u in [cb['unit_v'],cb['unit_scaled_rotation']]:
        energy=sum(x*y for x,y in zip(u,mv(cb['K'],u)))/2
        internal=0.
        for ids in ([0,1,2,3],[2,3,4,5]):
            ue=[u[k] for k in ids];internal+=sum(x*y for x,y in zip(ue,mv(cb['ke'],ue)))/2
        internal+=kv*(u[0]**2+u[4]**2)/2
        check('energy_partition_'+str(s)+'_'+str(len(checks)),near(energy,internal))
a=5e-6;h=1e-6;s=10e-6;E=3e6;rp=a/math.sqrt(2);kv=E*math.pi*rp**2/h;kr=E*math.pi*rp**4/(4*h)
cb=crossbar(s,1e-6,kv,kr)
rigid=E/h*(math.pi*a*a*s*s+math.pi*a**4/8)
check('rigid_carrier_limit_translation',near(cb['kz'],2*kv,rtol=1e-5))
check('rigid_carrier_limit_rotation',near(cb['kth'],rigid,rtol=1e-5,atol=1e-20))
for shear_s in [5e-6,10e-6,20e-6]:
    EI=1e-13;kv=10.;Q=.005
    cb=crossbar(shear_s,EI,kv,0.,Q)
    closed=2/(1/kv+shear_s**3/(3*EI)+shear_s/Q)
    check('timoshenko_pin_translation_'+str(shear_s),near(cb['kz'],closed))
    check('timoshenko_pin_rotation_'+str(shear_s),near(cb['kth'],closed*shear_s**2,atol=1e-20))
# Polar midpoint quadrature of two pad moments about center; independent of parallel-axis expression.
nr,nt=200,360;integral=0.
for cx in [-s,s]:
    for i in range(nr):
        radius=rp*(i+.5)/nr
        for k in range(nt):
            x=cx+radius*math.cos(2*math.pi*(k+.5)/nt)
            integral+=x*x*radius*(rp/nr)*(2*math.pi/nt)
check('two_disks_polar_integration',near(integral,math.pi*a*a*s*s+math.pi*a**4/8,rtol=2e-6,atol=1e-30))
check('force_scale_not_test',P['evidence']['physical_tests']==0 and P['evidence']['physical_success_probability'] is None)
source_arithmetic=dict(PHB2019_text_before_MPa=31.2,PHB2019_text_after_MPa=27.1,PHB2019_text_claim_drop_percent=3.5,drop_percent_from_printed_values=(31.2-27.1)/31.2*100,note='Text arithmetic inconsistency only; original figure/data not corrected or inferred')
result=dict(source_arithmetic=source_arithmetic,evidence=P['evidence'],counts=dict(local_cases=len(rows),excluded_overlap=len(excluded),mass_cost_cases=sum(len(x['cost_cases']) for x in rows)),branch_force_N=F,branch_I_m4=Ib,fixed_branch_deflection_um=delta_fixed*1e6,parent_grain_mass_kg=m0,baseline_annual_JPY=base,crf=crf,rows=rows,excluded=excluded)
(PTH/'results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
(PTH/'validation.json').write_text(json.dumps(dict(check_count=len(checks),all_passed=True,checks=checks,scope='Local numerical consistency only; no physical calibration'),indent=2)+'\n',encoding='utf-8')
sel=[x for x in rows if x['pad_E_MPa'] in [.3,3] and x['a_um']==5 and x['h_um']==1 and x['half_separation_um'] in [0,10,20] and x['carrier_t_um'] in [0,2,5]]
print(json.dumps(dict(counts=result['counts'],check_count=len(checks),selected=sel),indent=2))
