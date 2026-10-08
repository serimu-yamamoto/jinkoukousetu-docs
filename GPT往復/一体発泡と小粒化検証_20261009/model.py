"""Conditional H53 morphology, rain storage, rebound and production arithmetic.
No measured H53 material, no success probability. Python standard library only.
"""
import csv,json,math
from pathlib import Path
P=Path(__file__).resolve().parent
checks=[]
def check(name,ok):
    if not ok: raise AssertionError(name)
    checks.append({"name":name,"passed":True})
def near(a,b):return math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-15)
def js(name,data):
    (P/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
def csvout(name,rows):
    with (P/name).open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=rows[0],lineterminator="\n");w.writeheader();w.writerows(rows)
rho_f,rho_s=218.,1120.
porosity_reported=.788
porosity_from_density=1-rho_f/rho_s
# Transcribed numbers retain their own specimen and measurement scope.
source=[]
for name,rho,cell,strain in [("CF",221,19.4,.50),("WF1.77",218,19.6,.279),("WF1.94",220,19.6,.339),("WF2.16",218,19.6,.409)]:
    source.append({"source":"10.1021/acs.iecr.2c00001","sample":name,
      "foam_density_kg_m3":rho,"cell_diameter_um":cell,
      "axial_strain_at_0p2_MPa":strain,"E_MPa":None,
      "temperature_C":None,"scope":"author manuscript; 4 mm cuboids; not 50 C qualification"})
for T,E in [(-20,1.19),(23,.87),(40,.82)]:
    source.append({"source":"10.1186/s40712-024-00149-9","sample":"ETPU_about250kg_m3",
      "foam_density_kg_m3":250,"cell_diameter_um":None,
      "axial_strain_at_0p2_MPa":None,"E_MPa":E,
      "temperature_C":T,"scope":"published text; slow compression; not cut particles"})
# Geometric affected layer, not measured rupture or opened-cell fractions.
cuts=[]
def cube_core(D,ell):return max(1-2*ell/D,0)**3
def profile_core(L,ell):return max(1-2*ell/L,0)
def cylinder_core(d,L,ell):return max(1-2*ell/d,0)**2*max(1-2*ell/L,0)
for cell in (19.6,71,231,410):
    for depth in (.5,1):
        ell=cell*depth
        for D in (100,300,500,1000):
            cuts.append({"shape":"six_cut_faces_cube","dimension_um":D,"length_um":D,
                         "cell_um":cell,"depth_cells":depth,"affected_fraction":1-cube_core(D,ell)})
        for d in (50,100):
            cuts.append({"shape":"cut_cylinder_branch","dimension_um":d,"length_um":150,
                         "cell_um":cell,"depth_cells":depth,"affected_fraction":1-cylinder_core(d,150,ell)})
        for L in (300,500,1000):
            cuts.append({"shape":"profile_cut_at_two_ends_only","dimension_um":500,"length_um":L,
                         "cell_um":cell,"depth_cells":depth,"affected_fraction":1-profile_core(L,ell)})
check("affected-layer geometry has correct zero and fully affected limits",
      near(cube_core(500,0),1) and cube_core(50,30)==0 and cylinder_core(50,150,30)==0)
check("all affected fractions bounded by geometry",all(0<=x["affected_fraction"]<=1 for x in cuts))
check("two end cuts affect less volume than six face cuts at equal 500 um size",
      all(1-profile_core(500,c*d)<1-cube_core(500,c*d) for c in (19.6,71) for d in (.5,1)))
D80=2*19.6/(1-.8**(1/3))
check("80 percent retained interior inversion",near(cube_core(D80,19.6),.8))
# Single shape for mass comparison: cubic core + six dense cylindrical arms.
# This is a mass-equivalent candidate, not a mold/cavity manufacturing drawing.
particles=[]
for D in (300,500,750):
    for t in (0,2,5,10):
        Vcore=(D*1e-6)**3
        Vi=((D-2*t)*1e-6)**3
        Vs=Vcore-Vi
        Va=6*math.pi*(25e-6)**2*150e-6
        V=Vcore+Va
        m=rho_f*Vi+rho_s*(Vs+Va)
        rho=m/V
        particles.append({"core_side_um":D,"skin_um":t,"arms":6,"arm_radius_um":25,
          "arm_length_um":150,"envelope_volume_m3":V,"foam_inner_m3":Vi,
          "dense_skin_and_arms_m3":Vs+Va,"mass_kg":m,"envelope_density_kg_m3":rho,
          "packing_to_bulk120":120/rho,"mass_at_phi055_t":900*.55*rho/1000,
          "dense_fraction_of_mass":rho_s*(Vs+Va)/m,
          "extra_mass_over_all_foam_same_envelope_t":900*.55*(rho-rho_f)/1000})
selected=next(x for x in particles if x["core_side_um"]==500 and x["skin_um"]==5)
check("particle phase volumes close exactly",
      all(near(x["foam_inner_m3"]+x["dense_skin_and_arms_m3"],x["envelope_volume_m3"]) for x in particles))
check("particle mass independently reconstructed by mixture density",
      all(near(x["mass_kg"],x["envelope_volume_m3"]*x["envelope_density_kg_m3"]) for x in particles))
check("skin thickness raises mass at each fixed core size",
      all([x["mass_kg"] for x in particles if x["core_side_um"]==d]==sorted(x["mass_kg"] for x in particles if x["core_side_um"]==d) for d in (300,500,750)))
check("void fraction discrepancy retained rather than silently overwritten",
      abs(porosity_reported-porosity_from_density)>.01)
# Water accessible storage sensitivity. No saturation/retention measurements exist.
water=[]
for mode in ("six_cut_faces_cube","profile_cut_at_two_ends_only"):
    for layer in (.5,1):
        f=1-(cube_core(500,19.6*layer) if mode=="six_cut_faces_cube" else profile_core(500,19.6*layer))
        for voidlabel,void in (("published",porosity_reported),("density_identity",porosity_from_density)):
            for retained in (.01,.1,1):
                water.append({"shape":mode,"size_um":500,"cell_um":19.6,
                  "depth_cells":layer,"void_source":voidlabel,"void_fraction":void,
                  "affected_fraction":f,"accessible_and_retained_fraction_assumed":retained,
                  "water_t":900*.55*void*f*retained,
                  "not_a_measured_retention":True})
check("water bounded by total foam pore capacity",all(x["water_t"]<=900*.55*x["void_fraction"] for x in water))
# Packing and intraparticle volume changes separated. J is NOT axial strain.
groom=[]
for phi in (.45,.55,.65):
    for J in (.70,.85,.95):
        target=.450
        initial=target*phi/.45
        loaded=target*J
        wrong_recovered=target/J
        groom.append({"final_packing_assumed":phi,"particle_volume_ratio_under_load_J":J,
                      "loose_height_for_same_mass_mm":initial*1000,
                      "loaded_setting_for_450mm_final_mm":loaded*1000,
                      "final_height_if_loaded_setting450_mm":wrong_recovered*1000,
                      "rebound_if_loaded_setting450_mm":(wrong_recovered-target)*1000,
                      "pressure_to_J_and_packing_not_measured":True})
check("grooming mass balance independently closes on initial loaded and recovered states",
      all(near(x["loose_height_for_same_mass_mm"]*.45,
               x["loaded_setting_for_450mm_final_mm"]*x["final_packing_assumed"]/x["particle_volume_ratio_under_load_J"])
          and near(x["loaded_setting_for_450mm_final_mm"]/x["particle_volume_ratio_under_load_J"],450)
          for x in groom))
# Factory volume/mass throughput and the discrete-mold bottleneck.
M=selected["mass_at_phi055_t"]*1000
N=900*.55/selected["envelope_volume_m3"]
hours=30*16*.75
rate=N/(hours*3600)
pitch=.8e-3
n_mold=1/pitch**2
mold_rate=n_mold/30
roller_rate=1*.5/pitch**2
production={
 "mass_kg":M,"particle_count":N,"scheduled_hours":30*16,"availability":.75,
 "productive_hours":hours,"minimum_net_mass_kg_h":M/hours,
 "required_particles_s_when_running":rate,"assumed_pitch_m":pitch,
 "assumed_mold_area_m2":1,"assumed_cycle_s":30,
 "ideal_cavities_per_mold":n_mold,"ideal_parallel_mold_count":math.ceil(rate/mold_rate),
 "assumed_roll_width_m":1,"assumed_roll_speed_m_min":30,
 "ideal_parallel_roll_count":math.ceil(rate/roller_rate),
 "yield_assumed":1,"cavity_and_roll_geometry_not_validated":True,
 "gas_saturation_2h_inventory_lower_bound_kg":2*M/hours
}
check("discrete mold minimum line count bracketed",
      (production["ideal_parallel_mold_count"]-1)*mold_rate<rate<=production["ideal_parallel_mold_count"]*mold_rate)
check("continuous roll minimum line count bracketed",
      (production["ideal_parallel_roll_count"]-1)*roller_rate<rate<=production["ideal_parallel_roll_count"]*roller_rate)
buoyancy=[]
for wet_fraction in (.01,.1,1):
    submerged_envelope=900*.55*wet_fraction
    net_up=9.80665*(1000-selected['envelope_density_kg_m3'])*submerged_envelope
    buoyancy.append({'submerged_fraction_of_reference_particle_volume':wet_fraction,
       'submerged_particle_envelope_m3':submerged_envelope,
       'net_upward_force_N_if_unrestrained':net_up,
       'air_filled_intact_skin_assumed':True,'not_an_anchor_design_load':True})
check('buoyancy balances displaced water minus particle weight',
      all(near(x['net_upward_force_N_if_unrestrained'],9.80665*(1000*x['submerged_particle_envelope_m3']-M*x['submerged_fraction_of_reference_particle_volume'])) for x in buoyancy))
cost=[]
baseM=900*.55*rho_f
for unit in (300,1000,3000):
    cost.append({"assumed_same_finished_body_JPY_kg":unit,"baseline_all_foam_mass_kg":baseM,
      "candidate_mass_kg":M,"candidate_body_cost_JPY":M*unit,
      "extra_body_cost_JPY":(M-baseM)*unit,"minimum_life_ratio_to_break_even_same_unit_cost":M/baseM,
      "coating_tooling_yield_and_installation_excluded":True,"vendor_quote":False})
check("cost break-even lifetime ratio gives equal annual body cost",
      all(near(x["candidate_body_cost_JPY"]/x["minimum_life_ratio_to_break_even_same_unit_cost"],baseM*x["assumed_same_finished_body_JPY_kg"]) for x in cost))
# End sealing consumes foamed material. Same cross-sectional area; density identity.
seal=[]
for t in (2,5,10):
    feed_one=t*rho_s/rho_f
    # Solid caps remain part of finished length; start stock length chosen for final 500 um.
    feed_length=500+2*(feed_one-t)
    seal.append({"final_length_um":500,"cap_thickness_um":t,
                 "foam_consumed_per_end_um":feed_one,"required_feed_length_um":feed_length,
                 "feed_length_premium":feed_length/500-1,
                 "thermal_process_and_permeability_unproven":True})
check("end-sealing mass is conserved including dense caps",
      all(near(rho_f*x["required_feed_length_um"],rho_f*(500-2*x["cap_thickness_um"])+rho_s*2*x["cap_thickness_um"]) for x in seal))
results={
 "cycle":53,"base_commit":"b4014e27c86096725c70cc09c0774c1ce394867c",
 "physical_tests":0,"success_probability":None,
 "source_audit":{"reported_void_fraction":porosity_reported,"void_from_reported_densities":porosity_from_density,
   "temperature_figure_points_C":[-50,-40,-20,0,23,40,80,120],
   "50C_sample_identified":False,"60C_sample_identified":False,
   "recovery_wait_conflict_hours":[24,72],
   "wrinkled_E_retention_not_used_due_text_figure_discrepancy":True},
 "cutting":{"D_for_80pct_cube_interior_um_at_one_cell_depth":D80,
  "500um_cube_affected_at_one19p6um_cell":1-cube_core(500,19.6),
  "500um_profile_two_end_affected_at_one19p6um_cell":1-profile_core(500,19.6),
  "50um_diameter_150um_long_branch_affected_at_one19p6um_cell":1-cylinder_core(50,150,19.6)},
 "selected_mass_candidate":selected,
 "production":production,
 "buoyancy":{"free_float_submerged_volume_fraction":selected["envelope_density_kg_m3"]/1000,"air_filled_intact_skin_assumed":True},
 "counts":{"source_rows":len(source),"cut_rows":len(cuts),"particle_rows":len(particles),
  "water_rows":len(water),"buoyancy_rows":len(buoyancy),"groom_rows":len(groom),"cost_rows":len(cost),"seal_rows":len(seal),
  "numerical_checks":len(checks)},
 "limitations":["geometric cut layers do not predict actual ruptured cells",
  "macro-scale foams, wrinkled foams and injection-molded foams are different materials and processes",
  "no transfer of rebound ratios or energy loss into ski friction",
  "mass candidate six-arm geometry differs from proposed continuous profile; no proven factory line",
  "J and packing are free state variables, not functions fitted to groomer pressure",
  "no 50 C wet/dry fatigue, toxicity or snow-equivalence proof"]
}
for f,rows in [("source-values.csv",source),("cutting.csv",cuts),("particles.csv",particles),
               ("water.csv",water),("buoyancy.csv",buoyancy),("grooming.csv",groom),("cost.csv",cost),("end-seal.csv",seal)]:
    csvout(f,rows)
js("results.json",results);js("numerical-checks.json",checks)
print(json.dumps(results,ensure_ascii=False,indent=2))
