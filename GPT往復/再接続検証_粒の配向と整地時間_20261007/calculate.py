"""Cycle 10: geometric connectivity and process scales; not physical tests.
Python 3.10+, numpy and scipy. Outputs results.json. No success probability."""
from pathlib import Path
import json, math, sys
H=Path(__file__).resolve().parent
root=H.parent.parent
if (root/".deps").exists(): sys.path.insert(0,str(root/".deps"))
import numpy as np
from scipy.integrate import quad
from numpy.polynomial.legendre import leggauss
I=json.loads((H/"inputs.json").read_text(encoding="utf-8"))
rng=np.random.default_rng(I["seed"])
G=I["ring"]
R=G["center_radius_um"]*1e-6
a=G["tube_radius_um"]*1e-6
g=I["grooming"]["g_m_s2"]

def normal_cap(angle_deg,N,rng):
    c=math.cos(math.radians(angle_deg))
    z=1-rng.random(N)*(1-c)
    phi=rng.random(N)*2*math.pi
    s=np.sqrt(np.maximum(0,1-z*z))
    return np.column_stack((s*np.cos(phi),s*np.sin(phi),z))

def orient_quadrature(angle_deg,order=80,nphi=256):
    if angle_deg==0: return 0.0
    x,w=leggauss(order)
    c=math.cos(math.radians(angle_deg))
    z=c+(x+1)*(1-c)/2
    wz=w/2 # normalized uniform z on cap
    phi=(np.arange(nphi)+.5)*2*math.pi/nphi
    dot=z[:,None,None]*z[None,:,None]+np.sqrt(1-z*z)[:,None,None]*np.sqrt(1-z*z)[None,:,None]*np.cos(phi)[None,None,:]
    return float(np.einsum("i,j,ij->",wz,wz,np.sqrt(np.maximum(0,1-dot*dot)).mean(axis=2)))

def link_xor(c,normal):
    # Ring A has radius 1, centre 0, normal z.
    # Intersect ring B with A's plane and test exactly one intersection inside A.
    nz=normal[2]
    q=math.sqrt(max(0,1-nz*nz))
    if q<1e-12: return np.zeros(len(c),dtype=bool)
    e1=(np.array([0.,0.,1.])-nz*normal)/q
    e2=np.cross(normal,e1)
    t=-c[:,2]/q
    valid=np.abs(t)<1
    t=np.clip(t,-1,1)
    s=np.sqrt(1-t*t)
    p=c+t[:,None]*e1
    plus=p+s[:,None]*e2
    minus=p-s[:,None]*e2
    in1=np.einsum("ij,ij->i",plus,plus)<1
    in2=np.einsum("ij,ij->i",minus,minus)<1
    return valid & np.logical_xor(in1,in2)

def link_formula(c,normal):
    # Independent expression: Kim et al. Eq. 5 for equal unit-radius circles.
    n1=np.array([0.,0.,1.])
    k=np.cross(n1,normal); k2=np.dot(k,k)
    if k2<1e-24: return np.zeros(len(c),dtype=bool)
    b=(c@normal/k2)[:,None]*(np.dot(n1,normal)*n1-normal)
    lhs=(1-np.einsum("ij,ij->i",b,b))*(c@k)**2
    rhs=k2*(np.einsum("ij,ij->i",c,c)/2+np.einsum("ij,ij->i",b,c))**2
    return lhs>rhs

def shape(height_um):
    h=height_um*1e-6
    m=G["wave_number"]
    lo=math.radians(G["opening_deg"])/2
    hi=2*math.pi-lo
    length=quad(lambda p: math.sqrt(R*R+(m*h*math.sin(m*p))**2),lo,hi,epsabs=1e-14)[0]
    volume=math.pi*a*a*length+4*math.pi*a**3/3
    mass=volume*G["material_density_kg_m3"]
    p=np.linspace(lo,hi,20001)
    dr=np.column_stack((-R*np.sin(p),R*np.cos(p),-m*h*np.sin(m*p)))
    ddr=np.column_stack((-R*np.cos(p),-R*np.sin(p),-m*m*h*np.cos(m*p)))
    kappa=np.linalg.norm(np.cross(dr,ddr),axis=1)/np.linalg.norm(dr,axis=1)**3
    return {"height_um":height_um,"centreline_length_mm":length*1000,"solid_volume_mm3":volume*1e9,
            "particle_mass_kg":mass,"bulk_density_fixed_count_kg_m3":mass*G["number_density_m3"],
            "tube_times_max_curvature":float(a*np.max(kappa)),
            "scope":"Swept circular tube plus hemispherical tips; local curvature check, not deformation or global capture."}

def water_force():
    w=I["wet"]; tau=1-(w["T_C"]+273.15)/647.096
    gamma=.2358*tau**1.256*(1-.625*tau)
    return 2*math.pi*gamma*w["bridge_radius_um"]*1e-6*(1-.3823*w["bridge_V_R3"]**.2586)

def run():
    O=I["orientation"]; n=G["number_density_m3"]
    forms=[shape(h) for h in G["wave_heights_um"]]
    iso=math.pi/4
    orient=[]
    for angle in O["cap_angles_deg"]:
        avg=orient_quadrature(angle,O["quadrature_order"],O["azimuth_count"])
        normals1=normal_cap(angle,O["MC_pairs"],rng)
        normals2=normal_cap(angle,O["MC_pairs"],rng)
        samples=np.sqrt(np.maximum(0,1-np.sum(normals1*normals2,axis=1)**2))
        if angle==0: samples[:]=0
        vex=32/3*R**3*avg
        v_iso=math.pi/3*(2*R)**3
        # Isotropic eta=2.11 is NOT an anisotropic or physical percolation threshold.
        orient.append({"cap_deg":angle,"mean_sin_gamma":avg,"relative_link_volume":avg/iso,
                       "v_link_m3":vex,"ideal_mean_links_at_fixed_n":n*vex,
                       "MC_mean":float(samples.mean()),"MC_SE":float(samples.std(ddof=1)/math.sqrt(len(samples))),
                       "density_multiplier_to_recover_isotropic_mean":iso/avg if avg else None,
                       "R0_density_to_recover_isotropic_mean_kg_m3":forms[0]["bulk_density_fixed_count_kg_m3"]*iso/avg if avg else None,
                       "scope":"Geometry-only independent-centre model; not capture probability, physical packing or success."})
    spatial=[]
    for angle in O["fixed_relative_angles_deg"]:
        th=math.radians(angle); normal=np.array([math.sin(th),0.,math.cos(th)])
        centres=rng.uniform(-2,2,(O["geometric_volume_MC_samples"],3))
        linked=link_xor(centres,normal)
        independent=link_formula(centres,normal)
        p=float(linked.mean())
        spatial.append({"angle_deg":angle,"analytic_volume_over_R3":32/3*math.sin(th),
                        "MC_volume_over_R3":64*p,
                        "MC_SE_over_R3":64*math.sqrt(p*(1-p)/len(linked)),
                        "criterion_mismatches":int(np.count_nonzero(linked!=independent))})
    ref=I["reference_vibration"]; machine=I["grooming"]
    lam=2*R/ref["D_m"]
    freq=ref["frequency_Hz"]/math.sqrt(lam)
    amp=ref["amplitude_m"]*lam
    gamma=amp*(2*math.pi*freq)**2/g
    time=[{"reference_s":t,"gravity_similarity_only_s":t*math.sqrt(lam),
           "active_length_at_0_6m_s_m":machine["operating_speed_m_s"]*t*math.sqrt(lam)}
          for t in ref["reference_durations_s"]]
    residence=[]
    for length in machine["active_lengths_m"]:
        for t in time:
            maxv=length/t["gravity_similarity_only_s"]
            residence.append({"active_length_m":length,"reference_s":t["reference_s"],
                              "assumed_dwell_s":t["gravity_similarity_only_s"],
                              "speed_limited_by_dwell_m_s":maxv,
                              "course_minutes_if_dwell_controls":machine["course_length_m"]/(maxv*machine["utilization"])/60+machine["other_minutes"],
                              "scope":"Hypothetical dwell constraint; literature time has not been validated for artificial grains."})
    throughput=[]
    available=(machine["closure_minutes"]-machine["other_minutes"])*60
    for area in [machine["pilot_area_m2"],machine["course_length_m"]*machine["course_width_m"]]:
        for depth in machine["depths_m"]:
            throughput.append({"area_m2":area,"depth_m":depth,"volume_m3":area*depth,
                               "net_required_m3_s":area*depth/available,
                               "net_R0_mass_kg_s":area*depth/available*forms[0]["bulk_density_fixed_count_kg_m3"]})
    bypass=[]
    for fraction in machine["repair_area_fractions"]:
        for depth in [.30,.45]:
            for dwell in machine["unvalidated_conditioning_times_s"]:
                rate=machine["course_length_m"]*machine["course_width_m"]*fraction*depth/available
                cell=rate*dwell
                bypass.append({"damaged_area_fraction_assumed":fraction,"depth_m":depth,"conditioning_time_assumed_s":dwell,"net_rate_m3_s":rate,"one_cell_m3":cell,"three_cells_m3":3*cell,"three_cells_material_kg_R0":3*cell*forms[0]["bulk_density_fixed_count_kg_m3"],"scope":"Three equal cells: fill, condition, discharge in separate phases. Ideal valves/no dead time; peak collection and uneven damage not modelled."})
    wet=[]
    fcap=water_force()
    for s in forms:
        weight=s["particle_mass_kg"]*g
        wet.append({"wave_height_um":s["height_um"],"illustrative_capillary_force_uN":fcap*1e6,
                    "particle_weight_uN":weight*1e6,"capillary_to_weight":fcap/weight,
                    "gravity_scaled_inertial_force_uN":gamma*weight*1e6,
                    "capillary_to_scaled_inertia":fcap/(gamma*weight),
                    "scope":"Force scales only, not a wet-bed detachment threshold or PE contact-angle prediction."})
    c=I["cost"]; crf=c["discount"]*(1+c["discount"])**c["years"]/((1+c["discount"])**c["years"]-1)
    budget=(c["annual_budget_JPY"]-c["initial_other_JPY"]*crf-c["annual_other_JPY"])/(crf+c["replacement"])
    costs=[]
    for s in forms:
        mass=s["bulk_density_fixed_count_kg_m3"]*c["area_m2"]*c["depth_m"]
        cost=mass*c["assumed_price_JPY_kg"]
        costs.append({"wave_height_um":s["height_um"],"pilot_mass_kg":mass,"assumed_purchase_JPY":cost,
                      "annual_equivalent_JPY":c["initial_other_JPY"]*crf+c["annual_other_JPY"]+(crf+c["replacement"])*cost,
                      "finished_price_ceiling_JPY_kg":budget/mass,"extra_purchase_budget_JPY":budget-cost})
    N=n*c["area_m2"]*c["depth_m"]
    production=[]
    for yield_fraction in c["process_yield"]:
        for strands in c["parallel_strands"]:
            accepted=N/(c["working_hours"]*3600)
            gross=accepted/yield_fraction
            cuts=gross/strands
            production.append({"yield_assumption":yield_fraction,"parallel_lanes":strands,
                               "accepted_particles_s":accepted,"gross_particles_s":gross,
                               "cut_events_per_lane_s":cuts,
                               "feed_m_s_if_60um_pitch":cuts*c["pitch_mm"]/1000,
                               "scope":"Throughput target for process comparison, not a demonstrated cutter or extrusion rate."})
    return {"metadata":{"date":I["date"],"reference_commit":I["source_commit"],"physical_test_count":0,"physical_success_probability":None},
            "geometries":forms,"orientation":orient,"link_volume_validation":spatial,
            "vibration":{"scale_ratio":lam,"gravity_scaled_frequency_Hz":freq,"gravity_scaled_amplitude_um":amp*1e6,"Gamma":gamma,
                         "time_comparisons":time,"reference_tube_over_D":ref["tube_diameter_m"]/ref["D_m"],
                         "candidate_tube_over_D":2*a/(2*R),
                         "candidate_E_over_rho_g_D":G["assumed_E_Pa"]/(G["material_density_kg_m3"]*g*2*R),
                         "reference_E_over_rho_g_D":ref["assumed_E_Pa"]/(ref["density_kg_m3"]*g*ref["D_m"]),
                         "routine_total_minutes":machine["course_length_m"]/(machine["operating_speed_m_s"]*machine["utilization"])/60+machine["other_minutes"],
                         "actual_dwell_0_4m_at_nominal_s":.4/machine["operating_speed_m_s"]},
            "residence":residence,"throughput":throughput,"selective_reconditioning":bypass,"wet_force_scales":wet,"cost":costs,"production":production}

def checks(out):
    done=[]
    def ck(name,cond):
        assert cond,name
        done.append({"name":name,"passed":True,"scope":"Numerical consistency only"})
    ck("isotropic_hemisphere_equals_full_unoriented_ring_average",abs(out["orientation"][-1]["mean_sin_gamma"]-math.pi/4)<2e-5)
    ck("parallel_ring_link_volume_zero",out["orientation"][0]["v_link_m3"]==0)
    ck("quadrature_matches_independent_MC",all(abs(x["mean_sin_gamma"]-x["MC_mean"])<6*x["MC_SE"]+2e-6 for x in out["orientation"]))
    ck("spatial_MC_matches_analytic_link_volume",all(abs(x["MC_volume_over_R3"]-x["analytic_volume_over_R3"])<6*x["MC_SE_over_R3"] for x in out["link_volume_validation"]))
    ck("two_independent_link_criteria_agree",all(x["criterion_mismatches"]==0 for x in out["link_volume_validation"]))
    ck("flat_tube_volume",math.isclose(out["geometries"][0]["solid_volume_mm3"]*1e-9,math.pi*a*a*R*(2*math.pi-math.radians(G["opening_deg"]))+4*math.pi*a**3/3,rel_tol=1e-12))
    ck("wavy_lengths_increase",all(x["centreline_length_mm"]<y["centreline_length_mm"] for x,y in zip(out["geometries"],out["geometries"][1:])))
    ck("local_tube_curvature_regular",all(x["tube_times_max_curvature"]<1 for x in out["geometries"]))
    ref=I["reference_vibration"]; expected=ref["amplitude_m"]*(2*math.pi*ref["frequency_Hz"])**2/g
    ck("gravity_similarity_preserves_Gamma",math.isclose(out["vibration"]["Gamma"],expected,rel_tol=1e-12))
    ck("gravity_similarity_preserves_cycles",all(math.isclose(t["gravity_similarity_only_s"]*out["vibration"]["gravity_scaled_frequency_Hz"],t["reference_s"]*ref["frequency_Hz"],rel_tol=1e-12) for t in out["vibration"]["time_comparisons"]))
    c=I["cost"];n=G["number_density_m3"]
    ck("production_yield_mass_count_balance",all(math.isclose(x["gross_particles_s"]*x["yield_assumption"]*c["working_hours"]*3600,n*c["area_m2"]*c["depth_m"],rel_tol=1e-12) for x in out["production"]))
    ck("no_physical_probability",out["metadata"]["physical_success_probability"] is None and out["metadata"]["physical_test_count"]==0)
    return done

if __name__=="__main__":
    out=run();out["checks"]=checks(out)
    (H/"results.json").write_text(json.dumps(out,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({"checks":len(out["checks"]),"orientation":out["orientation"],
                      "geometries":out["geometries"],"vibration":out["vibration"]},ensure_ascii=False,indent=2))
