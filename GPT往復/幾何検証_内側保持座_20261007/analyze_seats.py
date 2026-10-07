"""Rigid-plane protection proof budgets and independent directional checks.

The proof uses an inscribed disk in the convex hull of the C centerline.
Finite direction samples corroborate the formulas; they are NOT the proof.
All coordinates in mm; no forces or measured material properties are inferred.
"""
import json, math
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
P=json.loads((HERE/'inputs.json').read_text(encoding='utf-8'))
G=P['G3']; R,r,re,gap=G['R'],G['r'],G['end_radius'],G['gap']
theta=math.asin((2*re+gap)/(2*R))
Rc=R*math.cos(theta)

def protective_support(n):
    p=np.hypot(n[:,0],n[:,1])
    arc=np.where(n[:,0]>p*math.cos(theta),R*(n[:,0]*math.cos(theta)+np.abs(n[:,1])*math.sin(theta)),R*p)
    guards=R*(n[:,0]*math.cos(theta)+np.abs(n[:,1])*math.sin(theta))+re
    return np.maximum(arc+r,guards)

def seat_support(n,c):
    supports=[]
    ax,ay,az=c['axes']
    for angle in c['seat_angles_deg']:
        t=math.radians(angle)
        nr=n[:,0]*math.cos(t)+n[:,1]*math.sin(t)
        nt=-n[:,0]*math.sin(t)+n[:,1]*math.cos(t)
        supports.append(c['rho']*nr+np.sqrt((ax*nr)**2+(ay*nt)**2+(az*n[:,2])**2))
    return np.max(supports,axis=0)

def proof_bound(c):
    # With rho <= Rc, the minimum of b*p+r-sqrt(az²+(a²-az²)*p²)
    # is at an endpoint: concave if a>=az, increasing if a<az.
    assert c['rho']<=Rc
    return min(r-c['axes'][2],Rc-c['rho']+r-max(c['axes'][:2]))

def cost_at_bulk(rho):
    C=P['cost']; rr=C['r']; T=C['T_year']
    crf=rr*(1+rr)**T/((1+rr)**T-1)
    mass=C['A_m2']*C['h_m']*rho
    eac=crf*C['I_yen']+C['O_yen_year']+(crf+C['lambda_year'])*C['P_yen_kg']*mass
    pcap=(C['B_yen_year']-crf*C['I_yen']-C['O_yen_year'])/((crf+C['lambda_year'])*mass)
    return dict(bulk_kg_m3=rho,mass_kg=mass,EAC_yen_year=eac,finished_price_cap_yen_kg=pcap)

def main():
    N=P['numerical_directions']; i=np.arange(N)
    z=1-2*(i+.5)/N; xy=np.sqrt(1-z*z); angle=i*math.pi*(3-math.sqrt(5))
    n=np.stack([xy*np.cos(angle),xy*np.sin(angle),z],axis=1)
    witness=np.array([[-.06,0,math.sqrt(1-.06**2)]])
    n=np.concatenate([n,np.eye(3),-np.eye(3),witness])
    hk=protective_support(n)
    G3next=[v for v in P['reference_volume_bounds'] if v['id']=='G3'][0]
    # Same particle number as prior G3 budget; use SAME reference upper volume.
    Vref=G3next['upper']; tau=P['texture_outward_envelope_allowance_mm']
    rows=[]
    for c in P['candidates']:
        values=hk-seat_support(n,c); k=int(np.argmin(values))
        vlo=4*math.pi/3*math.prod(c['axes'])*len(c['seat_angles_deg'])
        # S + ball(tau) is contained in (1+tau/a_min) S about its center.
        venv=vlo*(1+tau/min(c['axes']))**3
        basebulk=P['cost']['rho_g3_pe_kg_m3']
        centered=min(R-r,R-re,c['rho']-max(c['axes'][:2]))
        rows.append(dict(id=c['id'],c=c,analytic_plane_margin_lower_mm=proof_bound(c),
                         plane_margin_after_outward_envelope_mm=proof_bound(c)-tau,
                         sampled_minimum_plane_margin_mm=float(values[k]),sampled_worst_direction=n[k].tolist(),
                         explicit_counterexample_margin_mm=float((protective_support(witness)-seat_support(witness,c))[0]),
                         attached_to_arc_centerline=all(theta<math.radians(a)<2*math.pi-theta and abs(R-c['rho'])<c['axes'][0] for a in c['seat_angles_deg']),
                         gross_seat_volume_mm3=vlo,outward_envelope_seat_volume_upper_mm3=venv,
                         added_volume_fraction_of_G3_lower_bound_max=venv/G3next['lower'],
                         union_volume_upper_mm3=Vref+venv,
                         cost_upper_with_outward_envelope=cost_at_bulk(basebulk*(1+venv/Vref)),
                         cost_upper_nominal_untextured_seat=cost_at_bulk(basebulk*(1+vlo/Vref)),
                         centered_axial_open_radius_mm=centered,
                         centered_axial_open_radius_after_envelope_mm=centered-tau))
    # Directly evaluated conservative f(p) cross-check, not a substitute for proof.
    ps=np.linspace(0,1,10001)
    for c in P['candidates']:
        a=max(c['axes'][:2]); az=c['axes'][2]
        f=(Rc-c['rho'])*ps+r-np.sqrt(az*az+(a*a-az*az)*ps*ps)
        assert float(np.min(f))>=proof_bound(c)-1e-12
    cap=P['capillary']
    apertures=[]
    for name,rad in [('arc_only_incomplete',R-r),('G3_including_guards',min(R-r,R-re)),('W1_with_envelope',.22-.04-tau)]:
        head=2*cap['gamma_N_m']*abs(math.cos(math.radians(cap['angle_deg'])))/(cap['rho_water_kg_m3']*cap['g_m_s2']*rad*1e-3)
        apertures.append(dict(id=name,radius_mm=rad,ideal_entry_head_mm=head*1000))
    # Independent direct centerline sampling checks the branch in h_K.
    angles=np.linspace(theta,2*math.pi-theta,20001)
    centers=np.stack([R*np.cos(angles),R*np.sin(angles),np.zeros_like(angles)],axis=1)
    check_n=n[np.linspace(0,len(n)-1,128,dtype=int)]
    sampled_arc=np.max(centers@check_n.T,axis=0)+r
    endpoint_centers=np.array([[R*math.cos(theta),R*math.sin(theta),0],
                               [R*math.cos(theta),-R*math.sin(theta),0]])
    direct=np.maximum(sampled_arc,np.max(endpoint_centers@check_n.T,axis=0)+re)
    analytic=protective_support(check_n)
    sagitta=R*(1-math.cos((angles[1]-angles[0])/2))
    error=analytic-direct
    # A counterexample shape with a large seat, same reference orientation.
    checks={
        'unit_directions':bool(np.allclose(np.linalg.norm(n,axis=1),1)),
        'thick_seat_has_explicit_exposure':rows[0]['explicit_counterexample_margin_mm']<0,
        'W1_positive_analytic_margin_including_envelope':all(x['plane_margin_after_outward_envelope_mm']>0 for x in rows[1:]),
        'samples_respect_all_direction_lower_bounds':all(x['sampled_minimum_plane_margin_mm']>=x['analytic_plane_margin_lower_mm']-1e-12 for x in rows),
        'seats_connected_to_backbone':all(x['attached_to_arc_centerline'] for x in rows),
        'three_seats_have_three_times_gross_volume':math.isclose(rows[2]['gross_seat_volume_mm3'],3*rows[1]['gross_seat_volume_mm3']),
        'guards_reduce_centered_aperture':apertures[1]['radius_mm']<apertures[0]['radius_mm'],
        'support_at_z_includes_guard':math.isclose(protective_support(np.array([[0,0,1]]))[0],re),
        'support_formula_agrees_with_direct_arc_sampling':bool(np.min(error)>-1e-12 and np.max(error)<sagitta+1e-12),
    }
    assert all(checks.values()),checks
    out=dict(scope=P['scope'],physical_test_count=0,physical_success_probability=None,
             G3=dict(R=R,r=r,re=re,theta=theta,inscribed_convex_hull_disk_radius=Rc),
             directions_checked=len(n),candidates=rows,aperture_comparison=apertures,
             direct_support_check=dict(normals=128,arc_points=20001,max_error_mm=float(np.max(error)),
                                       chord_sagitta_bound_mm=sagitta))
    (HERE/'results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (HERE/'validation.json').write_text(json.dumps(dict(algebra_and_geometry_checks=checks,physical_validation=False),indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(checks=checks,rows=rows,apertures=apertures),ensure_ascii=False))

if __name__=='__main__':main()
