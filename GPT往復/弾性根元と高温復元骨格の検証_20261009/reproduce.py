"""Conditional beam layout and 2-D linear elasticity. No recovery prediction."""
from pathlib import Path
import sys,json,math
P=Path(__file__).resolve().parent
deps=P.parents[1]/".research94"/"deps"
if deps.exists():sys.path.insert(0,str(deps))
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
I=json.loads((P/"inputs.json").read_text(encoding="utf-8"));checks=[]
def ck(n,v):
    checks.append({"name":n,"passed":bool(v)})
    if not v:raise AssertionError(n)
def near(a,b,tol=1e-8):return math.isclose(a,b,rel_tol=tol,abs_tol=1e-12)
g=I["geometry_assumed"];m=I["material_assumed"]
L=g["length_m"]*1000;h=g["thickness_m"]*1000;b=g["width_m"]*1000;F=g["force_N"]
E=m["body_E_MPa"];nu=m["poisson"];J=b*h**3/12
delta0=F*L**3/(3*E*J);sigma0=6*F*L/(b*h*h)
def beam(alpha,Er):
    p=1-(1-alpha)**3;r=E/Er
    C=1-p+p*r
    return {"alpha":alpha,"root_E_MPa_assumed":Er,"root_length_um":alpha*L*1000,
            "root_length_over_thickness":alpha*L/h,
            "bending_deflection_um":delta0*C*1000,"compliance_ratio":C,
            "force_ratio_at_fixed_deflection":1/C,
            "root_energy_fraction_not_recovery":p*r/C,
            "root_nominal_strain_at_fixed_force":sigma0/Er if alpha>0 else None,
            "interface_nominal_bending_stress_MPa":sigma0*(1-alpha) if 0<alpha<1 else None,
            "tenfold_force_delta_over_L":delta0*C*10/L}
rows=[beam(a,er) for a in I["root_length_fractions"] for er in m["root_E_MPa"]]
ck("24_layouts",len(rows)==24)
ck("root_weight_10pct",near(1-.9**3,.271))
ck("root_weight_40pct",near(1-.6**3,.784))
ck("zero_root_baseline",all(near(x["compliance_ratio"],1) for x in rows if x["alpha"]==0))
ck("homogeneous_baseline",all(near(x["compliance_ratio"],1) for x in rows if x["root_E_MPa_assumed"]==E))
ck("all_root_compliance",near(beam(1,200)["compliance_ratio"],2.5))
ck("fixed_deflection_force",near(beam(.1,200)["force_ratio_at_fixed_deflection"],1/1.4065))
ck("root_shorter_than_thickness",near(beam(.1,200)["root_length_over_thickness"],.625))
# Independent quadrature of spatial compliance.
N=100000
integral=sum((L-(k+.5)*L/N)**2/(200 if (k+.5)/N<.1 else E) for k in range(N))*L/N
ck("beam_compliance_integral",abs(integral*F/J*1000-beam(.1,200)["bending_deflection_um"])<1e-7)
Dunit=np.array([[1,nu,0],[nu,1,0],[0,0,(1-nu)/2]])/(1-nu**2)
def element(dx,dy):
    coords=np.array([[0,0],[dx,0],[dx,dy],[0,dy]])
    K=np.zeros((8,8))
    for xi in [-1/math.sqrt(3),1/math.sqrt(3)]:
        for eta in [-1/math.sqrt(3),1/math.sqrt(3)]:
            dn=np.array([[-(1-eta),(1-eta),(1+eta),-(1+eta)],
                         [-(1-xi),-(1+xi),(1+xi),(1-xi)]])/4
            jac=dn@coords;grad=np.linalg.solve(jac,dn)
            B=np.zeros((3,8));B[0,0::2]=grad[0];B[1,1::2]=grad[1]
            B[2,0::2]=grad[1];B[2,1::2]=grad[0]
            K+=B.T@Dunit@B*np.linalg.det(jac)*b
    return K
kcheck=element(.025,.02)
tx=np.tile([1,0],4);ty=np.tile([0,1],4)
ck("element_symmetry",np.max(np.abs(kcheck-kcheck.T))<1e-12)
ck("element_rigid_translation",np.linalg.norm(kcheck@tx)+np.linalg.norm(kcheck@ty)<1e-12)
ck("element_nonnegative_energy",np.linalg.eigvalsh(kcheck).min()>-1e-12)
# Constant axial strain with free Poisson contraction: exact energy patch.
dx,dy=.025,.02;eps=.001
coords=np.array([[0,0],[dx,0],[dx,dy],[0,dy]])
u_patch=np.column_stack((eps*coords[:,0],-nu*eps*coords[:,1])).ravel()
ck("constant_strain_patch",near(u_patch@kcheck@u_patch,eps**2*dx*dy*b))
def solve(nx,ny,alpha,Er):
    dx=L/nx;dy=h/ny;ke=element(dx,dy)
    nn=(nx+1)*(ny+1);nd=nn*2
    rr=[];cc=[];vv=[];elements=[]
    for ix in range(nx):
        Ee=Er if (ix+.5)/nx<alpha else E
        for iy in range(ny):
            nodes=[ix*(ny+1)+iy,(ix+1)*(ny+1)+iy,(ix+1)*(ny+1)+iy+1,ix*(ny+1)+iy+1]
            dofs=np.array([d for node in nodes for d in [2*node,2*node+1]])
            rr.extend(np.repeat(dofs,8));cc.extend(np.tile(dofs,8));vv.extend((ke*Ee).ravel())
            elements.append((dofs,Ee,(ix+.5)/nx<alpha))
    K=coo_matrix((vv,(rr,cc)),shape=(nd,nd)).tocsr()
    load=np.zeros(nd);weights=np.ones(ny+1)/ny;weights[[0,-1]]*=.5
    tipd=np.array([2*(nx*(ny+1)+j)+1 for j in range(ny+1)])
    load[tipd]=-F*weights
    nfixed=2*(ny+1);free=np.arange(nfixed,nd)
    u=np.zeros(nd);u[free]=spsolve(K[free][:,free],load[free])
    residual=K@u-load
    U=float(u@(K@u)/2)
    root_U=sum(float(u[d]@(ke*Ee)@u[d]/2) for d,Ee,isroot in elements if isroot)
    avgdelta=float(-weights@u[tipd])
    ry=float(residual[1:nfixed:2].sum());rx=float(residual[:nfixed:2].sum())
    fixed_y=np.linspace(-h/2,h/2,ny+1)
    moment=float(-(fixed_y@residual[:nfixed:2]))
    return {"mesh":[nx,ny],"elements":nx*ny,"dofs":nd,"alpha":alpha,"root_E_MPa_assumed":Er,
            "mean_tip_deflection_um":avgdelta*1000,"energy_N_mm":U,
            "root_energy_fraction_not_recovery":root_U/U,
            "reaction_y_N":ry,"reaction_x_N":rx,"reaction_moment_N_mm":moment,
            "relative_free_residual":float(np.linalg.norm(residual[free])/F)}
fem=[]
for case in I["fem"]["cases"]:
    vals=[]
    for nx,ny in I["fem"]["meshes"]:
        z=solve(nx,ny,case["alpha"],case["root_E_MPa"])
        z["case"]=case["id"];fem.append(z);vals.append(z)
        tag=case["id"]+"_"+str(nx)
        ck("force_balance_"+tag,near(z["reaction_y_N"],F,1e-6) and abs(z["reaction_x_N"])<F*1e-6)
        ck("moment_balance_"+tag,near(abs(z["reaction_moment_N_mm"]),F*L,1e-6))
        ck("work_energy_"+tag,near(2*z["energy_N_mm"],F*z["mean_tip_deflection_um"]/1000,1e-6))
    ck("mesh_convergence_"+case["id"],abs(vals[-1]["mean_tip_deflection_um"]/vals[-2]["mean_tip_deflection_um"]-1)<.015)
last={x["case"]:x for x in fem if x["mesh"]==I["fem"]["meshes"][-1]}
ck("uniform_E_scaling",near(last["all_soft"]["mean_tip_deflection_um"]/last["body"]["mean_tip_deflection_um"],2.5,1e-6))
shear_delta=F*L/((5/6)*(E/(2*(1+nu)))*b*h)
ck("homogeneous_beam_comparison",abs(last["body"]["mean_tip_deflection_um"]/(1000*(delta0+shear_delta))-1)<.06)
inv=I["inventory_assumed"];M=inv["reference_mass_kg"];rb=m["body_density_kg_m3"];rt=m["root_density_kg_m3"]
costs=[]
for f in inv["replacement_volume_fractions"]:
    mass_body=M*(1-f);mass_root=M*f*rt/rb;mass=mass_body+mass_root
    for price in inv["root_prices_JPY_kg"]:
        raw=mass_body*inv["body_price_JPY_kg"]+mass_root*price
        base=M*inv["body_price_JPY_kg"]
        for process in inv["extra_processing_JPY_per_final_kg"]:
            costs.append({"replacement_volume_fraction":f,"root_price_JPY_kg_assumed":price,
              "extra_processing_JPY_kg_assumed":process,"body_mass_kg":mass_body,"root_mass_kg":mass_root,
              "final_mass_kg":mass,"mass_ratio_same_solid_volume":mass/M,
              "raw_material_increment_JPY":raw-base,"extra_processing_JPY":mass*process,
              "increment_excluding_tax_JPY":raw-base+mass*process})
ck("cost_27_cases",len(costs)==27)
selected=next(x for x in costs if x["replacement_volume_fraction"]==.08 and x["root_price_JPY_kg_assumed"]==1500 and x["extra_processing_JPY_kg_assumed"]==0)
ck("10pct_root_volume_budget",near(.1*inv["branch_volume_fraction"],.08))
ck("mass_conservation",all(near(x["final_mass_kg"],x["root_mass_kg"]+x["body_mass_kg"]) for x in costs))
ck("replacement_volume_conservation",all(near(x["body_mass_kg"]/rb+x["root_mass_kg"]/rt,M/rb) for x in costs))
ck("selected_mass",near(selected["final_mass_kg"],138716.12903225806))
ck("selected_raw_increment",near(selected["raw_material_increment_JPY"],16374193.548387095))
out={"physical_experiments":0,"success_probability":None,"actual_recovery_fraction":None,
"actual_50C_moduli":None,"actual_bond_strength":None,"selected_material":None,
"beam_cases":rows,"fem_cases":fem,"fem_finest":last,"cost_cases":costs,"selected_cost_scenario":selected,
"limitations":I["limitations"]+I["fem"]["assumptions"]}
val={"count":len(checks),"all_passed":all(x["passed"] for x in checks),"checks":checks,
"scope":"arithmetic and conditional linear model verification, not physical validation"}
def equal(a,b):
    if isinstance(a,dict):return a.keys()==b.keys() and all(equal(a[k],b[k]) for k in a)
    if isinstance(a,list):return len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
    if isinstance(a,float):return near(a,b,1e-7)
    return a==b
for name,data in [("results.json",out),("validation.json",val)]:
    if "--check" in sys.argv:assert equal(data,json.loads((P/name).read_text(encoding="utf-8"))),name
    else:(P/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
print(json.dumps({"checks":len(checks),"fem_cases":len(fem),"beam_cases":len(rows),"cost_cases":len(costs),
"finest_deflection_um":{k:v["mean_tip_deflection_um"] for k,v in last.items()},"physical_experiments":0}))
