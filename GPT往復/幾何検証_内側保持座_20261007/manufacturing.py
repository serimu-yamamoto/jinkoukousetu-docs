"""Mass accounting for one specified sheet-forming route, not a process claim."""
import json,math
from pathlib import Path
H=Path(__file__).resolve().parent
P=json.loads((H/'inputs.json').read_text(encoding='utf-8'))
M=json.loads((H/'mesh_validation.json').read_text(encoding='utf-8'))
A=json.loads((H/'results.json').read_text(encoding='utf-8'))
B=P['manufacturing']; rho=960
blank=B['pitch_mm']**2*B['stock_thickness_mm']
rows=[]
for shape in M['shapes']:
    v=shape['levels'][-1]['volume_mm3']
    part_mass=v*1e-9*rho
    accepted_yield=B['good_part_fraction']*v/blank
    target=B['target_good_kg_h']
    feed=target/accepted_yield
    good_parts_sec=target/(3600*part_mass)
    speed=(good_parts_sec/B['good_part_fraction'])*(B['pitch_mm']*1e-3)**2/B['line_width_m']
    recycle=[]
    cap=next(x for x in A['candidates'] if x['id']==shape['id'])['cost_upper_with_outward_envelope']['finished_price_cap_yen_kg']
    process=B['line_charge_yen_h']/target
    for fraction in B['scrap_recovery_fraction']:
        scrap=feed-target
        returned=fraction*scrap
        virgin=feed-returned
        assert math.isclose(virgin,target+(1-fraction)*scrap,rel_tol=1e-12)
        recycle.append(dict(recovery=fraction,virgin_kg_per_kg_good=virgin/target,returned_kg_h=returned,
                            rejected_unrecovered_kg_h=(1-fraction)*scrap,
                            virgin_resin_price_upper_yen_kg_before_other_costs=max(0,cap-process)/(virgin/target),
                            note='Recovery in factory only; unrecovered mass must be managed. Not authorized environmental discharge.'))
    rows.append(dict(id=shape['id'],nominal_mesh_volume_mm3=v,particle_mass_kg=part_mass,
                     geometric_part_to_blank_volume_fraction=v/blank,
                     first_pass_good_product_mass_fraction=accepted_yield,
                     processed_feed_kg_per_kg_good=1/accepted_yield,
                     total_processed_feed_kg_h_at_target=feed,
                     good_particles_per_second_at_target=good_parts_sec,
                     required_line_speed_m_s_at_target=speed,recycle=recycle))
    rows[-1]['assumed_line_charge_per_good_kg']=process
    rows[-1]['conservative_finished_price_cap_yen_kg']=cap
out=dict(scope=B['scope'],blank_volume_mm3=blank,assumed_resin_density_kg_m3=rho,
         physical_process_validated=False,tooling_quote_obtained=False,rows=rows)
(H/'manufacturing_results.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps(out))
