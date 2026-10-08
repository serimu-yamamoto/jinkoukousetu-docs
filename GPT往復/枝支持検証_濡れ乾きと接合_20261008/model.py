"""Cycle 18: bounded diagnostics, not a calibrated grain or snow simulation."""
import json, math
from pathlib import Path
HERE = Path(__file__).resolve().parent
P = json.loads((HERE/"inputs.json").read_text(encoding="utf-8"))
def gamma_water(c):
    tau = 1-(c+273.15)/647.096
    return .2358*tau**1.256*(1-.625*tau)
def beta(kind, alpha=1):
    return {"cantilever_tip":3, "pin_pin_mid":48,
            "spring_spring_mid":192*(alpha+1)/(alpha+4),
            "fixed_fixed_mid":192}[kind]
def case(d_um,L_um,E_MPa,mult,kind,gap_um=None):
    if gap_um is None: gap_um=P["gap_um"]
    d,L,E,gap=d_um*1e-6,L_um*1e-6,E_MPa*1e6,gap_um*1e-6
    I=math.pi*d**4/64
    F=mult*math.pi*gamma_water(P["water_temperature_C"])*d
    b=beta(kind)
    k=b*E*I/L**3
    delta=F/k
    Lcrit=(b*E*I*gap/(2*F))**(1/3)
    return dict(d_um=d_um,L_um=L_um,E_MPa=E_MPa,
        force_multiplier=mult,support=kind,gap_um=gap_um,
        assumed_force_N=F,stiffness_N_m=k,one_beam_delta_um=delta*1e6,
        relative_gap_closure_index=2*delta/gap,
        crossover_length_um=Lcrit*1e6,
        delta_over_L=delta/L,L_over_d=L/d,
        linear_diagnostic_scope=(delta/L<=.1 and L/d>=10),
        before_pair_contact=(2*delta<gap),
        note="Closure index is a linear diagnostic, not predicted collapse or pass/fail.")
def linear_solve(a,b):
    a=[row[:]+[v] for row,v in zip(a,b)]
    n=len(b)
    for i in range(n):
        j=max(range(i,n),key=lambda j:abs(a[j][i]))
        if abs(a[j][i])<1e-15: raise ValueError("singular")
        a[i],a[j]=a[j],a[i]
        p=a[i][i]
        a[i]=[x/p for x in a[i]]
        for j in range(n):
            if j==i:continue
            f=a[j][i]
            a[j]=[x-f*y for x,y in zip(a[j],a[i])]
    return [row[-1] for row in a]
def beam_fe(kind,alpha=1,n=8,ks=None):
    # Nondimensional L=EI=F=1. Independent Hermite element assembly.
    h=1/n
    e=[[12/h**3,6/h**2,-12/h**3,6/h**2],
       [6/h**2,4/h,-6/h**2,2/h],
       [-12/h**3,-6/h**2,12/h**3,-6/h**2],
       [6/h**2,2/h,-6/h**2,4/h]]
    N=2*(n+1);K=[[0.]*N for _ in range(N)];f=[0.]*N
    for j in range(n):
        ix=[2*j,2*j+1,2*j+2,2*j+3]
        for a in range(4):
            for b in range(4): K[ix[a]][ix[b]]+=e[a][b]
    if kind=="cantilever_tip":fixed={0,1};target=2*n
    else:
        fixed={0,2*n};target=n
        if kind=="fixed_fixed_mid":fixed|={1,2*n+1}
        if kind=="spring_spring_mid":
            # alpha = kr L/(2 EI)
            K[1][1]+=2*alpha;K[2*n+1][2*n+1]+=2*alpha
    if ks is not None:
        if kind=="cantilever_tip": raise ValueError("Only symmetric middle load")
        fixed-={0,2*n}
        K[0][0]+=ks;K[2*n][2*n]+=ks
    f[target]=1
    free=[i for i in range(N) if i not in fixed]
    u=linear_solve([[K[i][j] for j in free] for i in free],[f[i] for i in free])
    full=[0.]*N
    for i,v in zip(free,u):full[i]=v
    reaction=[sum(K[i][j]*full[j] for j in range(N))-f[i] for i in range(N)]
    return full[target],(sum(reaction[i] for i in fixed if i%2==0) if ks is None else -ks*(full[0]+full[2*n]))
def run():
    checks=[]
    for kind in P["support_cases"]:
        for n in (4,8,16):
            val,reaction=beam_fe(kind,n=n)
            assert math.isclose(val,1/beta(kind),rel_tol=1e-9)
            assert math.isclose(reaction,-1,abs_tol=1e-9)
            checks.append({"check":"FE compliance and vertical reaction","support":kind,"elements":n,
                           "deflection":val,"relative_error":abs(val*beta(kind)-1)})
    for alpha in (0,.1,1,10,100):
        val,_=beam_fe("spring_spring_mid",alpha)
        assert math.isclose(val,1/beta("spring_spring_mid",alpha),rel_tol=1e-9)
        checks.append({"check":"finite rotational restraint","alpha":alpha,"compliance":val})
    for ks_ratio in (.1,1,5,10):
        ks=ks_ratio*48
        value,reaction=beam_fe("pin_pin_mid",ks=ks)
        assert math.isclose(value,1/48+1/(2*ks),rel_tol=1e-9)
        assert math.isclose(reaction,-1,abs_tol=1e-9)
        checks.append({"check":"moving supports FE","ks_over_beam_k":ks_ratio,"compliance":value})
    # Published IAPWS calculated table values, mN/m, rounded to 2 decimals.
    for T,value in ((0.01,75.65),(20,72.74),(50,67.94),(100,58.91)):
        got=gamma_water(T)*1000
        assert abs(got-value)<.01
        checks.append({"check":"IAPWS table rounded","T_C":T,"calculated_mN_m":got})
    rows=[case(d,L,E,m,k) for d in P["diameters_um"] for L in P["spans_um"]
          for E in P["moduli_MPa"] for m in P["force_multipliers"]
          for k in P["support_cases"]]
    # Scaling identities are algebraic checks, not new experiments.
    a=case(2,100,300,1,"cantilever_tip")
    b=case(2,50,300,1,"cantilever_tip")
    c=case(4,100,300,1,"cantilever_tip")
    assert math.isclose(a["relative_gap_closure_index"]/b["relative_gap_closure_index"],8)
    assert math.isclose(a["relative_gap_closure_index"]/c["relative_gap_closure_index"],8)
    checks.append({"check":"L cubed and d inverse cubed scaling"})
    creep=[]
    for a in P["creep"]["a"]:
        for tau in P["creep"]["tau_s"]:
            for t in P["creep"]["t_s"]:
                factor=1+a*(-math.expm1(-t/tau))
                creep.append(dict(a=a,tau_s=tau,t_s=t,compliance_multiplier=factor,
                                  crossover_length_ratio=factor**(-1/3)))
    support_motion=[]
    nominal_branch=case(2,20,300,1,"pin_pin_mid")
    for ratio in (.1,1,5,10):
        support_motion.append(dict(each_support_k_over_beam_k=ratio,each_support_k_N_m=ratio*nominal_branch["stiffness_N_m"],total_deflection_multiplier=1+1/(2*ratio),relative_gap_closure_index=nominal_branch["relative_gap_closure_index"]*(1+1/(2*ratio))))
    q=P["operation"];b=P["budget"]
    volume=q["area_m2"]*q["depth_m"];mass=volume*q["bulk_density_kg_m3"]
    eps=1-q["bulk_density_kg_m3"]/P["solid_density_kg_m3"]
    water=[]
    for s in P["pore_water_saturations"]:
        water_kg=volume*eps*s*P["water_density_kg_m3"]
        water.append(dict(pore_saturation=s,water_kg=water_kg,
             total_bulk_density_kg_m3=(mass+water_kg)/volume,water_to_dry_mass_ratio=water_kg/mass))
        assert math.isclose(water_kg/P["water_density_kg_m3"]+volume*eps*(1-s)+mass/P["solid_density_kg_m3"],volume)
    checks.append({"check":"solid plus water plus gas volume conservation"})
    capillary=[]
    for r_um in P["pore_radii_um"]:
        for angle in P["contact_angles_deg"]:
            pressure=2*gamma_water(50)*math.cos(math.radians(angle))/(r_um*1e-6)
            capillary.append(dict(cylindrical_pore_radius_um=r_um,contact_angle_deg=angle,
                     pressure_Pa=pressure,ideal_vertical_head_m=pressure/(P["water_density_kg_m3"]*9.81)))
    crf=b["discount"]/(1-(1+b["discount"])**(-b["years"]))
    crf_direct=1/sum((1+b["discount"])**(-t) for t in range(1,b["years"]+1))
    assert math.isclose(crf,crf_direct)
    checks.append({"check":"capital recovery from discounted annual sum"})
    baseline=(b["nonmaterial_capital_JPY"]+mass*b["material_JPY_kg"])*crf+b["annual_fixed_JPY"]+mass*b["material_JPY_kg"]*b["annual_material_replacement_fraction"]
    costs=[]
    for x in P["added_mass_fractions"]:
        newmass=mass*(1+x)
        extra=mass*x*b["material_JPY_kg"]*(crf+b["annual_material_replacement_fraction"])
        head=b["annual_budget_JPY"]-baseline-extra
        costs.append(dict(added_mass_fraction=x,total_dry_mass_kg=newmass,
          extra_annual_material_JPY=extra,remaining_annual_JPY=head,
          max_initial_finished_price_uplift_JPY_kg=head/(newmass*(crf+b["annual_material_replacement_fraction"])),
          reform_fees=[dict(fraction=f,all_in_ceiling_JPY_kg=head/(newmass*f*q["closures_per_year"])) for f in q["reform_fractions"]],
          note="Price uplift and reform fees are alternative uses of the SAME headroom, not additive entitlements."))
    nominal=[case(d,L,300,1,k) for d,L in ((2,100),(2,20),(10,100),(30,250)) for k in P["support_cases"]]
    output=dict(physical_tests=0,physical_success_probability=None,
      water_surface_tension_N_m={str(T):gamma_water(T) for T in (30,40,50)},
      formula_scope="Prescribed transverse force, isolated linear circular beam, ideal supports. No actual meniscus, entanglement, viscoelastic material, ski, or grain-bed prediction.",
      grid_count=len(rows),grid=rows,nominal=nominal,creep_sensitivity=creep,
      symmetric_support_motion=support_motion,
      porosity_assuming_all_voids_accessible=eps,water_inventory=water,
      cylindrical_capillary_scale=capillary,
      baseline_annual_JPY=baseline,CRF=crf,cost_sensitivity=costs)
    (HERE/"results.json").write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (HERE/"verification.json").write_text(json.dumps(dict(scope="Internal numerical and formula checks only",physical_tests=0,checks=checks),indent=2)+"\n",encoding="utf-8")
    print(json.dumps(dict(grid_count=len(rows),check_groups=len(checks),gamma50=gamma_water(50),nominal=nominal[:4],cost=costs),ensure_ascii=False))
if __name__=="__main__":run()
