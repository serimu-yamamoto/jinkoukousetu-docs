"""Continuous-path counterexample, not a mechanics/DEM model or success probability.
Run: python analyze.py (standard library only). Length unit is mm.
"""
from pathlib import Path
import json, math, itertools
HERE=Path(__file__).resolve().parent
P=json.loads((HERE/'inputs.json').read_text(encoding='utf-8'))

def geometry(p):
    q=dict(p);R=(p['D_mm']-p['end_diameter_mm'])/2
    r=p['d_mm']/2;e=p['end_diameter_mm']/2
    theta=math.asin((p['end_diameter_mm']+p['gap_mm'])/(2*R))
    L=R*(2*math.pi-2*theta)
    low=math.pi*r*r*L+4*math.pi*r**3/3
    high=low+8*math.pi*(e**3-r**3)/3
    q.update(R_mm=R,r_mm=r,re_mm=e,theta_rad=theta,arc_length_mm=L,
        volume_lower_mm3=low,volume_upper_mm3=high,
        mass_lower_kg=low*1e-9*P['rho_s_kg_m3'],mass_upper_kg=high*1e-9*P['rho_s_kg_m3'])
    return q

def clearance(q,c):
    R=q['R_mm'];t=q['theta_rad']
    return math.hypot(2*R*math.cos(t)-c,math.sqrt(2)*R*math.sin(t))-q['end_diameter_mm']

def direct_3d(q,c,N):
    R=q['R_mm'];t=q['theta_rad']
    pts=[(R*math.cos(t+(2*math.pi-2*t)*i/(N-1)),R*math.sin(t+(2*math.pi-2*t)*i/(N-1))) for i in range(N)]
    return math.sqrt(min((x-(c-u))**2+y*y+z*z for x,y in pts for u,z in pts))-q['end_diameter_mm']

def main():
    out=[];paths=[];tols=[];prod=[];cross=[]
    shapes=[geometry(x) for x in P['candidates']];base=shapes[0]
    C=P['cost'];af=(1-(1+C['r'])**(-C['T_year']))/C['r']
    for q in shapes:
        R=q['R_mm'];de=q['end_diameter_mm'];g=q['gap_mm']
        cs=2*R*math.cos(q['theta_rad']);crit=(math.sqrt(2)-1)*de
        cm=(de+g)/math.sqrt(2)-de
        rec=dict(q);rec.update(critical_separation_mm=cs,minimum_clearance_mm=cm,
            checked_path='CERTIFIED_CLEAR_IN_IDEAL_MODEL' if cm>0 else 'THIS_PATH_INTERSECTS',
            all_paths_retention='NOT_PROVEN',gap_threshold_this_path_mm=crit,
            radial_wear_to_path_tangency_mm=max(0,-cm/2),
            wear_scope='uniform whole-strand radial wear' if math.isclose(de,q['d_mm']) else 'end-guard radial wear while guard diameter remains at least strand diameter',
            tip_shift_to_tangency_each_mm=max(0,(crit-g)/2),
            tip_shift_for_2um_clearance_each_mm=max(0,(crit+math.sqrt(2)*P['surface_clearance_margin_um']/1000-g)/2),
            single_gap_body_pass_shift_each_mm=max(0,(q['d_mm']-g)/2),
            mass_ratio_lower=q['volume_lower_mm3']/base['volume_upper_mm3'],
            mass_ratio_upper=q['volume_upper_mm3']/base['volume_lower_mm3'])
        rho=C['rho_base_kg_m3']*rec['mass_ratio_upper'];M=C['A_m2']*C['h_m']*rho
        eac=(C['I_yen']+M*C['P_yen_kg'])/af+C['O_yen_year']+C['lambda_year']*M*C['P_yen_kg']
        price=((C['B_yen_year']-C['O_yen_year'])*af-C['I_yen'])/(M*(1+C['lambda_year']*af))
        rec.update(assumed_same_count_bulk_upper=rho,assumed_EAC_upper_yen=eac,price_cap_at_bulk_upper_yen_kg=price)
        for i in range(101):
            c=R+2*R*i/100
            paths.append(dict(id=q['id'],center_separation_mm=c,clearance_mm=clearance(q,c)))
        for N,c in itertools.product([17,65,257],[R,cs,3*R]):
            cross.append(dict(id=q['id'],points=N,c_mm=c,error_mm=abs(direct_3d(q,c,N)-clearance(q,c))))
        for tu in P['geometric_tolerances_um']:
            tol=tu/1000;gx=g+tol;ex=de-tol
            cmax=(ex+gx)/math.sqrt(2)-ex
            body_at_corner=ex if math.isclose(de,q['d_mm']) else q['d_mm']+tol
            assert ex>=body_at_corner
            tols.append(dict(id=q['id'],dimension_tolerance_um=tu,body_diameter_at_evaluated_corner_mm=body_at_corner,max_escape_clearance_um=cmax*1000,radial_wear_to_tangency_um=max(0,-cmax*1000/2),
                result='CLEAR_PATH_EXISTS_IN_BOX' if cmax>0 else 'PATH_INTERSECTS_THROUGHOUT_BOX',
                note='Gap and diameter tolerance box. Uniform G1/G2 link body and end diameters; G3 keeps body no larger than the end guard. Not an empirical distribution or all-path proof.'))
        m=P['manufacturing'];pitch=m['pitch_mm']/1000
        per_v=m['width_m']/pitch**2*3600*m['good_part_fraction']
        for speed in m['velocity_m_s']:
            n=per_v*speed;lo=n*q['mass_lower_kg'];hi=n*q['mass_upper_kg']
            prod.append(dict(id=q['id'],speed_m_s=speed,good_parts_hour=n,kg_hour_lower=lo,kg_hour_upper=hi,
                processing_yen_kg_lower=m['line_charge_yen_hour']/hi,processing_yen_kg_upper=m['line_charge_yen_hour']/lo))
        rec.update(speed_for_75kg_hour_lower_m_s=m['required_good_kg_hour']/(per_v*q['mass_upper_kg']),
                   speed_for_75kg_hour_upper_m_s=m['required_good_kg_hour']/(per_v*q['mass_lower_kg']))
        out.append(rec)
    checks={
      'coordinate_crosscheck':max(x['error_mm'] for x in cross)<1e-12,
      'G1_continuous_clear_path':out[0]['minimum_clearance_mm']>0,
      'G2_checked_path_intersects':out[1]['minimum_clearance_mm']<0,
      'G3_checked_path_intersects':out[2]['minimum_clearance_mm']<0,
      'critical_pose_within_proven_interval':all(q['R_mm']<=q['critical_separation_mm']<=3*q['R_mm'] for q in out),
      'outer_envelope_0_6mm':all(math.isclose(2*(q['R_mm']+q['re_mm']),.6) for q in out),
      'volume_bounds_ordered':all(q['volume_lower_mm3']<=q['volume_upper_mm3'] for q in out),
      'G3_mass_upper_increase_under_9percent':out[2]['mass_ratio_upper']<1.09,
      'G2_5um_tolerance_counterexample':any(x['id']=='G2' and x['dimension_tolerance_um']==5 and x['max_escape_clearance_um']>0 for x in tols),
      'G3_10um_checked_path_still_intersects':any(x['id']=='G3' and x['dimension_tolerance_um']==10 and x['max_escape_clearance_um']<0 for x in tols)}
    if not all(checks.values()):raise AssertionError(checks)
    result=dict(scope=P['model'],physical_test_count=0,success_probability=None,candidates=out,
        path_samples=paths,tolerance_boxes=tols,production_area_rate_budget=prod,direct_coordinate_checks=cross)
    (HERE/'results.json').write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
    (HERE/'validation.json').write_text(json.dumps(dict(checks=checks,max_coordinate_error_mm=max(x['error_mm'] for x in cross),physical_validation=False),indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(candidates=out,checks=checks),indent=2,ensure_ascii=False))
if __name__=='__main__':main()
