"""Cycle 42: prescribed wear shapes, contact response, phase load and recovery cost.
No shape is claimed to be the solution of a local wear evolution equation.
All material/operating inputs are uncalibrated unless explicitly source-labelled.
"""
from pathlib import Path
import sys, json, csv, math, platform
ROOT = Path(__file__).resolve().parent
deps = ROOT.parent.parent / ".deps"
if deps.is_dir():
    sys.path.insert(0, str(deps))
import numpy as np
import scipy
from scipy.integrate import quad
from scipy.optimize import brentq
from scipy.special import dawsn
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

I = json.loads((ROOT / "inputs.json").read_text(encoding="utf-8"))
C = I["contact"]
A0 = C["initial_radius_m"]
P0 = C["initial_mean_pressure_Pa"]
E = C["effective_modulus_Pa"]
F0 = math.pi * A0**2 * P0
R0 = 4 * E * A0**3 / (3 * F0)
D0 = A0**2 / R0
checks = []
def check(name, ok, detail=None):
    checks.append({"name":name,"passed":bool(ok),"detail":detail})
    if not ok:
        raise AssertionError(name + ": " + str(detail))
def close(x,y,tol=1e-8):
    return abs(x-y) <= tol * max(abs(x),abs(y),1e-20)
def J(z):
    if z < 1e-4:
        return 1 - 2*z/3 + 4*z*z/15 - 8*z**3/105 + 16*z**4/945
    return dawsn(math.sqrt(z))/math.sqrt(z)
def g(x,w):
    if w == 0:
        return x*x
    z=x*x/(2*w)
    s=(2*z/3-4*z*z/15+8*z**3/105-16*z**4/945) if z<1e-4 else 1-J(z)
    return x*x*s
def gp_over_x(x,w):
    if w==0:
        return 2.0
    z=x*x/(2*w)
    if z<1e-4:
        return 8*z/3-8*z*z/5+64*z**3/105-32*z**4/189
    return 1+(2*z-1)*J(z)
def g_direct(x,w):
    if w==0:
        return x*x
    z=x*x/(2*w)
    return x*x*quad(lambda t:math.sin(t)*(-math.expm1(-z*math.sin(t)**2)),0,math.pi/2,epsabs=1e-12)[0]
def smooth_force(a,w):
    return 1.5*(a*g(a,w)-quad(lambda x:g(x,w),0,a,epsabs=1e-12,epsrel=1e-11)[0])
def solve_shape(kind,w):
    if w==0:
        return {"a_rel":1.0,"indentation_rel":1.0,"flat_radius_rel":0.0}
    if kind=="flat_truncation":
        b=math.sqrt(2*w)
        s=brentq(lambda s:s**3+1.5*b*b*s-1,0,1,xtol=1e-14)
        a=math.hypot(s,b)
        return {"a_rel":a,"indentation_rel":a*s,"flat_radius_rel":b}
    high=max(2,4*math.sqrt(w))
    while smooth_force(high,w)<1:
        high*=2
    a=brentq(lambda a:smooth_force(a,w)-1,1,high,xtol=1e-12)
    return {"a_rel":a,"indentation_rel":g(a,w),"flat_radius_rel":0.0}
def pressure_rel(r,a,w,n=64):
    # Relative to original mean pressure, substitution x=sqrt(r^2+t^2).
    tmax=math.sqrt(max(0,a*a-r*r))
    if tmax==0:
        return 0.0
    nodes, weights = np.polynomial.legendre.leggauss(n)
    ts=tmax*(nodes+1)/2
    vals=np.array([gp_over_x(math.hypot(r,float(t)),w) for t in ts])
    return 0.75*tmax/2*float(weights @ vals)
def state(m,kw,kind,distance=None):
    distance=C["sole_length_m"]*C["local_passes"] if distance is None else distance
    a0=A0/math.sqrt(m); r0=R0/math.sqrt(m); f=F0/m; d0=a0*a0/r0
    volume=kw*f*distance*1e-9  # mm^3 -> m^3, kw already dimensional specific wear
    factor=math.pi if kind=="flat_truncation" else 2*math.pi
    w=math.sqrt(volume/(factor*r0)) if volume else 0
    s=solve_shape(kind,w/d0)
    area_rel=s["a_rel"]**2
    mu=C["interface_beta"]+C["interface_tau0_Pa"]*area_rel/P0
    return {"split_count":m,"specific_wear_mm3_Nm":kw,"profile":kind,"sliding_distance_m":distance,
        "force_per_contact_N":f,"initial_contact_radius_um":a0*1e6,
        "curvature_radius_um":r0*1e6,"removed_volume_per_contact_m3":volume,
        "total_removed_volume_m3":volume*m,"apex_removed_um":w*1e6,
        "apex_removed_over_initial_indentation":w/d0,"contact_radius_um":a0*s["a_rel"]*1e6,
        "area_ratio":area_rel,"mean_pressure_MPa":P0/area_rel/1e6,
        "interface_mu":mu,"normal_contact_stiffness_ratio":s["a_rel"],
        "elastic_indentation_um":d0*s["indentation_rel"]*1e6,
        "power_per_400N_ski_W":mu*400*C["relative_speed_m_s"],
        "finite_peak_pressure_MPa":None,"peak_radius_over_contact_radius":None,
        "peak_pressure_status":"sharp_rim_singularity" if volume and kind=="flat_truncation" else "finite",
        "w_dimensionless":w/d0,"a_dimensionless":s["a_rel"]}

rows=[]
for m in C["split_counts"]:
    for kw in C["specific_wear_mm3_Nm"]:
        for kind in ["flat_truncation","smooth_gaussian_removal"]:
            r=state(m,kw,kind)
            if r["peak_pressure_status"]=="finite":
                grid=np.linspace(0,r["a_dimensionless"],501)
                vals=np.array([pressure_rel(float(x),r["a_dimensionless"],r["w_dimensionless"]) for x in grid])
                j=int(np.argmax(vals))
                r["finite_peak_pressure_MPa"]=float(vals[j])*P0/1e6
                r["peak_radius_over_contact_radius"]=float(grid[j]/r["a_dimensionless"])
            rows.append(r)

threshold=[]
for m in C["split_counts"]:
    for kind in ["flat_truncation","smooth_gaussian_removal"]:
        for inc in C["friction_increments"]:
            mu0=C["interface_beta"]+C["interface_tau0_Pa"]/P0
            kw=brentq(lambda logk:state(m,10**logk,kind)["interface_mu"]-mu0-inc,-15,-3,xtol=1e-12)
            r=state(m,10**kw,kind)
            threshold.append({"split_count":m,"profile":kind,"diagnostic_mu_increment":inc,
                "threshold_mu":mu0+inc,"max_specific_wear_at_100_local_passes_mm3_Nm":10**kw,
                "apex_removed_um":r["apex_removed_um"],"total_removed_volume_m3":r["total_removed_volume_m3"],
                "note":"Diagnostic friction drift only, not a snow acceptance or material life."})

mix=[]
for phi in I["heterogeneous"]["wear_resistant_area_fractions"]:
    for ratio in I["heterogeneous"]["wear_ratio_fast_over_slow"]:
        # k_slow=1, k_fast=ratio; equal recession requires k_i*p_i = const.
        den=phi+(1-phi)/ratio
        p_slow=1/den; p_fast=p_slow/ratio
        mix.append({"slow_area_fraction":phi,"k_fast_over_k_slow":ratio,
            "slow_phase_load_fraction":phi*p_slow,"p_slow_over_mean":p_slow,
            "p_fast_over_mean":p_fast,"k_effective_over_k_slow":1/den,
            "k_effective_over_k_fast":1/(ratio*den)})
redist=[]
for sectors in I["redistribution"]["sectors"]:
    for chi in I["redistribution"]["direction_wear_multipliers"]:
        r=state(1,I["redistribution"]["baseline_specific_wear_mm3_Nm"]*chi/sectors,"smooth_gaussian_removal")
        redist.append({"sectors_with_equal_exposure":sectors,"unknown_direction_wear_multiplier":chi,
            "dose_ratio_per_sector":chi/sectors,"mu":r["interface_mu"],
            "total_wear_volume_ratio_all_sectors":chi,
            "interpretation":"exposure redistribution, not restoration or measured lifetime"})

cost=[]
ci=I["cost"]
af=(1-(1+ci["discount_rate"])**(-ci["years"]))/ci["discount_rate"]
annual_before=ci["bed_mass_kg"]*ci["complete_particle_JPY_kg"]*(1/af+ci["baseline_annual_new_fraction"])
annual_after=ci["bed_mass_kg"]*ci["complete_particle_JPY_kg"]*(1/af+ci["new_annual_new_fraction"])
savings=ci["bed_mass_kg"]*ci["complete_particle_JPY_kg"]*(ci["baseline_annual_new_fraction"]-ci["new_annual_new_fraction"])
for depth in ci["processed_depths_m"]:
    mass=ci["bed_mass_kg"]*depth/ci["bed_depth_m"]
    annual=mass*ci["maintenance_cycles_per_year"]
    cost.append({"processed_depth_m":depth,"processed_mass_per_operation_kg":mass,
        "processed_mass_per_year_kg":annual,"assumed_gross_savings_JPY_year":savings,
        "max_added_cost_JPY_processed_kg":savings/annual,
        "annual_material_cost_before_JPY":annual_before,"annual_material_cost_after_JPY":annual_after,
        "illustrative_material_budget_JPY_year":ci["illustrative_material_budget_JPY_year"],
        "note":"No improved replacement rate demonstrated; excludes extra capital and other costs."})

check("Hertz load and input mean pressure",close(4*E*A0**3/(3*R0),F0))
check("Unworn contact and friction",all(close(x["area_ratio"],1) and close(x["interface_mu"],.05) for x in rows if x["specific_wear_mm3_Nm"]==0))
check("MDR transform independent angle integral",all(close(g(x,w),g_direct(x,w),2e-8) for x in [.01,.1,.5,1,3] for w in [.001,.1,1,10]))
check("MDR derivative finite difference",all(close(gp_over_x(x,w),(g(x+1e-5,w)-g(x-1e-5,w))/(2e-5*x),1e-5) for x in [.1,.5,1,3] for w in [.01,.1,1]))
check("Smooth force roots",all(close(smooth_force(x["a_dimensionless"],x["w_dimensionless"]),1,1e-8) for x in rows if x["profile"]=="smooth_gaussian_removal"))
check("Flat force independent MDR integral",all(close(1.5*(a*a*math.sqrt(a*a-b*b)-quad(lambda t:t*math.sqrt(max(0,t*t-b*b)),b,a,epsabs=1e-11)[0]),1,1e-7) for x in rows if x["profile"]=="flat_truncation" for a,b in [(x["a_dimensionless"],math.sqrt(2*x["w_dimensionless"]))]))
# Independent volume integration in dimensionless radii r/sqrt(R*w).
check("Flat removed volume",close(2*math.pi*quad(lambda r:r*(1-r*r/2),0,math.sqrt(2))[0],math.pi))
check("Smooth removed volume",close(2*math.pi*quad(lambda r:r*math.exp(-r*r/2),0,np.inf)[0],2*math.pi))
check("Equal volume between morphology alternatives",all(close(state(m,k,"flat_truncation")["total_removed_volume_m3"],state(m,k,"smooth_gaussian_removal")["total_removed_volume_m3"]) for m in C["split_counts"] for k in C["specific_wear_mm3_Nm"]))
check("Total removed volume invariant under splitting",all(close(state(m,k,"flat_truncation")["total_removed_volume_m3"],k*F0*160*1e-9) for m in C["split_counts"] for k in C["specific_wear_mm3_Nm"]))
conv=[]
for w in [0,.01,.1,1,3]:
    a=solve_shape("smooth_gaussian_removal",w)["a_rel"]
    for r in [0,.25*a,.75*a,.99*a]:
        p64=pressure_rel(r,a,w,64);p128=pressure_rel(r,a,w,128)
        conv.append({"w":w,"radius_over_contact":r/a,"p64_over_p0":p64,"p128_over_p0":p128,"difference":abs(p64-p128)})
check("Pressure quadrature convergence",max(x["difference"] for x in conv)<1e-8)
check("Hertz pressure profile",all(close(pressure_rel(r,1,0),1.5*math.sqrt(1-r*r)) for r in [0,.2,.7,.99]))
check("Pressure integrates to imposed normal load",all(close(2*quad(lambda r:pressure_rel(r,solve_shape("smooth_gaussian_removal",w)["a_rel"],w)*r,0,solve_shape("smooth_gaussian_removal",w)["a_rel"],epsabs=1e-8)[0],1,1e-6) for w in [0,.1,1,3]))
check("Incremental stiffness is 2 E a",all(close((smooth_force(a+1e-5,w)-smooth_force(a-1e-5,w))/(g(a+1e-5,w)-g(a-1e-5,w)),1.5*a,1e-5) for w in [.01,.1,1] for a in [solve_shape("smooth_gaussian_removal",w)["a_rel"]]))
check("Area and friction grow with prescribed wear",all(all(x2["area_ratio"]>=x1["area_ratio"] for x1,x2 in zip(rr,rr[1:])) for m in C["split_counts"] for kind in ["flat_truncation","smooth_gaussian_removal"] for rr in [[x for x in rows if x["split_count"]==m and x["profile"]==kind]]))
check("Friction is shear force over load",all(close(x["interface_mu"],C["interface_beta"]+C["interface_tau0_Pa"]/(x["mean_pressure_MPa"]*1e6)) for x in rows))
check("Friction thresholds roots",all(close(state(x["split_count"],x["max_specific_wear_at_100_local_passes_mm3_Nm"],x["profile"])["interface_mu"],x["threshold_mu"],1e-8) for x in threshold))
check("Phase load equilibrium",all(close(x["slow_area_fraction"]*x["p_slow_over_mean"]+(1-x["slow_area_fraction"])*x["p_fast_over_mean"],1) for x in mix))
check("Equal phase recession",all(close(x["p_slow_over_mean"],x["k_fast_over_k_slow"]*x["p_fast_over_mean"]) for x in mix))
check("Homogeneous material limit",all(close(x["slow_phase_load_fraction"],x["slow_area_fraction"]) for x in mix if x["k_fast_over_k_slow"]==1))
check("Harmonic effective wear coefficient",all(close(x["k_effective_over_k_fast"],1/(x["slow_area_fraction"]*x["k_fast_over_k_slow"]+1-x["slow_area_fraction"])) for x in mix))
check("Reorientation can lose all dose benefit",all(close(x["dose_ratio_per_sector"],1) for x in redist if x["sectors_with_equal_exposure"]==x["unknown_direction_wear_multiplier"]))
check("Processing mass and money balance",all(close(x["max_added_cost_JPY_processed_kg"]*x["processed_mass_per_year_kg"],savings) for x in cost))
check("Specific wear unit conversion",close(1e-7*F0*160*1e-9,state(1,1e-7,"flat_truncation")["removed_volume_per_contact_m3"]))

def write_csv(name,data):
    with (ROOT/name).open("w",encoding="utf-8",newline="") as fh:
        writer=csv.DictWriter(fh,fieldnames=list(data[0]),lineterminator="\n")
        writer.writeheader();writer.writerows(data)
write_csv("wear_contact_cases.csv",rows)
write_csv("friction_drift_limits.csv",threshold)
write_csv("heterogeneous_phase_cases.csv",mix)
write_csv("redistribution_cases.csv",redist)
write_csv("maintenance_cost_limits.csv",cost)
write_csv("pressure_convergence.csv",conv)
result={"schema":"cycle42-results-v1","physical_tests":0,"physical_success_probability":None,
    "prescribed_morphologies_not_wear_evolution":True,"contact_cases":len(rows),
    "heterogeneous_cases":len(mix),"redistribution_cases":len(redist),
    "check_count":len(checks),"checks":checks,"base_geometry":{"a0_m":A0,"R0_m":R0,"F0_N":F0,"delta0_m":D0},
    "representatives":[x for x in rows if x["specific_wear_mm3_Nm"] in [0,1e-7] and x["profile"]=="smooth_gaussian_removal"],
    "friction_thresholds":threshold,"maintenance_cost_limits":cost,
    "source_data_are_not_calibration":True}
(ROOT/"results.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
env={"python":platform.python_version(),"numpy":np.__version__,"scipy":scipy.__version__,"matplotlib":matplotlib.__version__}
(ROOT/"environment.json").write_text(json.dumps(env,indent=2)+"\n",encoding="utf-8",newline="\n")

if "--no-plots" not in sys.argv:
    plt.rcParams.update({"font.size":10,"figure.dpi":140,"axes.spines.top":False,"axes.spines.right":False})
    fig,ax=plt.subplots(1,2,figsize=(11.5,4.6),layout="constrained")
    colors={1:"#266b8a",4:"#d28132",16:"#843f87"}
    for m in C["split_counts"]:
        for kind,style in [("smooth_gaussian_removal","-"),("flat_truncation","--")]:
            rr=[x for x in rows if x["split_count"]==m and x["profile"]==kind and x["specific_wear_mm3_Nm"]>0]
            ax[0].semilogx([x["specific_wear_mm3_Nm"] for x in rr],[x["interface_mu"] for x in rr],style,color=colors[m],marker="o",label=f"m={m}, "+("smooth" if style=="-" else "flat"))
    ax[0].axhline(.05,color="black",lw=.8,label="Initial hypothesis")
    ax[0].set(xlabel="Assumed specific wear [mm³/(N m)]",ylabel="Interface friction coefficient",title="Equal total loss, different contact shapes")
    ax[0].legend(fontsize=8,ncol=2)
    for w,color in [(0,"#444444"),(.1,"#266b8a"),(1,"#d28132"),(3,"#843f87")]:
        a=solve_shape("smooth_gaussian_removal",w)["a_rel"]; rs=np.linspace(0,a,201)
        ax[1].plot(rs/a,[pressure_rel(float(r),a,w) for r in rs],color=color,label=f"w/δ₀={w:g}")
    ax[1].set(xlabel="Radial position / contact radius",ylabel="Pressure / original mean pressure",title="Smooth prescribed profiles: finite pressure")
    ax[1].legend(fontsize=9)
    fig.suptitle("Shape sensitivity only • 100 local passes × 1.6 m • no material calibration",fontsize=12)
    fig.savefig(ROOT/"wear_contact_response.png");plt.close(fig)
    fig,ax=plt.subplots(1,2,figsize=(11.5,4.6),layout="constrained")
    for phi in [.01,.1,.5]:
        rr=[x for x in mix if x["slow_area_fraction"]==phi]
        ax[0].semilogx([x["k_fast_over_k_slow"] for x in rr],[x["slow_phase_load_fraction"] for x in rr],marker="o",label=f"Slow-wear area {phi:.0%}")
    ax[0].set(xlabel="Specific wear ratio: fast / slow",ylabel="Load fraction on slow-wear phase",ylim=(0,1),title="Area fraction is not load fraction")
    ax[0].legend()
    xs=np.arange(len(cost))
    ax[1].bar(xs,[x["max_added_cost_JPY_processed_kg"] for x in cost],color=["#266b8a","#d28132","#843f87"])
    ax[1].set_xticks(xs,[f'{x["processed_depth_m"]*1000:g} mm' for x in cost])
    ax[1].set(xlabel="Assumed processed depth per operation",ylabel="Gross added-cost ceiling [JPY/kg processed]",title="Replacement 20% → 10%: assumed, not measured")
    for x,row in zip(xs,cost):
        ax[1].text(x,row["max_added_cost_JPY_processed_kg"]+.12,f'{row["max_added_cost_JPY_processed_kg"]:.2f}',ha="center")
    fig.suptitle("Stationary full-contact phase model / 108 t inventory, 200 operations/year",fontsize=12)
    fig.savefig(ROOT/"phase_load_and_maintenance.png");plt.close(fig)
print(json.dumps({"checks":len(checks),"contact_cases":len(rows),"physical_tests":0,"success_probability":None}))
