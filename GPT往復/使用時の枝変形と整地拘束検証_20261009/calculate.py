"""Service-load diagnostics, not a validated ski/material model."""
from pathlib import Path
import sys,json,math,csv
P=Path(__file__).resolve().parent
D=P.parents[1]/'.deps'
if D.exists():sys.path.insert(0,str(D))
import numpy as np
from scipy.integrate import solve_bvp,quad,solve_ivp
from scipy.optimize import brentq
I=json.loads((P/'inputs.json').read_text(encoding='utf-8'));b=I['beam'];checks=[]
def check(name,ok,details=None):
    checks.append({'name':name,'passed':bool(ok),'details':details})
    if not ok:raise AssertionError(name)
def near(name,a,z,rtol=1e-7,atol=1e-12):check(name,math.isclose(a,z,rel_tol=rtol,abs_tol=atol),{'actual':float(a),'expected':float(z)})
L=b['length_m'];rmin=b['minimum_radius_m'];Dref=b['reference_area_factor'];Iref=math.pi*rmin**4/4
# Exact small-deflection compliance minimizer at fixed arm volume and r>=rmin.
B=brentq(lambda v:.6*v**(2/3)+.4/v-Dref,1.000001,20,xtol=1e-13)
transition=1-1/B
def rad(s,profile):
    s=np.asarray(s)
    if profile=='uniform':return np.ones_like(s)*rmin*math.sqrt(Dref)
    if profile=='volume_optimal_clipped':return rmin*np.maximum(1,B*(1-s))**(1/3)
    a=1 if profile=='quadratic_a1' else 5
    return rmin*math.sqrt(Dref/(1+2*a/3+a*a/5))*(1+a*(1-s)**2)
def linear(profile,E,F,q):
    points=[transition/q] if profile=='volume_optimal_clipped' and transition<q else None
    integral=quad(lambda t:(1-t)**2/(float(rad(q*t,profile))/rmin)**4,0,1,points=points,epsabs=1e-11)[0]
    return F*(q*L)**3/(E*Iref)*integral

def solve(profile,E,F,q,tol=None,nmesh=121,scale=1):
    # Coordinates X,Y normalized by loaded arc length q*L*scale, theta angle and m=M/(F*q*L*scale).
    ell=q*L*scale;scaleI=Iref*scale**4;lam=F*ell**2/(E*scaleI)
    x=np.linspace(0,1,nmesh)
    if profile=='volume_optimal_clipped' and transition<q:x=np.unique(np.r_[x,transition/q])
    y=np.zeros((4,len(x)));y[1]=1-x;y[2]=x
    def bc(ya,yb):return np.array([ya[0],yb[1],ya[2],ya[3]])
    # Load continuation selects the branch connected to the unloaded, straight arm.
    for fac in np.linspace(.05,1,12):
        def rhs(t,v):
            j=(rad(q*t,profile)/rmin)**4
            return np.vstack([fac*lam*v[1]/j,-np.cos(v[0]),np.cos(v[0]),np.sin(v[0])])
        sol=solve_bvp(rhs,bc,x,y,tol=tol or b['bvp_tolerance'],max_nodes=16000)
        if not sol.success:raise RuntimeError(profile+' '+sol.message)
        x=sol.x;y=sol.y
    t=np.linspace(0,1,2001);a,m,X,Y=sol.sol(t);r=rad(q*t,profile)*scale
    moment=m*F*ell
    # Axial stress from force resolved along the deformed arm; elongation is neglected in the elastica geometry.
    sn=4*np.abs(moment)/(math.pi*r**3)+abs(F)*np.abs(np.sin(a))/(math.pi*r*r)
    sb=4*np.abs(moment)/(math.pi*r**3)
    max_idx=int(np.argmax(sn));linear_y=linear(profile,E,F/(scale**2),q)*scale
    out={'profile':profile,'E_Pa':E,'F_N':F,'contact_fraction':q,'scale':scale,'lambda':lam,'contact_y_um':float(Y[-1]*ell*1e6),'contact_x_um':float(X[-1]*ell*1e6),'free_tip_y_um':float((Y[-1]*ell+(1-q)*L*scale*math.sin(a[-1]))*1e6),'linear_contact_y_um':linear_y*1e6,'contact_y_over_loaded_length':float(Y[-1]),'linear_y_over_loaded_length':linear_y/ell,'tip_angle_deg':float(a[-1]*180/math.pi),'max_surface_normal_MPa':float(max(sn)/1e6),'max_bending_MPa':float(max(sb)/1e6),'max_linear_elastic_strain_diagnostic':float(max(sn)/E),'strain_above_diagnostic_level':bool(max(sn)/E>b['strain_diagnostic_level']),'max_stress_position_fraction_of_arm':float(t[max_idx]*q),'moment_integral_error':float(max(abs(m-(X[-1]-X)))),'boundary_error':float(max(abs(bc(sol.y[:,0],sol.y[:,-1])))),'max_bvp_residual':float(max(sol.rms_residuals)),'monotone_bend':bool(min(a)>-1e-9 and max(a)<math.pi/2+1e-9 and min(m)>-1e-9),'root_moment_N_m':float(sol.y[1,0]*F*ell)}
    curve=[{'profile':profile,'s_over_L':float(tt*q),'X_um':float(xx*ell*1e6),'Y_um':float(yy*ell*1e6),'radius_um':float(rr*1e6),'theta_rad':float(aa),'normal_MPa':float(ss/1e6)} for tt,xx,yy,rr,aa,ss in zip(t[::10],X[::10],Y[::10],r[::10],a[::10],sn[::10])]
    return out,curve,sol
rows=[];curves=[];refsol={}
for profile in b['profiles']:
    for E in b['E_Pa']:
        for q in b['contact_fractions']:
            for F in b['F_N']:
                row,curve,sol=solve(profile,E,F,q);rows.append(row)
                if E==3e8 and F==1e-4 and q==1:curves+=curve;refsol[profile]=sol
# Fixed-volume / minimum-radius / analytical compliance checks.
profile_info=[]
for profile in b['profiles']:
    volume=math.pi*L*quad(lambda s:float(rad(s,profile))**2,0,1,points=[transition] if profile=='volume_optimal_clipped' else None,epsabs=1e-22)[0]
    near('volume_'+profile,volume,math.pi*L*rmin*rmin*Dref,rtol=1e-9,atol=1e-22)
    profile_info.append({'profile':profile,'root_radius_um':float(rad(0,profile)*1e6),'tip_radius_um':float(rad(1,profile)*1e6),'arm_volume_m3':volume,'linear_compliance_m_N_E300MPa':linear(profile,3e8,1,1)})
near('uniform_linear_compliance',linear('uniform',3e8,1,1),L**3/(3*3e8*Iref*Dref**2))
opt=next(v for v in profile_info if v['profile']=='volume_optimal_clipped')
check('clipped_compliance_below_feasible_controls',all(opt['linear_compliance_m_N_E300MPa']<=v['linear_compliance_m_N_E300MPa'] for v in profile_info if v['profile']!='quadratic_a5'))
near('clipped_min_tip',float(rad(1,'volume_optimal_clipped')),rmin)
near('clipped_volume_closed_form',.6*B**(2/3)+.4/B,Dref)
check('all_bvp_boundary_conditions',max(r['boundary_error'] for r in rows)<1e-9)
check('all_bvp_equilibrium_integral',max(r['moment_integral_error'] for r in rows)<3e-7)
check('all_bvp_residuals',max(r['max_bvp_residual'] for r in rows)<1.1*b['bvp_tolerance'])
check('all_unloaded_connected_branch',all(r['monotone_bend'] for r in rows))
for profile in b['profiles']:
    low,_,_=solve(profile,3e8,1e-9,1)
    near('small_load_limit_'+profile,low['contact_y_um'],low['linear_contact_y_um'],rtol=2e-5)
    refined,_,_=solve(profile,3e8,1e-4,1,tol=1e-9,nmesh=321)
    base=next(r for r in rows if r['profile']==profile and r['E_Pa']==3e8 and r['F_N']==1e-4 and r['contact_fraction']==1)
    near('mesh_refinement_'+profile,base['contact_y_um'],refined['contact_y_um'],rtol=3e-6)
# Independent forward integration of the reference uniform solution.
sol=refsol['uniform'];lam=1e-4*L*L/(3e8*Iref)
def rhs_ivp(t,v):return [lam*v[1]/Dref**2,-math.cos(v[0]),math.cos(v[0]),math.sin(v[0])]
ivp=solve_ivp(rhs_ivp,[0,1],sol.y[:,0],rtol=1e-11,atol=1e-12,dense_output=True)
near('ivp_contact_y',ivp.y[3,-1],sol.y[3,-1],rtol=1e-7)
near('ivp_free_end_moment',ivp.y[1,-1],0,atol=1e-8)
t=np.linspace(0,1,301);ang,m,_,_=sol.sol(t);K=lam/Dref**2
check('uniform_elastica_first_integral',max(abs((K*m)**2-2*K*(math.sin(float(ang[-1]))-np.sin(ang))))<1e-7)
# Similarity: same external stress and geometrically scaled contact arrangement -> force scales as length^2.
scale_rows=[]
Varm=math.pi*L*rmin*rmin*Dref;mass_particle=I['scale']['arms_per_particle']*Varm*I['scale']['solid_density_kg_m3']
base=next(r for r in rows if r['profile']=='quadratic_a1' and r['E_Pa']==3e8 and r['F_N']==1e-4 and r['contact_fraction']==1)
for scale in I['scale']['factors']:
    row,_,_=solve('quadratic_a1',3e8,1e-4*scale**2,1,scale=scale)
    count=I['scale']['reference_mass_kg']/(mass_particle*scale**3)
    scale_rows.append({'scale':scale,'force_ratio_same_stress':scale**2,'relative_deflection':row['contact_y_over_loaded_length'],'surface_normal_MPa':row['max_surface_normal_MPa'],'number_ratio_same_mass':1/scale**3,'nominal_particles_for_reference_mass':count,'number_only_hypothetical_cost_JPY':count/1e6*I['scale']['number_only_handling_JPY_per_million'],'maximum_JPY_per_million_at_processing_budget':I['scale']['processing_budget_JPY_kg']*mass_particle*scale**3*1e6,'nominal_particles_per_second':count/(I['scale']['production_time_hours']*3600),'gravity_to_pressure_force_ratio_scaling':scale,'capillary_to_pressure_force_ratio_scaling':1/scale})
    near('stress_similarity_'+str(scale),row['max_surface_normal_MPa'],base['max_surface_normal_MPa'],rtol=1e-7)
    near('deformation_similarity_'+str(scale),row['contact_y_over_loaded_length'],base['contact_y_over_loaded_length'],rtol=1e-7)
# Dwell time, not total closure time, determines nominal vibration cycles at one point.
g=I['grooming'];moving=g['closure_s']-g['reserved_deploy_and_QA_s'];speed=g['course_length_m']/moving
groom=[]
for width in g['head_widths_m']:
    passes=g['course_width_m']/width
    path=g['course_length_m']*passes
    traverse_speed=path/moving
    for footprint in g['working_lengths_m']:
        for hz in g['frequencies_Hz']:
            dwell=footprint/traverse_speed
            groom.append({'head_width_m':width,'ideal_coverage_passes':passes,'footprint_m':footprint,'frequency_Hz':hz,'speed_m_s':traverse_speed,'point_dwell_s':dwell,'nominal_cycles_per_point':hz*dwell,'cycles_if_whole_moving_time_wrongly_used':hz*moving,'overcount_factor':path/footprint})
required=[]
for cycles in g['reference_cycles']:
    hz=30;required.append({'reference_cycles_not_target':cycles,'frequency_Hz':hz,'required_total_active_length_m':cycles*speed/hz,'required_time_s_at_one_point':cycles/hz,'required_traverse_time_s_for_0_4m_head':g['course_length_m']*cycles/(hz*.4)})
near('dwell_example',next(r['nominal_cycles_per_point'] for r in groom if r['footprint_m']==.4 and r['frequency_Hz']==30 and r['head_width_m']==40),576)
near('10000cycle_head_length',required[-1]['required_total_active_length_m'],6.944444444444445)
# Idealized 2D point probe on the exposed circular arcs of a sphere chain; not a measured friction coefficient.
rough=[]
for eta in I['roughness']['sphere_pitch_over_diameter']:
    rr=I['roughness']['sphere_radius_m'];height=rr*(1-math.sqrt(1-eta**2));slope=eta/math.sqrt(1-eta**2)
    rough.append({'pitch_over_diameter':eta,'height_over_radius':height/rr,'height_um':height*1e6,'maximum_envelope_slope':slope,'spheres_per_straight_length_relative_to_eta0_5':.5/eta})
check('roughness_vanishes_as_pitch_reduces',all(rough[j]['maximum_envelope_slope']>rough[j+1]['maximum_envelope_slope'] for j in range(len(rough)-1)))
check('physical_probability_not_assigned',I['physical_tests']==0 and I['physical_success_probability'] is None)
R={'physical_tests':0,'physical_success_probability':None,'profiles':profile_info,'optimized_taper_B':B,'tip_constant_radius_length_fraction':1/B,'beam_cases':rows,'beam_case_count':len(rows),'similarity':scale_rows,'nominal_particle_mass_kg_without_node_cap_overlap':mass_particle,'grooming':groom,'required_residence':required,'nominal_peak_acceleration_in_g_at_30Hz_2_5mm':(2*math.pi*30)**2*g['amplitude_m']/g['g_m_s2'],'roughness':rough,'numerical_checks':len(checks),'versions':{'python':sys.version.split()[0],'numpy':np.__version__,'scipy':__import__('scipy').__version__}}
(P/'results.json').write_text(json.dumps(R,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
(P/'validation.json').write_text(json.dumps({'passed':True,'count':len(checks),'physical_tests':0,'checks':checks},ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
for filename,data in [('beam_cases.csv',rows),('beam_shapes.csv',curves),('grooming_residence.csv',groom)]:
    with (P/filename).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(data[0]),lineterminator='\n');w.writeheader();w.writerows(data)
print('Computed '+str(len(rows))+' uncalibrated beam cases; '+str(len(checks))+' numerical checks pass. Physical tests = 0.')
