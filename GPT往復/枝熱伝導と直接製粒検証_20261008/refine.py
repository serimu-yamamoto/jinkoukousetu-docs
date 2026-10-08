from pathlib import Path
import sys,json,math
P=Path(__file__).resolve().parent
dep=P.parents[1]/'.deps'
if dep.exists():sys.path.insert(0,str(dep))
import numpy as np
I=json.loads((P/'inputs.json').read_text(encoding='utf8'));T=I['thermal']
rho,cp,k=T['rho_kg_m3'],T['cp_J_kgK'],T['k_W_mK']
r=.5e-6;L=50e-6;h=500;area=math.pi*r*r;ell=math.sqrt(k*r/(2*h))
steady=[]
for n in [16,32,64,128]:
    dx=L/n;g=k*area/dx;ha=h*2*math.pi*r*dx
    A=np.eye(n)*ha;b=np.full(n,ha*T['gas_C'])
    for j in range(n-1):
        A[j,j]+=g;A[j+1,j+1]+=g;A[j,j+1]-=g;A[j+1,j]-=g
    A[0,0]+=2*g;b[0]+=2*g*T['T0_C']
    fv=np.linalg.solve(A,b);x=(np.arange(n)+.5)*dx
    exact=T['gas_C']-(T['gas_C']-T['T0_C'])*np.cosh((L-x)/ell)/math.cosh(L/ell)
    steady.append(dict(cells=n,max_temperature_error_C=float(np.max(np.abs(fv-exact))),tip_cell_C=float(fv[-1]),analytic_tip_cell_C=float(exact[-1])))
beads=[]
for ru in [.5,1]:
    for lu in [10,40,90]:
        a=(3*ru*ru*lu/4)**(1/3)
        beads.append(dict(radius_um=ru,melted_length_um=lu,equivalent_single_sphere_radius_um=a,equivalent_sphere_diameter_um=2*a,note='Conserved volume if collected into one sphere only. Retraction, contact angle, detached droplets and grain shape not predicted.'))
tests=[
dict(name='steady spatial errors decrease with refinement',passed=steady[0]['max_temperature_error_C']>steady[1]['max_temperature_error_C']>steady[2]['max_temperature_error_C']),
dict(name='steady 128-cell maximum error below 0.02C',passed=steady[-1]['max_temperature_error_C']<.02),
dict(name='finite volume approaches second-order spatial convergence',passed=3.5<steady[0]['max_temperature_error_C']/steady[1]['max_temperature_error_C']<4.5 and 3.5<steady[1]['max_temperature_error_C']/steady[2]['max_temperature_error_C']<4.5)
]
R=dict(steady_fin_comparison=steady,bead_volume_diagnostic=beads,tests=tests,all_passed=all(x['passed'] for x in tests))
(P/'refinement.json').write_bytes((json.dumps(R,indent=2,allow_nan=False)+'\n').encode('utf8'))
print(json.dumps(dict(all_passed=R['all_passed'],steady_errors_C=[x['max_temperature_error_C'] for x in steady],sphere_diameter_for_r05_L40_um=next(x['equivalent_sphere_diameter_um'] for x in beads if x['radius_um']==.5 and x['melted_length_um']==40))))
if not R['all_passed']:raise SystemExit('refinement check failed')
