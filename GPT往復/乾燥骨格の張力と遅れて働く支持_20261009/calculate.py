"""Cycle 69: support/formation separation. Standard-library calculations.
No physical tests, no inferred success probability. Run beside the output files.
"""
from pathlib import Path
import math,json,csv
D=Path(__file__).resolve().parent
Acell=(500e-6)**2;H=577.350269e-6;a=100e-6
x1=48.15e-6;x2=0.15*H;p1=5000.;p2=100000.
E=1.35e6 # published film modulus at unspecified test temperature; proxy, NOT measured 50 C
rho=1200. # assumed solid density
l1=math.hypot(a,x1);l2=math.hypot(a,x2)
k=(p2/p1)*(x1/x2)
l0=(k-1)/(k/l1-1/l2)
EA=p2*Acell/(2*x2*(1/l0-1/l2))
Aband=EA/E

def force(x,rest=l0,ea=EA):
    l=math.hypot(a,x)
    return 2*ea*x*max(0,1/rest-1/l)
def energy(x,rest=l0,ea=EA):
    l=math.hypot(a,x)
    return ea/rest*max(0,l-rest)**2

def jsonout(n,o):
    (D/n).write_text(json.dumps(o,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
def table(n,rows):
    with (D/n).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)

# Compare shape of force curve, separately sized to the same 100kPa endpoint.
configs=[('slack_inverse_spec',l0),('just_taut',a),('pretension_1_5_assumed',a/1.5)]
curve=[];sizing=[]
for label,rest in configs:
    ea=p2*Acell/(2*x2*(1/rest-1/l2))
    sizing.append({'configuration':label,'rest_half_length_um':rest*1e6,'area_each_half_um2_at_Eproxy':ea/E*1e12,
                   'pressure_at_48_15um_kPa':force(x1,rest,ea)/Acell/1000,
                   'pressure_at_86_60um_kPa':force(x2,rest,ea)/Acell/1000,
                   'force_ratio':force(x2,rest,ea)/force(x1,rest,ea),
                   'max_band_strain':max(0,l2/rest-1)})
    for n in range(101):
        x=x2*n/100
        curve.append({'configuration':label,'displacement_um':x*1e6,'pressure_kPa':force(x,rest,ea)/Acell/1000,
                      'elastic_energy_nJ':energy(x,rest,ea)*1e9})
# No distribution/probability assigned to dimensional and modulus factors.
tol=[]
for restfactor in (.98,.99,1.,1.01,1.02):
    for efactor in (.2,.5,1.):
        rest=l0*restfactor
        tol.append({'rest_length_ratio_assumed':restfactor,'modulus_ratio_assumed':efactor,
                    'slack_ends_at_um':math.sqrt(max(0,rest*rest-a*a))*1e6,
                    'p48_kPa':force(x1,rest,EA*efactor)/Acell/1000,
                    'p86_kPa':force(x2,rest,EA*efactor)/Acell/1000})
Vcell=Acell*H;bedvolume=2000*.45;phi=.5;N=bedvolume*phi/Vcell
mem=[]
for ep in (1.35,5,20):
    area=EA/(ep*1e6)
    vol=2*area*l0
    mem.append({'E_MPa_assumed_or_proxy':ep,'area_each_half_um2':area*1e12,
                'thickness_um_if_width_500um':area/(500e-6)*1e6,
                'total_band_volume_fraction_of_cell':vol/Vcell,
                'band_mass_kg_for_reference_bed':vol*N*rho})
# Planar precursor area budget, not a specific print machine throughput.
manufacturing=[]
for footprintfactor in (1.,2.,4.):
    for layoutyield in (.5,.8,1.):
        area=N*Acell*footprintfactor/layoutyield
        manufacturing.append({'flat_area_per_grain_footprint_ratio_assumed':footprintfactor,
                              'layout_yield_assumed':layoutyield,'patterned_area_m2':area,
                              'needed_area_m2_h_for_100days_16h':area/1600,
                              'area_in_12h_soak_m2_at_that_rate':area/1600*12,
                              'area_cost_JPY_at_10JPY_m2_assumed':area*10,
                              'area_cost_JPY_at_100JPY_m2_assumed':area*100})
resolution=[]
for pitch in (51,17,10,5):
    for feature in (20,50,100):
        resolution.append({'pixel_pitch_um':pitch,'feature_um_assumed':feature,'pixels_across':feature/pitch,
                           'meets_3pixel_layout_rule_not_resolution_proof':feature/pitch>=3})
kinematics=[]
for stretch in (1.5,3,10,20):
    kinematics.append({'stretch':stretch,'unstretched_length_um_for_final_200um':200/stretch,
                       'width_ratio_if_incompressible_uniaxial':stretch**(-.5),
                       'area_ratio_if_incompressible_uniaxial':1/stretch})
# General necessary relaxation condition: fixed length cannot maintain force if material relaxes.
# No time constant is claimed for any candidate.
relax=[{'relative_modulus_or_relaxation_assumed':r,'force_retention_fixed_geometry':r} for r in (1,.8,.5,.2)]
results={'cycle':69,'physical_tests':0,'success_probability':None,'status':'UNCALIBRATED_GEOMETRIC_COUNTEREXAMPLES_AND_INVERSE_SPECIFICATION',
 'source_moduli_not_50C_data':True,
 'basis':{'cell_width_um':500,'cell_height_um':H*1e6,'half_span_um':a*1e6,'x1_um':x1*1e6,'x2_um':x2*1e6,
          'p1_kPa':5,'p2_kPa':100,'Eproxy_MPa':1.35,'solid_density_kg_m3_assumed':rho,
          'bed_m2':2000,'bed_depth_m':.45,'envelope_packing_fraction_assumed':phi},
 'inverse_spec':{'rest_half_length_um':l0*1e6,'engagement_displacement_um':math.sqrt(l0*l0-a*a)*1e6,
                  'EA_N':EA,'area_each_half_um2':Aband*1e12,'strain_at_upper_displacement':l2/l0-1,
                  'geometric_limit_prestress_only_ratio_cubic':(x2/x1)**3,
                  'is_measured_response':False},
 'sizing_comparison':sizing,'band_material_budget':mem,
 'factory_basis':{'grain_count':N,'case_factor2_yield80':manufacturing[4]},
 'source_thermal_ratio_audit':{'printed_endpoints_ratio_2_1_over_0_15':2.1/.15,
                              'reported_strain_tuning_ratio':11.5,
                              'same_normalization_confirmed':False},
 'rows':{'support_curve':len(curve),'sizing':len(sizing),'tolerance':len(tol),'membrane':len(mem),
         'manufacturing':len(manufacturing),'resolution':len(resolution),'stretch':len(kinematics),'relaxation':len(relax)}}
checks=[]
def ck(n,v):
    checks.append({'name':n,'passed':bool(v)});assert v,n
def close(x,y):return math.isclose(x,y,rel_tol=1e-8,abs_tol=1e-10)
ck('rest length lies beyond unloaded chord',a<l0<l1)
ck('5kPa inverse endpoint only',close(force(x1)/Acell,p1))
ck('100kPa inverse endpoint only',close(force(x2)/Acell,p2))
ck('slack has zero force',force(math.sqrt(l0*l0-a*a)*.9)==0)
for frac in (.6,.8,1.):
    x=x2*frac;h=1e-10
    derivative=(energy(x+h)-energy(x-h))/(2*h)
    ck('energy derivative equals force '+str(frac),close(derivative,force(x)))
ck('taut response ratio below cubic bound',sizing[1]['force_ratio']<(x2/x1)**3)
ck('positive pretension cannot reproduce required ratio',sizing[2]['force_ratio']<20)
ck('same endpoint hides wrong low pressure response',sizing[1]['pressure_at_48_15um_kPa']>5 and sizing[2]['pressure_at_48_15um_kPa']>5)
ck('dimensional drift can suppress initial engagement',force(x1,l0*1.02)==0)
ck('modulus loss persists under fixed geometry',close(force(x2,l0,EA*.2)/force(x2),.2))
ck('fitted area inversely proportional to modulus',close(mem[0]['area_each_half_um2']/mem[2]['area_each_half_um2'],20/1.35))
ck('material volume sums both half bands',close(mem[0]['total_band_volume_fraction_of_cell'],2*Aband*l0/Vcell))
ck('grain count times cell envelope equals packed volume',close(N*Vcell,bedvolume*phi))
ck('area formula independent check by height',close(manufacturing[4]['patterned_area_m2'],bedvolume*phi/H*2/.8))
ck('doubling processing area doubles cost',close(manufacturing[4]['area_cost_JPY_at_10JPY_m2_assumed'],2*manufacturing[1]['area_cost_JPY_at_10JPY_m2_assumed']))
ck('51um pixel cannot encode 50um with 3 pixels',resolution[1]['meets_3pixel_layout_rule_not_resolution_proof'] is False)
ck('incompressible stretch preserves volume',all(close(r['stretch']*r['area_ratio_if_incompressible_uniaxial'],1) for r in kinematics))
ck('thermal endpoint arithmetic not forced to headline',not close(2.1/.15,11.5))
ck('no physical success claim',results['physical_tests']==0 and results['success_probability'] is None)
for stem,rows in [('support_curve',curve),('sizing',sizing),('tolerance',tol),('membrane',mem),('manufacturing',manufacturing),('resolution',resolution),('stretch',kinematics),('relaxation',relax)]:table(stem+'.csv',rows)
jsonout('results.json',results);jsonout('checks.json',{'count':len(checks),'all_passed':all(x['passed'] for x in checks),'checks':checks})
print(json.dumps({'checks':len(checks),'rows':sum(results['rows'].values()),'l0_um':l0*1e6,'onset_um':math.sqrt(l0*l0-a*a)*1e6,'physical_tests':0,'success_probability':None}))
