"""Capillary force scale and conditional material-quantity comparison."""
import json,math
from pair_geometry import H,np,arcs
from scipy.optimize import brentq

def gamma_water(TC):
    tau=1-(TC+273.15)/647.096
    return .2358*tau**1.256*(1-.625*tau)
def volume_sum(model,R,a):
    L=R*sum(hi-lo for _,_,lo,hi in arcs(model));caps={'R4':4,'C3':6,'S3':0}[model]
    return math.pi*a*a*L+caps*2*math.pi*a**3/3

def main():
    I=json.loads((H/'inputs.json').read_text(encoding='utf-8'));old=json.loads((H.parent/'接触配分検証_傾きと自整列_20261007/gravity_results.json').read_text(encoding='utf-8'));r4=next(x for x in old['models'] if x['opening_deg']==150);weight=r4['weight_N'];rows=[]
    for T in I['wet']['temperatures_C']:
        gamma=gamma_water(T)
        for r in I['wet']['contact_radii_um']:
            for theta in I['wet']['contact_angles_deg']:
                F=2*math.pi*r*1e-6*gamma*math.cos(math.radians(theta));rows.append(dict(T_C=T,r_um=r,contact_angle_deg=theta,surface_tension_N_m=gamma,bridge_force_N=F,force_over_R4_weight=F/weight,force_over_0_9mN=F/.0009,equivalent_inertial_acceleration_g=F/weight))
    R=I['geometry']['R_mm'];a=I['geometry']['wire_radius_mm'];V=volume_sum('R4',R,a);cost=[]
    prior_cost=json.loads((H.parent/'荷重経路検証_直交輪と内部補強_20261007/inputs.json').read_text(encoding='utf-8'))['cost'];base_density=prior_cost['matrix_density_kg_m3']*prior_cost['number_density_m3']*V*1e-9;area=2000;depth=.45;price=500;crf=.08*(1.08**10)/(1.08**10-1);nonmaterial=20e6*crf+4e6
    for model in I['geometry']['models']:
        v=volume_sum(model,R,a);ratio=v/V;mass=base_density*ratio*area*depth;aeq=brentq(lambda x:volume_sum(model,R,x)-V,.001,.1)
        cap=(19e6-nonmaterial)/(mass*(crf+.02));eac=nonmaterial+mass*price*(crf+.02)
        cost.append(dict(model=model,volume_sum_upper_mm3=v,same_count_volume_ratio=ratio,equal_volume_wire_diameter_um=2*aeq*1000,conditional_bulk_density_kg_m3=base_density*ratio,conditional_pilot_mass_kg=mass,conditional_material_initial_JPY=mass*price,conditional_EAC_JPY=eac,conditional_price_cap_JPY_kg=cap,conditional_full_course_material_JPY=mass*10*price))
    out=dict(physical_tests=0,success_probability=None,wet_scope=I['wet']['scope'],capillary=rows,R4_weight_N=weight,cost=cost,cost_assumptions=dict(same_grain_count_per_volume=True,base_R4_bulk_density_kg_m3=base_density,area_m2=area,depth_m=depth,finished_grain_price_JPY_kg=price,replenishment_fraction_per_year=.02,years=10,discount=.08,nonmaterial_initial_JPY=20e6,annual_operating_JPY=4e6,annual_budget_JPY=19e6,CRF=crf,additional_alignment_cost_included=False),scope='Bridge existence, contact angle and contact radius are assumptions. Acceleration ratio is a force scale, not a vibration requirement. Costs preserve grain count, not measured packing.')
    (H/'wet_cost_results.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps({'surface_tension_50C':gamma_water(50),'cases':len(rows),'physical_tests':0,'success_probability':None}))
if __name__=='__main__':main()
