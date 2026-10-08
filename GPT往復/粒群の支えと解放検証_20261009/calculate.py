"""Independent EnviDat reanalysis + uncalibrated virtual-work link ensemble.
No success probability or measured performance of artificial firn is inferred.
Only standard library. Run python -X utf8 calculate.py.
"""
from pathlib import Path
import csv,json,math,statistics,itertools,hashlib
P=Path(__file__).resolve().parent
x=json.loads((P/'inputs.json').read_text(encoding='utf8'))
d=x['dataset']; source_path=P/'source_dataset_v1.csv'
if not source_path.exists():
 from urllib.request import urlopen
 with urlopen(d['stable_url'],timeout=60) as response: downloaded=response.read()
 if hashlib.sha256(downloaded).hexdigest()!=d['sha256']:raise ValueError('Source version changed; do not silently substitute')
 source_path.write_bytes(downloaded)
raw=source_path.read_bytes()
assert hashlib.sha256(raw).hexdigest()==d['sha256']
rows=list(csv.DictReader(raw.decode('utf-8-sig').splitlines(),delimiter=';'))
def num(r,k):return float(r[k]) if r[k].strip() else None
def fit(rr,key):
 valid=[r for r in rr if num(r,key) is not None and num(r,key)>0 and num(r,d['strength'])>0]
 X=[math.log(num(r,key)) for r in valid];Y=[math.log(num(r,d['strength'])) for r in valid]
 xm=statistics.mean(X);ym=statistics.mean(Y);s=sum((a-xm)*(b-ym) for a,b in zip(X,Y))/sum((a-xm)**2 for a in X);a=ym-s*xm
 R2=1-sum((b-a-s*c)**2 for c,b in zip(X,Y))/sum((b-ym)**2 for b in Y)
 return dict(n=len(valid),log_OLS_exponent=s,R2_in_sample=R2,log_intercept=a,method='equal parent-row weight, ordinary least squares in log space; not published ODR')
def med(rr,key):return statistics.median([num(r,key) for r in rr if num(r,key) is not None])
summary={};meanerrors=[];derived=[]
for cat in sorted({r['Category'] for r in rows}):
 rr=[r for r in rows if r['Category']==cat]
 indiv=sum(sum(num(r,f'Sample {i} Peak Stress [kPa]') is not None for i in range(1,9)) for r in rr)
 summary[cat]=dict(parent_rows=len(rr),listed_individual_strengths=indiv,fit_primary=fit(rr,d['E_primary']),fit_all_ROIs=fit(rr,d['E_sensitivity']),median_strength_kPa=med(rr,d['strength']),median_E_ROI01_MPa=med(rr,d['E_primary']),median_failure_strain=med(rr,'mean_strain_at_failure []'))
for r in rows:
 vals=[num(r,f'Sample {i} Peak Stress [kPa]') for i in range(1,9)];vals=[v for v in vals if v is not None]
 diff=statistics.mean(vals)-num(r,d['strength']);meanerrors.append(abs(diff))
 E=num(r,d['E_primary']);strength=num(r,d['strength']);ratio=strength/(1000*E) if E else None
 derived.append(dict(ID=r['ID'],category=r['Category'],phi=num(r,d['solid_fraction']),strength_kPa=strength,E_ROI01_MPa=E,E_allROIs_MPa=num(r,d['E_sensitivity']),strength_over_E=ratio,measured_mean_failure_strain=num(r,'mean_strain_at_failure []'),listed_strength_count=len(vals)))
pairs=[]
for a,b in itertools.combinations([r for r in derived if r['E_ROI01_MPa']],2):
 if max(a['phi'],b['phi'])/min(a['phi'],b['phi'])<=d['near_fraction_ratio']:
  pairs.append(dict(IDs=[a['ID'],b['ID']],categories=[a['category'],b['category']],phi=[a['phi'],b['phi']],E_ROI01_MPa=[a['E_ROI01_MPa'],b['E_ROI01_MPa']],strength_kPa=[a['strength_kPa'],b['strength_kPa']],E_ratio=max(a['E_ROI01_MPa'],b['E_ROI01_MPa'])/min(a['E_ROI01_MPa'],b['E_ROI01_MPa']),strength_ratio=max(a['strength_kPa'],b['strength_kPa'])/min(a['strength_kPa'],b['strength_kPa'])))
# Each model link opens by q*(gamma-gamma0), gamma0 uniform over [0,w].
# Virtual work gives tau = n_links*q*mean(F); it is not an empirical snow law.
a=x['links']; vg=a['arms_per_particle']*math.pi*a['arm_radius_m']**2*a['arm_length_m']
nb=a['solid_fraction']*a['coordination']/(2*vg);q=a['strain_transfer']*a['link_length_m'];k=a['link_stiffness_N_m']
def meanforce(g,w,Fc,res):
 gc=Fc/(k*q);lo=max(0,g-gc);hi=min(w,g)
 elastic=k*q*(g*(hi-lo)-(hi*hi-lo*lo)/2)/w if hi>lo else 0
 released=min(w,max(0,g-gc))/w
 return elastic+released*res*Fc

def rawforce(g,g0,Fc,res):
 elong=q*max(0,g-g0)
 return k*elong if k*elong<Fc else res*Fc

ensemble=[]
for Fc,w,res in itertools.product(a['release_forces_N'],a['activation_widths_strain'],a['residual_fractions']):
 gc=Fc/(k*q);gp=max(gc,w+res*gc);taup=nb*q*meanforce(gp,w,Fc,res);taur=nb*q*res*Fc
 ensemble.append(dict(release_force_N=Fc,activation_width=w,residual_fraction=res,single_link_release_strain=gc,ensemble_peak_strain=gp,all_links_released_strain=w+gc,peak_stress_budget_Pa=taup,residual_stress_budget_Pa=taur,residual_to_peak=taur/taup,elastic_release_energy_J_m3=nb*Fc*Fc/(2*k),peak_to_fullrelease_m={str(h):max(0,w+gc-gp)*h for h in a['active_band_thickness_m']}))
curves=[]
for w in a['activation_widths_strain']:
 Fc=.003;res=.05
 for j in range(501):
  g=a['strain_plot_max']*j/500
  f_uncap=k*q*(g*min(w,g)-min(w,g)**2/2)/w
  curves.append(dict(activation_width=w,strain=g,uncapped_stress_Pa=nb*q*f_uncap,capped_stress_Pa=nb*q*meanforce(g,w,Fc,res)))
winter=[]
for z,c in itertools.product(x['winter']['load_sharing_links'],x['winter']['projection_factors']):
 winter.append(dict(sharing_links=z,projection=c,minimum_link_force_N=x['winter']['load_per_grain_N']/(z*c)))
e=x['economic'];M=e['bed_volume_m3']*e['dry_bulk_density_kg_m3'];cost=[]
for frac,price in itertools.product(e['annual_reset_fraction'],e['reset_hypothesis_JPY_kg']):
 cost.append(dict(annual_reset_fraction=frac,process_price_JPY_kg=price,processed_kg_year=M*frac,processing_JPY_year=M*frac*price))
wear=[]
for chi,b in itertools.product(e['exposure_fractions'],e['cap_break_fraction']):
 replacement=e['events_per_year']*chi*b
 wear.append(dict(exposure_fraction=chi,damaged_material_fraction_per_exposure=b,initial_stock_ever_damaged_fraction=1-(1-chi*b)**e['events_per_year'],steady_replacement_kg_year=M*replacement,steady_replacement_fraction_year=replacement,purchase_JPY_year=M*replacement*e['price_hypothesis_JPY_kg'],within_hypothetical_2percent_budget=replacement<=e['yearly_loss_budget_fraction']))
checks=[]
def chk(n,c):
 checks.append(dict(name=n,passed=bool(c)))
 if not c:raise AssertionError(n)
chk('CSV source SHA256 matches',hashlib.sha256(raw).hexdigest()==d['sha256'])
chk('Unique parent IDs',len({r['ID'] for r in rows})==len(rows)==65)
chk('Strength means recomputed from listed values',max(meanerrors)<1e-6)
chk('299 listed measurements differ from paper278',sum(v['listed_individual_strengths'] for v in summary.values())==299 and 299!=278)
chk('62 complete modulus parent rows; not299 independent rows',sum(v['fit_primary']['n'] for v in summary.values())==62)
chk('No fabricated zeros for missing modulus',sum(r['E_ROI01_MPa'] is None for r in derived)==3)
# Independent midpoint quadrature against analytic uniform activation integral.
err=[]
for g in [.003,.03,.09,.101,.115,.15]:
 n=20000;w=.02;Fc=.003;res=.05
 direct=sum(rawforce(g,(i+.5)*w/n,Fc,res) for i in range(n))/n
 err.append(abs(meanforce(g,w,Fc,res)-direct))
chk('Mean force matches direct link quadrature',max(err)<1e-8)
chk('All links initially unloaded',meanforce(0,.02,.003,.05)==0)
chk('Post-release residual exact',math.isclose(meanforce(.2,.02,.003,.05),.05*.003))
chk('Zero residual gives zero post-release stress',meanforce(.2,.02,.003,0)==0)
chk('Peak bounded by link force cap',all(v['peak_stress_budget_Pa']<=nb*q*v['release_force_N']*(1+1e-12) for v in ensemble))
chk('Peak before full release',all(v['ensemble_peak_strain']<=v['all_links_released_strain'] for v in ensemble))
chk('Analytic peak is not below nearby points',all(meanforce(v['ensemble_peak_strain'],v['activation_width'],v['release_force_N'],v['residual_fraction'])>=max(meanforce(max(0,v['ensemble_peak_strain']+dlt),v['activation_width'],v['release_force_N'],v['residual_fraction']) for dlt in [-1e-6,1e-6])-1e-12 for v in ensemble))
chk('Winter one-direction projected force budget closes; not full vector equilibrium',all(math.isclose(v['minimum_link_force_N']*v['sharing_links']*v['projection'],x['winter']['load_per_grain_N']) for v in winter))
chk('Bed mass108t',M==108000)
chk('Replacement not confused with one-time damage probability',all(v['steady_replacement_fraction_year']>=v['initial_stock_ever_damaged_fraction']-1e-12 for v in wear))
chk('Our experiments and success probability remain unmeasured',x['physical_tests_our_material']==0 and x['success_probability'] is None)
result=dict(physical_tests_our_material=0,success_probability=None,data_summary=summary,data_audit=dict(parent_rows=65,listed_strengths=299,paper_claimed_tests=278,paper_claimed_CT_scans=70,max_mean_recompute_error_kPa=max(meanerrors),complete_E_rows=62,unresolved_count_difference=True,independent_inference_limit='parent rows may also share source conditions; fits descriptive only'),near_fraction_pairs=pairs,max_E_pair=max(pairs,key=lambda v:v['E_ratio']),max_strength_pair=max(pairs,key=lambda v:v['strength_ratio']),link_parameters=dict(particle_reference_volume_m3=vg,link_number_density_m3=nb,q_m_per_strain=q,all_active_uncapped_modulus_Pa=nb*k*q*q),ensemble=ensemble,winter=winter,reset_cost=cost,wear=wear,allowable_exposure_times_damage=e['yearly_loss_budget_fraction']/e['events_per_year'])
for fn,obj in [('results.json',result),('validation.json',dict(checks=checks,count=len(checks),all_passed=True,maximum_force_quadrature_error_N=max(err),scope='data parsing, algebra and integration only; no material validation'))]:
 (P/fn).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf8',newline='\n')
for fn,vals in [('derived_snow_rows.csv',derived),('link_curves.csv',curves)]:
 with (P/fn).open('w',encoding='utf8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(vals[0]),lineterminator='\n');w.writeheader();w.writerows(vals)
print(json.dumps(dict(parent_rows=len(rows),checks=len(checks),ensemble_cases=len(ensemble),near_fraction_pairs=len(pairs),winter_cases=len(winter),cost_cases=len(cost),wear_cases=len(wear),link_parameters=result['link_parameters']),ensure_ascii=False))
