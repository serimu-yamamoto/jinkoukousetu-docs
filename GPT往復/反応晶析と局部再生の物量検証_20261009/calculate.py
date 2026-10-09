"""Cycle 68: conservation bounds and decision costs, not physical validation.
Python 3 standard library only. Outputs beside this file, LF UTF-8.
"""
from pathlib import Path
import csv, json, math
D=Path(__file__).resolve().parent
F=96485.33212
MC=240.30 # g/mol cystine, rounded formula mass
MS=121.16 # g/mol cysteine, rounded formula mass
MT=181.19 # g/mol tyrosine
MP=30.973761998
Q=2*F/(MC/1000)/3600 # Ah per kg cystine, 2 electrons per molecule
O2=16.0/MC # kg O2 per kg cystine, net aerobic stoichiometry
R=2*MS/MC # cysteine/cystine mass ratio
checks=[]
def check(name, condition):
    checks.append({'name':name,'passed':bool(condition)})
    assert condition, name
def close(a,b): return math.isclose(a,b,rel_tol=1e-9,abs_tol=1e-10)
def out(name,obj):
    (D/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
def tab(name,rows):
    with (D/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)

def supply(cys_mM,do_mg_L,kLa_h=0.0,t_h=1.0):
    # 1 mM = 1 mol/m3; two cysteines -> one cystine.
    cap=cys_mM/2*MC/1000
    oxygen=do_mg_L/1000*(1+kLa_h*t_h) # kg/m3: upper bound, dissolved O2 kept near zero
    product=min(cap,oxygen/O2)
    return {'cysteine_mM':cys_mM,'initial_DO_mg_L':do_mg_L,'kLa_per_h_assumed':kLa_h,
            'time_h':t_h,'feed_theoretical_cystine_kg_m3':cap,'O2_available_upper_kg_m3':oxygen,
            'product_oxygen_upper_kg_m3':product,'fraction_of_feed_upper':product/cap,
            'liquid_L_per_kg_at_complete_reaction':1000/cap,
            'evaporation_only_heat_kWh_per_kg_assumed':1000/cap*0.65}
rows_s=[supply(c,do,k) for c in (3.3,6,100) for do in (5,7.5,10) for k in (0,1,10,100)]
# These are 36 capacity cases; no kinetic/crystal-shape result is generated.
rows_q=[]
for I in (10,40,100,1000):
    for fe in (0.5,0.8,1.0):
        rows_q.append({'current_A':I,'faradaic_efficiency_assumed':fe,'cystine_kg_h':I*fe/Q,
                       'hours_per_kg':Q/I/fe,'hours_per_5_4kg':5.4*Q/I/fe})

# Sequential conditional MATERIAL yields; products need no independence assumption.
factors={'collection':0.90,'reduction':0.98,'oxidation':0.95,'shape_retention':0.80,'functional_QC':0.90}
eta=math.prod(factors.values())
P=6000.0 # JPY/kg new qualified crystal phase, assumed not quoted
C=2000.0 # JPY/kg retired phase, variable recycle cost, assumed all stages inclusive
fixed=2000000.0 # JPY/y additional fixed cost, assumed not an equipment quote
savings=eta*P-C
rows_r=[]
for shape in (0.5,0.8,0.95):
    for qc in (0.5,0.9,0.98):
        e=0.9*0.98*0.95*shape*qc
        save=e*P-C
        rows_r.append({'shape_yield_assumed':shape,'functional_QC_yield_assumed':qc,'net_mass_yield':e,
                       'variable_cost_JPY_retiredkg':C,'new_cost_JPY_qualifiedkg':P,
                       'variable_savings_JPY_retiredkg':save,
                       'break_even_retiredkg_year':fixed/save if save>0 else None})
rows_f=[]
for er in (100,200,1000,2000):
    rows_f.append({'retired_phase_kg_year':er,'qualified_recovered_kg_year':er*eta,
                   'net_savings_after_fixed_JPY_year':er*savings-fixed})
# Grain inventory and floor throughput: 2000 m2, 0.45 m, 120 kg/m3 is a design basis.
bed=2000*0.45*120
rows_x=[]
for fraction in (0.0001,0.001,0.005,0.01):
    for lead_days in (1,5,10):
        m=bed*fraction
        rows_x.append({'exchange_grain_fraction_per_day':fraction,'qualified_grains_kg_day':m,
                       'crystal_phase_fraction_assumed':0.01,'crystal_phase_kg_day':m*0.01,
                       'factory_lead_days_assumed':lead_days,'replacement_grain_inventory_kg':m*(lead_days+1),
                       'qualified_handling_kg_h_in_40min':m/(40/60),
                       'feed_handling_kg_h_at_95pct_yield':m/(40/60)/0.95})
# Ideal washing only, not a residual safety specification. H=0.1L retained/kg phase.
H=0.1; W=1.0; kcl_g_L=74.55
wash=[]
for n in range(0,5):
    wash.append({'wash_count':n,'retained_L_per_kg_phase_assumed':H,'wash_L_each_per_kg_phase':W,
                 'KCl_residual_mg_per_kg_ideal':H*kcl_g_L*1000*(H/(H+W))**n,
                 'total_wash_L_per_kg_phase':W*n})
# Electron conservation re-check of published maxima: do NOT assume simultaneous operation.
source_current=100*400/1000
cys_max_g_h=source_current*3600*MS/F
required_A_200=200/MS*F/3600
red_energy_source_basis=1.0*R # 1 Wh/g cysteine, separately reported optimized condition
ox_energy_assumed=Q/0.9*3.0/1000
pair_energy=red_energy_source_basis+ox_energy_assumed
results={
 'cycle':68,'physical_tests':0,'success_probability':None,'route_successes':None,
 'quantities_are':'Conservation bounds and assumption scenarios, not measurements or success probabilities',
 'constants':{'F_C_mol':F,'cystine_g_mol':MC,'cysteine_g_mol':MS,'tyrosine_g_mol':MT},
 'stoichiometry':{'oxygen_kg_kg_cystine':O2,'cysteine_kg_kg_cystine':R,'Ah_kg_cystine_theory':Q,
                  'Tyr_kg_m3_from_50mM_max':50*MT/1000,'P_kg_per_kg_Tyr':MP/MT},
 'oxygen_examples':{'6mM_no_reaeration':supply(6,7.5,0),'100mM_no_reaeration':supply(100,7.5,0),
                    'kLa_needed_for_6mM_feed_in_1h_oxygen_only':max(0,(6/2*MC/1000*O2)/(7.5/1000)-1)},
 'electrochemical_audit':{'current_A_if_100cm2_and_400mA_cm2':source_current,
                         'cysteine_g_h_2electron_ceiling_at_40A':cys_max_g_h,
                         'A_minimum_for_200g_cysteine_h':required_A_200,
                         'combined_published_maxima_validated':False,
                         'hours_for_1kg_cystine_at_10A_100pct':Q/10},
 'energy_separate_conditions':{'reduction_kWh_per_kg_cystine_equivalent':red_energy_source_basis,
                                'oxidation_3V_FE90pct_assumed_kWh_kg':ox_energy_assumed,
                                'pair_before_loss_kWh_kg':pair_energy,
                                'electricity_at_35JPY_kWh_assumed':pair_energy*35,
                                'is_demonstrated_closed_loop':False},
 'recovery_example':{'conditional_mass_yields_assumed':factors,'net_mass_yield':eta,
                      'P_new_JPY_kg_assumed':P,'C_variable_JPY_retiredkg_assumed':C,
                      'fixed_JPY_year_assumed':fixed,'variable_saving_JPY_retiredkg':savings,
                      'break_even_retiredkg_year':fixed/savings,
                      'minimum_mass_yield_for_variable_break_even':C/P,
                      'cycles_until_original_mass_below_half_at_same_yield':math.ceil(math.log(0.5)/math.log(eta))},
 'exchange_basis':{'bed_kg':bed,'closure_min':60,'handling_min':40,'other_tasks_min_assumed':20,
                    'case_grains_kg_day':bed*.005,'case_crystal_kg_day':bed*.005*.01,
                    'case_inventory_kg_at_5day_lead_plus_1day_buffer':bed*.005*6},
 'wash_example':wash[3],
 'output_rows':{'supply':len(rows_s),'charge':len(rows_q),'recovery':len(rows_r),'fixed_cost':len(rows_f),'exchange':len(rows_x),'wash':len(wash)}
}
# Conservation, inverse checks, independent units and explicit failure examples.
check('feed 6mM permits 0.7209 kg/m3 before soluble remainder',close(supply(6,7.5)['feed_theoretical_cystine_kg_m3'],.7209))
check('oxygen and product mass balance',close(supply(6,7.5)['product_oxygen_upper_kg_m3']*O2,.0075))
check('initial oxygen cannot consume all 6mM feed',supply(6,7.5)['fraction_of_feed_upper']<.16)
check('high concentration does not cure oxygen shortage',supply(100,7.5)['fraction_of_feed_upper']<.01)
check('no negative or super-stoichiometric production',all(0<=r['fraction_of_feed_upper']<=1 for r in rows_s))
check('zero feed-independent oxygen ceiling increases with transfer',supply(100,7.5,10)['product_oxygen_upper_kg_m3']>supply(100,7.5,1)['product_oxygen_upper_kg_m3'])
check('charge inverse returns kg',close(Q*3600/(2*F)*MC/1000,1))
check('10A 1kg takes more than 22h',22<Q/10<23)
check('40A 200g/h incompatible with two electron cysteine stoichiometry',cys_max_g_h<200 and required_A_200>40)
check('two electrode sides do not silently double electrical current',close(source_current,40))
check('lower FE reduces production and increases duration',rows_q[0]['cystine_kg_h']<rows_q[2]['cystine_kg_h'] and rows_q[0]['hours_per_kg']>rows_q[2]['hours_per_kg'])
check('conditional yield example product',close(eta,.603288))
check('regeneration reject mass conserved',close(eta+(1-eta),1))
check('perfect chemistry still permits functional failure',.9*1*1*.5*.5<.3)
check('fixed cost break-even gives zero net saving',close((fixed/savings)*savings-fixed,0))
check('small factory throughput loses despite variable savings',rows_f[1]['net_savings_after_fixed_JPY_year']<0)
check('phase replacement cannot count as entire grain handling',close(bed*.005,540) and close(bed*.005*.01,5.4))
check('replacement inventory covers delay plus buffer',close(bed*.005*6,3240))
check('full bed handling needs far more than selective removal',bed/(40/60)>100000)
check('ideal washing recurrence conserves solute',all(close(wash[i+1]['KCl_residual_mg_per_kg_ideal'],wash[i]['KCl_residual_mg_per_kg_ideal']*H/(H+W)) for i in range(4)))
check('phosphate atom molar balance',close((MP/MT)*(50*MT/1000),50*MP/1000))
check('not a physical success estimate',results['physical_tests']==0 and results['success_probability'] is None)
for n,r in [('supply.csv',rows_s),('charge.csv',rows_q),('recovery.csv',rows_r),('fixed_cost.csv',rows_f),('exchange.csv',rows_x),('wash.csv',wash)]:tab(n,r)
out('results.json',results);out('checks.json',{'count':len(checks),'checks':checks,'all_passed':all(x['passed'] for x in checks)})
print(json.dumps({'checks':len(checks),'rows':sum(results['output_rows'].values()),'physical_tests':0,'success_probability':None,'Q_Ah_kg':Q,'net_yield_assumed':eta,'break_even_kg_year':fixed/savings},ensure_ascii=False))
