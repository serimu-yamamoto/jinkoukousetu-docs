"""Cycle 43: hypothetical sizing and conservation checks; no physical validation."""
from pathlib import Path
import csv, json, math, sys
D=Path(__file__).resolve().parent
repo=D.parents[1]
if (repo/'.deps').exists(): sys.path.insert(0,str(repo/'.deps'))
p=json.loads((D/'inputs.json').read_text(encoding='utf-8'))
g,e,r,s,c,k=[p[n] for n in ['geometry','erosion','rain','settling','chemistry','economics']]
A=g['slope_area_m2']; Ah=A*math.cos(math.radians(g['slope_deg']))
M=A*g['bed_depth_m']*g['bulk_density_kg_m3']
def dump(name,obj):
    with (D/name).open('w',encoding='utf-8',newline='\n') as f: json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
def table(name,rows):
    with (D/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
checks=[]
def ck(name,ok,detail=''):
    checks.append({'name':name,'passed':bool(ok),'detail':detail})
    if not ok: raise AssertionError(name)
def close(a,b): return math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-10)
eros=[]
for rad in e['branch_radii_um']:
    u=rad*(1-e['stiffness_retention']**0.25)/e['equivalent_wet_days']
    for d in e['debris_diameters_um']:
        loss=(1-(1-e['target_mass_removal'])**(1/3))*d/2
        eros.append({'branch_radius_um':rad,'debris_diameter_um':d,'branch_allowed_recession_um_day':u,'debris_90pct_mass_loss_days_same_rate':loss/u,'required_offsite_to_use_rate_ratio':loss/e['diagnostic_debris_days']/u})
representative=next(x for x in eros if x['branch_radius_um']==30 and x['debris_diameter_um']==10)
ck('erosion branch stiffness equation',all(close((1-x['branch_allowed_recession_um_day']*100/x['branch_radius_um'])**4,0.9) for x in eros))
ck('erosion sphere remaining volume',all(close((1-x['branch_allowed_recession_um_day']*x['debris_90pct_mass_loss_days_same_rate']/(x['debris_diameter_um']/2))**3,0.1) for x in eros))
ck('erosion radius scaling',close(eros[8]['branch_allowed_recession_um_day']/eros[4]['branch_allowed_recession_um_day'],2))
# Rectangular rain, all particles uniformly carried with water; dissolved species excluded.
rain=[]
for intensity in r['vertical_rain_mm_h']:
    q=Ah*intensity/1000*r['runoff_coefficient']; V=q*r['duration_h']; qt=min(q,r['treatment_m3_h'])
    for f in r['damage_fraction_per_operating_day']:
        for mob in r['mobilized_fractions']:
            mass=M*f*r['accumulation_operating_days']*mob
            for eta in r['particle_mass_capture']:
                cap=mass*qt/q*eta; escaped=mass-cap; S=max(0,q-r['treatment_m3_h'])*r['duration_h']
                rain.append({'rain_mm_h':intensity,'damage_fraction_per_day':f,'mobilized_fraction':mob,'filter_particle_mass_capture':eta,'rain_m3_h':q,'rain_volume_m3':V,'input_particle_kg':mass,'input_mg_L':1000*mass/V,'captured_no_storage_kg':cap,'outflow_no_storage_kg':escaped,'outflow_no_storage_mg_L':1000*escaped/V,'system_capture_no_storage':cap/mass,'minimum_ideal_storage_m3':S,'drawdown_after_rain_h':S/r['treatment_m3_h'],'outflow_with_adequate_storage_kg':mass*(1-eta),'outflow_with_adequate_storage_mg_L':1000*mass*(1-eta)/V})
ck('slope projection',close(Ah,1000*math.sqrt(3)))
ck('bed mass',close(M,108000))
ck('rain mass conservation no storage',all(close(x['captured_no_storage_kg']+x['outflow_no_storage_kg'],x['input_particle_kg']) for x in rain))
ck('whole system capture bounded by filter',all(0<=x['system_capture_no_storage']<=x['filter_particle_mass_capture']+1e-12 for x in rain))
ck('low rain capacity no bypass',all(close(x['system_capture_no_storage'],x['filter_particle_mass_capture']) for x in rain if x['rain_mm_h']==30))
ck('storage water balance',all(close(min(x['rain_m3_h'],100)*r['duration_h']+x['minimum_ideal_storage_m3'],x['rain_volume_m3']) for x in rain))
ck('with storage retains filter limit',all(close(x['outflow_with_adequate_storage_kg'],x['input_particle_kg']*(1-x['filter_particle_mass_capture'])) for x in rain))
# Independent time-marching reservoir with no discharge overflow and sufficient storage.
def march(q,dt):
    stock=peak=treated=0.0
    n=round(1/dt)
    for _ in range(n):
        stock+=q*dt; out=min(stock,100*dt); stock-=out;treated+=out;peak=max(peak,stock)
    return peak,stock,treated
for intensity in r['vertical_rain_mm_h']:
    q=Ah*intensity/1000
    a=march(q,0.001); b=march(q,0.0005)
    ck('reservoir independent march '+str(intensity),all(close(v,max(0,q-100)) for v in [a[0],b[0]]) and close(a[1]+a[2],q) and close(b[1]+b[2],q))
sett=[]
for d in s['diameters_um']:
    dm=d*1e-6; v=(s['solid_density_kg_m3']-s['water_density_kg_m3'])*9.81*dm*dm/(18*s['dynamic_viscosity_Pa_s'])
    sett.append({'diameter_um':d,'stokes_settling_m_h':v*3600,'Re':s['water_density_kg_m3']*v*dm/s['dynamic_viscosity_Pa_s'],'ideal_surface_area_for_100mmh_rain_m2':Ah*0.1/(v*3600)})
ck('settling diameter squared',close(sett[1]['stokes_settling_m_h']/sett[0]['stokes_settling_m_h'],100))
ck('settling low Reynolds ideal spheres',all(x['Re']<0.1 for x in sett))
base=next(x for x in rain if x['rain_mm_h']==100 and x['damage_fraction_per_day']==1e-5 and x['mobilized_fraction']==1 and x['filter_particle_mass_capture']==0.999)
oxygen={'PHB_ThOD_kg_O2_kg':c['PHB_O2_g_mol']/c['PHB_repeat_g_mol'],'cellulose_ThOD_kg_O2_kg':c['cellulose_O2_g_mol']/c['cellulose_repeat_g_mol'],'example_PHB_mass_kg':base['input_particle_kg'],'example_rain_DO_kg':base['rain_volume_m3']*c['illustrative_DO_mg_L']/1000}
oxygen['example_PHB_ThOD_kg']=oxygen['example_PHB_mass_kg']*oxygen['PHB_ThOD_kg_O2_kg']
oxygen['ThOD_to_initial_DO_ratio']=oxygen['example_PHB_ThOD_kg']/oxygen['example_rain_DO_kg']
ck('PHB complete oxidation oxygen atom balance',close(2+2*4.5,2*4+3))
ck('cellulose complete oxidation oxygen atom balance',close(5+2*6,2*6+5))
# Capture counts vs mass, and dissolved contribution: a diagnostic counterexample, not a filter specification.
bins=[{'mass_fraction':0.2,'mass_capture':0.5},{'mass_fraction':0.5,'mass_capture':0.99},{'mass_fraction':0.3,'mass_capture':0.999}]
weighted=sum(x['mass_fraction']*x['mass_capture'] for x in bins)
ck('particle distribution normalized',close(sum(x['mass_fraction'] for x in bins),1))
# Bioconversion reported on monomer-feed basis; no unreported acid/enzymatic process yield is assumed.
bio={'reported_PHB_per_3HB_g_g':c['PHB_fermentation_yield_g_g'],'conditional_PHB_per_original_PHB_g_g':c['PHB_fermentation_yield_g_g']*c['PHB_monomer_g_mol']/c['PHB_repeat_g_mol']}
ck('hydrolysis water mass balance approximate',abs(c['PHB_monomer_g_mol']-c['PHB_repeat_g_mol']-18.015)<1e-9)
rr=k['discount_rate'];n=k['life_years'];crf=rr*(1+rr)**n/((1+rr)**n-1)
cost=[{'annual_fines_fraction':f,'annual_fines_kg':M*f,'maximum_avoided_virgin_purchase_JPY_year':M*f*k['replacement_JPY_kg']} for f in k['annual_fines_mass_fractions']]
capital=[{'net_annual_budget_JPY':b,'annual_opex_JPY':k['annual_extra_opex_JPY'],'capital_limit_JPY':max(0,b-k['annual_extra_opex_JPY'])/crf} for b in k['net_additional_annual_budget_JPY']]
through=[{'active_depth_m':d,'processed_mass_t':A*d*g['bulk_density_kg_m3']/1000,'required_bulk_throughput_t_h':A*d*g['bulk_density_kg_m3']/1000/(k['processing_minutes']/60)} for d in k['processed_bulk_depth_m']]
ck('capital annualization reversal',all(close(x['capital_limit_JPY']*crf+x['annual_opex_JPY'],x['net_annual_budget_JPY']) for x in capital))
ck('processing depth and rate scaling',close(through[2]['required_bulk_throughput_t_h']/through[0]['required_bulk_throughput_t_h'],45))
ck('aqueous mg L units',close(base['input_mg_L']*base['rain_volume_m3']/1000,10.8))
summary={'physical_tests':0,'physical_success_probability':None,'hypothesis':'H43 reduce breakage; capture before offsite decomposition','counts':{'erosion_scenarios':len(eros),'rain_scenarios':len(rain),'settling_sizes':len(sett),'numeric_checks':len(checks)},'area_horizontal_m2':Ah,'bed_mass_kg':M,'representative_erosion':representative,'representative_rain':base,'oxygen':oxygen,'particle_bins':bins,'particle_mass_weighted_capture':weighted,'dissolved_fraction_0_1_total_carbon_capture_at_filter_0_999':0.9*0.999,'biorecycling':bio,'capital_recovery_factor':crf,'annual_fines_value':cost,'capital_budget_inverse':capital,'bulk_processing':through}
for name,rows in [('erosion.csv',eros),('rain.csv',rain),('settling.csv',sett),('annual_fines_value.csv',cost),('capital_budget.csv',capital),('bulk_processing.csv',through)]:table(name,rows)
dump('results.json',summary);dump('checks.json',checks)
# Author-created scientific figures; no publisher images are redistributed.
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size':10,'svg.hashsalt':'cycle43-fixed'})
fig,axes=plt.subplots(1,2,figsize=(11.5,4.3),layout='constrained')
for rad in e['branch_radii_um']:
    z=[x for x in eros if x['branch_radius_um']==rad]
    axes[0].loglog([x['debris_diameter_um'] for x in z],[x['debris_90pct_mass_loss_days_same_rate'] for x in z],marker='o',label='branch radius '+str(rad)+' um')
axes[0].axhline(30,color='black',ls='--',label='30-day diagnostic')
axes[0].set(xlabel='Debris diameter (um)',ylabel='Time to 90% geometric mass loss (days)',title='Same surface recession rate; no mineralization model');axes[0].legend(fontsize=8);axes[0].grid(alpha=.2)
xs=[x/100 for x in range(101)]
for rad in [20,30,60]:
    u=30*(1-.9**.25)/100
    axes[1].plot([x*100 for x in xs],[(1-u*x*100/rad)**4 for x in xs],label='branch radius '+str(rad)+' um')
axes[1].set(xlabel='Equivalent wet-exposure days',ylabel='Branch bending stiffness / initial',ylim=(.84,1.01),title='Same recession: 0.007799 um/day (assumed)');axes[1].grid(alpha=.2);axes[1].legend(fontsize=8)
fig.savefig(D/'erosion_boundary.png',dpi=180);fig.savefig(D/'erosion_boundary.svg',metadata={'Date':None});plt.close(fig)
fig,axes=plt.subplots(1,2,figsize=(11.5,4.3),layout='constrained')
z=[x for x in rain if x['damage_fraction_per_day']==1e-5 and x['mobilized_fraction']==1 and x['filter_particle_mass_capture']==.999]
ix=list(range(len(z)))
axes[0].bar([i-.18 for i in ix],[100*x['system_capture_no_storage'] for x in z],width=.36,label='No storage')
axes[0].bar([i+.18 for i in ix],[99.9]*len(z),width=.36,label='Adequate storage + full later treatment')
axes[0].set(xticks=ix,xticklabels=['30','100','300'],xlabel='Vertical rain (mm/h), duration 1 h',ylabel='Whole-system particle mass capture (%)',ylim=(0,107),title='100 m3/h treatment; 99.9% filter is assumed');axes[0].legend(fontsize=8)
axes[1].bar(ix,[x['minimum_ideal_storage_m3'] for x in z],color='#26756f')
for i,x in enumerate(z): axes[1].text(i,x['minimum_ideal_storage_m3']+6,str(round(x['minimum_ideal_storage_m3'],1)),ha='center')
axes[1].set(xticks=ix,xticklabels=['30','100','300'],xlabel='Vertical rain (mm/h), duration 1 h',ylabel='Minimum ideal storage (m3)',ylim=(0,490),title='No freeboard, sediment, snowmelt or external catchment')
fig.savefig(D/'rain_capture.png',dpi=180);fig.savefig(D/'rain_capture.svg',metadata={'Date':None});plt.close(fig)
for svg_file in D.glob("*.svg"):
    svg_file.write_text("\n".join(line.rstrip() for line in svg_file.read_text(encoding="utf-8").splitlines())+"\n",encoding="utf-8",newline="\n")
import platform, numpy
dump("environment.json",{"python":platform.python_version(),"matplotlib":matplotlib.__version__,"numpy":numpy.__version__,"platform":platform.system(),"physical_tests":0})
print(json.dumps(summary,ensure_ascii=False))
