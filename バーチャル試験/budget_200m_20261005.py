"""Reproducible screening, not a validated machine design or supplier quote.

Python standard library only. Run next to the inputs; results are UTF-8 JSON.
All costs called ceilings are procurement allocations, not predicted prices.
"""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
P = json.loads((HERE / 'budget_200m_inputs_20261005.json').read_text(encoding='utf-8'))
g = 9.81
theta = math.radians(P['geometry']['slope_deg'])
s, c = math.sin(theta), math.cos(theta)
L, W = P['geometry']['length_m'], P['geometry']['width_m']
t, f = P['time'], P['force']

def minutes(length, speed, duty, cure):
    return length / speed / duty / 60 + t['setup_clear_park_inspect_min'] + cure

def force(mass, rolling, payload, mu, tool, deployed=L):
    body = mass * g * (s + rolling*c)
    material = payload * f['wet_bulk_kg_m3'] * g * (s + mu*c)
    rope_each = deployed * f['rope_linear_kg_m'] * g * (s + f['rope_support_mu']*c)
    machine = body + material + tool
    service = machine/2 + rope_each
    design = service * f['load_multiplier']
    return dict(machine_kN=machine/1000, rope_each_kN=rope_each/1000,
                line_each_service_kN=service/1000, line_each_screen_kN=design/1000,
                screen_within_50kN=design <= f['per_side_service_N'],
                each_motor_kW_at_service=service*t['speed_m_s']/f['drive_efficiency']/1000,
                each_motor_kW_at_screen=design*t['speed_m_s']/f['drive_efficiency']/1000)

nominal = force(f['machine_kg'], f['rolling_resistance'], f['payload_m3'],
                f['payload_slide_mu'], f['tool_drag_N'])
stress = force(6000, .3, 1, .6, 20000)
zero_payload = force(f['machine_kg'],f['rolling_resistance'],0,f['payload_slide_mu'],f['tool_drag_N'])
payload_increment_per_m3 = (force(f['machine_kg'],f['rolling_resistance'],1,f['payload_slide_mu'],f['tool_drag_N'])['line_each_screen_kN']
                            -zero_payload['line_each_screen_kN'])
nominal_force_limited_payload_m3 = (f['per_side_service_N']/1000-zero_payload['line_each_screen_kN'])/payload_increment_per_m3
pressure = {str(contact_m): f['machine_kg']*g*c/(W*contact_m)/1000
            for contact_m in [.03, .05, .10]}
# Pressure assumes ALL normal weight on ONE roller row; multi-row loads reduce it.
# This is not a required material pressure or a Hertzian maximum.
timing_grid = [dict(speed_m_s=v, duty=d, cure_min=q,
                    closure_min=minutes(L,v,d,q), within_60=minutes(L,v,d,q)<=60)
               for v in [.2,.3,.4,.5,.6,.7,.8]
               for d in [.65,.75,.8,.9]
               for q in [0,5,10,20,60]]
force_grid = [dict(mass_kg=m, rolling=r, payload_m3=v, tool_kN=tool/1000,
                   **force(m,r,v,.4,tool))
              for m in [3000,4000,6000] for r in [.05,.15,.3]
              for v in [.1,.3,1] for tool in [5000,10000,20000]]
base = sum(v for _,v in P['budget_million_yen'])
pretax = base+P['reserve_million_yen']
gross = pretax*(1+P['tax_rate'])
b = P['source_benchmark']
benchmark = dict(active_width_m=b['units']*b['box_width_m'],
                 overlap_each_m=(b['units']*b['box_width_m']-W)/(b['units']-1),
                 total_usd=b['units']*b['ginzu_usd_each'],
                 listed_weight_total_kg=b['units']*b['listed_weight_lb']*.45359237,
                 fx_scenario_million_yen={str(x):b['units']*b['ginzu_usd_each']*x/1e6
                    for x in b['fx_jpy_per_usd_scenarios']},
                 full_drain_200mm_exworks_million_yen=L*W*.2*b['quarry_4020_jpy_m3']/1e6)
material = [dict(volume_m3=v,dry_bulk_kg_m3=r,ex_tax_jpy_kg=p,
                 mass_t=v*r/1000, material_ex_tax_million_yen=v*r*p/1e6,
                 equipment_plus_material_gross_million_yen=gross+v*r*p*(1+P['tax_rate'])/1e6)
             for v in P['material']['volume_cases_m3']
             for r in P['material']['dry_bulk_cases_kg_m3']
             for p in P['material']['price_cases_ex_tax_jpy_kg']]
# All-in alternative ceiling: 100m equipment/civil +25m reserve; not a quote.
material_room = 200/(1+P['tax_rate'])-100-25
all_in_limits = [dict(volume_m3=v,dry_bulk_kg_m3=r,
                      max_ex_tax_jpy_kg=material_room*1e6/(v*r))
                 for v in [6000,8000] for r in [500,1500]]
storm = P['storm']
captured = storm['mobilized_m3']*storm['capture_fraction']
reuse = captured*storm['reusable_fraction']
reject = captured-reuse
lost = storm['mobilized_m3']-captured
trips = math.ceil(reuse/storm['payload_recovery_m3'])
trip_minutes = (storm['average_haul_m']/storm['loaded_speed_m_s']/storm['loaded_duty']
                +storm['average_haul_m']/storm['empty_speed_m_s'])/60+storm['load_unload_min']
life_capex = 150 # reserve consumption excluded from this baseline sensitivity
rate, years = .05, 10
crf = rate*(1+rate)**years/((1+rate)**years-1)
out = dict(status=P['status'], nominal_force=nominal, stress_force=stress,
    nominal_force_limited_payload_m3=nominal_force_limited_payload_m3,
    isolated_groove_example=dict(width_m=4,length_m=5,depth_m=.02,required_m3=4*5*.02,
                                nominal_payload_shortfall_m3=max(0,4*5*.02-f['payload_m3'])),
    pressure_kPa_single_row_all_weight=pressure,
    nominal_closure_min=minutes(L,t['speed_m_s'],t['duty'],t['cure_min']),
    min_speed_for_60_with_10min_cure=L/(60*(60-12-10)*.75),
    timing_grid=timing_grid, force_grid=force_grid,
    budget=dict(base_million_yen=base,reserve_million_yen=P['reserve_million_yen'],
                pretax_million_yen=pretax,tax_million_yen=pretax*P['tax_rate'],
                gross_million_yen=gross,headroom_to_200_million_yen=200-gross),
    benchmark=benchmark, material_sensitivity=material,
    all_in_material_room_million_yen=material_room,all_in_material_unit_limits=all_in_limits,
    storm=dict(captured_m3=captured,reuse_m3=reuse,reject_m3=reject,lost_m3=lost,
               makeup_m3=reject+lost,trips=trips,trip_min=trip_minutes,haul_hours=trips*trip_minutes/60),
    annual_capital_equivalent_million_yen={str(cap):cap*crf for cap in [100,150,180]},
    upkeep_sensitivity_million_yen=[3,6,10],
    checks=dict(timing_scenarios=len(timing_grid),force_scenarios=len(force_grid),
                passes_are_arithmetic_only=True, physical_validation=False,supplier_quotes=0))
assert abs(gross-198)<1e-10
assert abs(reuse+reject+lost-storm['mobilized_m3'])<1e-10
assert minutes(L,.6,.75,10)<60<minutes(L,.5,.75,10)
assert nominal['screen_within_50kN'] and not stress['screen_within_50kN']
assert len(timing_grid)==140 and len(force_grid)==81
assert min(x['max_ex_tax_jpy_kg'] for x in all_in_limits)>0
assert b['units']*b['box_width_m']>=W
output = HERE/'budget_200m_results_20261005.json'
output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:out[k] for k in ['nominal_force','stress_force','nominal_closure_min','budget','benchmark','storm','annual_capital_equivalent_million_yen','checks']},ensure_ascii=False,indent=2))
