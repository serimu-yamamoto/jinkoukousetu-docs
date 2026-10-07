"""Inverse diagnostic thresholds and independent numerical checks, not tolerances certified for production."""
import copy,json,math
from contact_model import H,np,normal,evaluate,build_frame
from scipy.optimize import brentq

def main():
    I=json.loads((H/'inputs.json').read_text(encoding='utf-8'));I['geometry']['opening_deg']=150;model=build_frame(I,brace_a=.022,closed_hoop=True);F=.0009;out=[]
    for az in [0,22.5,45]:
        def allforces(beta):
            n=normal(beta,az);tips=model['nodes'][model['tips']];height=tips@n;g=max(height)-height;B=np.zeros((12,4))
            for k in range(4):B[k*3:k*3+3,k]=-n
            C=B.T@model['C']@B;mat=np.zeros((5,5));mat[:4,:4]=C;mat[:4,4]=-1;mat[4,:4]=1;return np.linalg.solve(mat,np.r_[-g,F])[:4]
        contact=brentq(lambda beta:min(allforces(beta)),0,10,xtol=1e-11)
        diag=brentq(lambda beta:evaluate(model,beta,az,F)['mechanics']['linear_diagnostic_ratio']-1,0,2,xtol=1e-10)
        out.append(dict(azimuth_deg=az,first_contact_loss_deg=contact,chosen_linear_diagnostic_boundary_deg=diag))
    h=brentq(lambda a:evaluate(model,0,0,F,offset=[-a,-a,-a,a])['mechanics']['linear_diagnostic_ratio']-1,0,2,xtol=1e-10)
    # Numerically independent interior-integration refinement at a non-symmetric case.
    coarse=evaluate(model,.25,22.5,F);fineI=copy.deepcopy(I);fineI['mechanics']['interior_points']=1025;fine=build_frame(fineI,brace_a=.022,closed_hoop=True);finer=evaluate(fine,.25,22.5,F)
    ref={k:dict(coarse=coarse['mechanics'][k],fine=finer['mechanics'][k],relative=abs(coarse['mechanics'][k]/finer['mechanics'][k]-1)) for k in ['nominal_normal_strain','nominal_shear_strain_upper','max_interior_rotation_rad','max_interior_displacement_mm']}
    contact_data=json.loads((H/'contact_results.json').read_text(encoding='utf-8'))
    hr=[x for x in contact_data['hertz_cases'] if x['opening_deg']==150 and x['total_force_mN']==.9 and x['tilt_deg']==1 and x['azimuth_deg']==0]
    result=dict(physical_tests=0,success_probability=None,load_mN=.9,opening_deg=150,angle_boundaries=out,specific_height_pattern=dict(pattern='[-a,-a,-a,+a] um, initial contact height only',a_um=h,total_height_spread_um=2*h),interior_refinement=ref,endpoint_error_coarse_mm=coarse['mechanics']['endpoint_integration_discrepancy_mm'],endpoint_error_fine_mm=finer['mechanics']['endpoint_integration_discrepancy_mm'],hertz_at_1deg=[dict(plane_E_MPa=x['plane_E_MPa'],maximum_force_mN=max(x['forces_mN']),strain=x['mechanics']['nominal_normal_strain'],patch_over_radius=x['hertz']['max_patch_over_tip_radius']) for x in hr],scope='Boundaries refer to specified contact and linear-diagnostic models; not allowable manufacturing tolerance or material strength.')
    (H/'threshold_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'boundaries':out,'height_spread_um':2*h,'max_refinement_relative':max(x['relative'] for x in ref.values()),'physical_tests':0},indent=2))
if __name__=='__main__':main()
