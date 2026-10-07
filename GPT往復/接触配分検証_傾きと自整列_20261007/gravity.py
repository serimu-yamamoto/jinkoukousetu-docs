"""Dry flat-support orientation from exact ideal support functions and mesh mass centres.
A lower energy orientation is not an observed orientation or probability in a bed.
"""
from pathlib import Path
import json,math,struct
from contact_model import H,np,support,normal

def mesh_mass(path):
    b=path.read_bytes();nt=struct.unpack_from('<I',b,80)[0];assert len(b)==84+50*nt
    dt=np.dtype([('n','<f4',(3,)),('v','<f4',(3,3)),('a','<u2')]);v=np.frombuffer(b,dtype=dt,offset=84,count=nt)['v'].astype(float)
    dv=np.einsum('ij,ij->i',v[:,0],np.cross(v[:,1],v[:,2]))/6;vol=float(sum(dv));c=np.sum(dv[:,None]*np.sum(v,axis=1)/4,axis=0)/vol
    return vol,c

def separate_mass(R,a,opening):
    al=math.radians(opening/2);L=R*(2*math.pi-2*al);arcV=2*L*math.pi*a*a;capV=8*math.pi*a**3/3;hoopV=2*math.pi*R*math.pi*a*a
    arcx=-R*math.sin(al)/(math.pi-al);capx=R*math.cos(al)+3*a*math.sin(al)/8
    return arcV+capV+hoopV,(arcV*arcx+capV*capx)/(arcV+capV+hoopV)

def analytic_min(R,a,opening,cx):
    # For alpha in [45,90) and symmetric mass centre (cx,0,0), at fixed nx=u
    # max(h_XY,h_XZ) is minimized by |ny|=|nz|. The hoop contribution is fixed.
    # There the support is piecewise: max(sqrt(1-u^2), circular arc support).
    al=math.radians(opening/2);assert math.pi/4<=al<math.pi/2
    c=-cx/R;K=(1-math.sin(al)/math.sqrt(2))/math.cos(al);us=K/math.sqrt(1+K*K)
    candidates=[-1.,-1/math.sqrt(3),0.,us,1.]
    if 0<c<1/math.sqrt(2):
        u=-math.sqrt(2)*c/math.sqrt(1-2*c*c)
        if -1<=u<=-1/math.sqrt(3):candidates.append(u)
    data=[]
    for u in candidates:
        v=math.sqrt(max(0,1-u*u))/math.sqrt(2);n=np.array([u,v,v]);height=support(n,R,a,opening)-cx*u
        data.append(dict(nx=u,beta_deg=math.degrees(math.acos(u)),azimuth_deg=45,height_mm=height))
    return dict(c=-cx/R,candidates=data,minimum=min(data,key=lambda x:x['height_mm']),face_down_height_mm=R*math.cos(al)+a-cx,scope='Exact ideal support geometry conditional on the supplied mass centre; not a dynamic settling result.')

def main():
    I=json.loads((H/'inputs.json').read_text(encoding='utf-8'));g=I['geometry'];R=g['R_mm'];a=g['wire_radius_mm'];rows=[];scans=[]
    for opening,rel in zip(g['openings_deg'],I['gravity']['mesh_files']):
        vol,c=mesh_mass(H/rel);altvol,altcx=separate_mass(R,a,opening);result=analytic_min(R,a,opening,float(c[0]));alt=analytic_min(R,a,opening,altcx)
        beta=np.arange(0,180+I['gravity']['tilt_step_deg']/2,I['gravity']['tilt_step_deg']);curves=[]
        for az in I['gravity']['azimuth_deg']:
            heights=[support(normal(b,az),R,a,opening)-float(c[0])*math.cos(math.radians(b)) for b in beta]
            curves.append(dict(azimuth_deg=az,beta_deg=beta.tolist(),height_mm=heights))
        diag=np.array(curves[-1]['height_mm']);ids=beta<=math.degrees(math.acos(-1/math.sqrt(3)))
        barrier=float(max(diag[ids])-result['face_down_height_mm']);mass=vol*1e-9*I['gravity']['density_kg_m3'];weight=mass*I['gravity']['g_m_s2']
        foot_radius=R*math.sin(math.radians(opening/2));face_height=result['face_down_height_mm'];slope=[]
        for az in [0,22.5,45]:
            cf=abs(math.cos(math.radians(az)))+abs(math.sin(math.radians(az)))
            slope.append(dict(slope_azimuth_deg=az,geometric_tipping_deg=math.degrees(math.atan(foot_radius/(face_height*cf))),at_30deg_inside_support_polygon=face_height*math.tan(math.radians(30))*cf<foot_radius,diamond_margin_at_30deg_mm=foot_radius-face_height*math.tan(math.radians(30))*cf))
        wind_force=.5*1.2*80**2*math.pi*((R+a)/1000)**2
        rows.append(dict(ideal_face_support_on_slope=slope,friction_coefficient_needed_without_other_retention_at_30deg=math.tan(math.radians(30)),isolated_wind_scale=dict(air_density_kg_m3=1.2,velocity_m_s=80,assumed_drag_coefficient=1,bounding_disk_area_m2=math.pi*((R+a)/1000)**2,force_N=wind_force,force_over_weight=wind_force/weight,scope='Illustrative exposed disk scale, not drag of porous or shielded grain and not a wind-retention test'),opening_deg=opening,mesh_volume_mm3=vol,mesh_centroid_mm=c.tolist(),centroid_transverse_asymmetry_mm=float(np.linalg.norm(c[1:])),separate_parts_centroid_x_mm=altcx,separate_parts_volume_upper_mm3=altvol,mesh_centroid_analysis=result,separate_parts_analysis=alt,orientation_curves=curves,barrier_to_rear_diagonal_mm=barrier,barrier_J=weight*barrier/1000,weight_N=weight,mass_kg=mass,force_0_9mN_over_weight=.0009/weight))
        assert min(diag)>=result['minimum']['height_mm']-1e-12
        for row in curves:assert np.min(np.array(row['height_mm'])-diag)>-1e-12
    for op in range(90,171,5):
        vol,cx=separate_mass(R,a,op);ans=analytic_min(R,a,op,cx);scans.append(dict(opening_deg=op,volume_sum_mm3=vol,centroid_x_mm=cx,face_height_mm=ans['face_down_height_mm'],minimum=ans['minimum'],mass_model='separate shapes before overlap subtraction'))
    out=dict(metadata={'physical_tests':0,'success_probability':None,'scope':I['gravity']['scope']},models=rows,opening_scan=scans)
    (H/'gravity_results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'models':2,'minima':[{'opening':x['opening_deg'],'beta_deg':x['mesh_centroid_analysis']['minimum']['beta_deg'],'height_um':1000*x['mesh_centroid_analysis']['minimum']['height_mm']} for x in rows],'physical_tests':0,'success_probability':None},indent=2))
if __name__=='__main__':main()
