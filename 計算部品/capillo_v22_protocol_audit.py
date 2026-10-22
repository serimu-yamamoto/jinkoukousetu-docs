"""Audit of proposed 100g protocol. Conditional arithmetic; empirical trials = 0."""
import math
from capillo_v22_summary_audit import accepted_output, carrier_water_budget
NAMES=["calcite","kaolinite","CNF","MCC","CMC_Ca","gellan_Ca","water"]
RHO=[2.71,2.6,1.5,1.5,1.55,1.5,1.]
CORE=[22.,4.5,4.5,0.,2.8,1.,45.2]
SHELL=[8.,1.5,0.,2.5,.7,.5,6.8]
def mixture_volume(masses):
    return sum(m/r for m,r in zip(masses,RHO))
def recycle_with_virgin_shell(recovered_t,shell_mass_fraction=.2):
    total=recovered_t/(1-shell_mass_fraction)
    return dict(recovered_core_t=recovered_t,finished_t=total,virgin_shell_t=total-recovered_t)
def slope_example(normal_thickness=.45,normal_saturated_height=2/9,angle=30.,bulk_density=487.,particle_density=1180.40):
    theta=math.radians(angle);g=9.81;porosity=1-bulk_density/particle_density
    base=bulk_density*g*normal_thickness
    added=1000*g*porosity*normal_saturated_height
    total_weight=base+added
    normal=total_weight*math.cos(theta)
    shear=total_weight*math.sin(theta)
    pore=1000*g*normal_saturated_height*math.cos(theta)
    return dict(assumptions="fixed volume; only interparticle air fills; slope-parallel steady seepage; no anchors or interface cohesion",
        dry_normal_kpa=base*math.cos(theta)/1000,dry_shear_kpa=base*math.sin(theta)/1000,
        added_water_kg_m2=added/g,total_normal_kpa=normal/1000,driving_shear_kpa=shear/1000,
        pore_pressure_kpa=pore/1000,effective_normal_kpa=(normal-pore)/1000,
        friction_only_safety_factors={str(d):(normal-pore)*math.tan(math.radians(d))/shear for d in [10.,18.,30.]})
def audit():
    full=[c+s for c,s in zip(CORE,SHELL)]
    vc=mixture_volume(CORE);vs=mixture_volume(SHELL)
    frac=vs/(vc+vs);geometry_frac=1-(2.6/3.)**2
    w_shell_geometry=geometry_frac*(20/vs)/(geometry_frac*(20/vs)+(1-geometry_frac)*(80/vc))
    recovered=1051.92;net_hours=recovered/.75
    re=recycle_with_virgin_shell(recovered)
    next_formula=[.8*a+b for a,b in zip(full,SHELL)]
    e0=1-487/1180.4
    density_gain=.2;volume_loss=1-1/(1+density_gain)
    e1=1-(487*(1+density_gain))/1180.4
    result=dict(empirical_trials=0,success_probability=None,
        composition=dict(names=NAMES,core_g=CORE,shell_g=SHELL,total_g=full,core_total_g=sum(CORE),shell_total_g=sum(SHELL),
          core_no_gas_cm3=vc,shell_no_gas_cm3=vs,core_W_S=CORE[-1]/sum(CORE[:-1]),shell_W_S=SHELL[-1]/sum(SHELL[:-1]),
          minimum_CNF_solids_if_no_other_carrier_water=4.5/(4.5+45.2),
          CNF_9_5pct=carrier_water_budget(4.5,.095,45.2)),
        geometry=dict(no_gas_equal_axial_speed_assumption=True,shell_volume_fraction=frac,
          die_shell_area_fraction=geometry_frac,shell_mass_fraction_implied_by_die=w_shell_geometry,
          equal_speed_wall_mm=(3-3*math.sqrt(1-frac))/2),
        recycling=dict(old_net_hours=net_hours,output_1402_56_calendar_h_t=accepted_output(750,net_hours,1,.85,.8)/1000,
          output_1402_56_running_h_t=accepted_output(750,net_hours,1,1.,.8)/1000,
          output_1760_calendar_h_t=accepted_output(750,8,220,.85,.8)/1000,
          fixed_finished_1051_92_core_t=recovered*.8,fixed_finished_1051_92_virgin_t=recovered*.2,
          unused_recovered_if_finished_fixed_t=recovered*.2,
          all_recovered_used=re,
          net_hours_for_all_recovered_and_virgin=re["finished_t"]/.75,
          required_uptime_for_all_recovered=re["finished_t"]/(.75*1760),
          minimum_net_rate_at_85pct_uptime_kg_h=re["finished_t"]*1000/(1760*.85),
          first_recycle_formula_per_100g_if_uniform_old_formula=next_formula),
        civil=dict(cell_top_depth_mm=[450-150,450-200],minimum_bottom_depth_mm=[450+150,450+200],
          slope=slope_example()),
        measurement=dict(tan_delta_point3_Gdoubleprime_over_Gprime=.3,
          density_gain_20pct_volume_loss=volume_loss,initial_interparticle_porosity=e0,final_interparticle_porosity_if_particle_volume_fixed=e1,
          relative_interparticle_void_volume_loss=volume_loss/e0),
        alternative_water=dict(solids_fixed_48g={str(w):dict(total_mass_g=48+w,water_mass_fraction=w/(48+w)) for w in [42.,35.,28.]}))
    assert sum(CORE)==80 and sum(SHELL)==20
    assert all(abs(a-b)<1e-12 for a,b in zip(full,[30,6,4.5,2.5,3.5,1.5,52]))
    assert abs(vc+vs-73.302534191595)<1e-10
    assert geometry_frac>frac
    assert 4.5/(4.5+45.2)<.095<.1
    assert abs(result["recycling"]["output_1402_56_running_h_t"]-841.536)<1e-6
    assert abs(re["finished_t"]-1314.9)<1e-6
    assert abs(sum(next_formula)-100)<1e-9 and next_formula[2]<full[2] and next_formula[3]>full[3]
    assert min(result["civil"]["cell_top_depth_mm"])<300
    assert result["civil"]["slope"]["effective_normal_kpa"]>0
    assert abs(volume_loss-1/6)<1e-12
    result["arithmetic_checks"]=11
    return result
