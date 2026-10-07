from pathlib import Path
import sys,os,json,math
H=Path(__file__).resolve().parent;root=H.parent.parent
if (root/'.deps').exists():sys.path.insert(0,str(root/'.deps'))
os.environ.setdefault('MPLCONFIGDIR',str(root/'.scratch'/'mpl'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
plt.rcParams.update({'font.size':10,'axes.spines.right':False,'axes.spines.top':False,'axes.facecolor':'#fbfcfe','figure.facecolor':'#fbfcfe'})
C=json.loads((H/'contact_results.json').read_text(encoding='utf-8'));G=json.loads((H/'gravity_results.json').read_text(encoding='utf-8'));T=json.loads((H/'threshold_results.json').read_text(encoding='utf-8'))
blue='#255b92';green='#148779';orange='#d06932';purple='#8054a8'
fig,ax=plt.subplots(2,2,figsize=(13,9));rows=[x for x in C['tilt_cases'] if x['opening_deg']==150 and x['azimuth_deg']==0 and x['total_force_mN']==.9]
for j,col in enumerate([blue,green,orange,purple]):ax[0,0].plot([x['tilt_deg'] for x in rows],[x['forces_mN'][j] for x in rows],'o-',color=col,label=f'Tip {j+1}')
ax[0,0].set(xlabel='Misalignment to contact plane (degrees)',ylabel='Force at each tip (mN)',title='R4-150, fixed back, total force 0.9 mN');ax[0,0].legend(fontsize=8)
for az,col in [(0,blue),(22.5,green),(45,purple)]:
    rr=[x for x in C['tilt_cases'] if x['opening_deg']==150 and x['azimuth_deg']==az and x['total_force_mN']==.9 and x['tilt_deg']<=2]
    ax[0,1].plot([x['tilt_deg'] for x in rr],[100*x['mechanics']['nominal_normal_strain'] for x in rr],'o-',color=col,label=f'Azimuth {az:g} deg')
ax[0,1].axhline(1,color=orange,ls='--',label='Chosen linear-model diagnostic');ax[0,1].set(xlabel='Misalignment (degrees)',ylabel='Nominal axial + bending strain (%)',title='Four contacts can remain active while load becomes uneven');ax[0,1].legend(fontsize=8)
x=[0,.5,1,2]
for label,collection,col in [('Fixed back',C['tilt_cases'],blue),('Ideal rotation at back',C['ideal_rotation_cases'],green),('Hertz contact, plane E=100 MPa',C['hertz_cases'],purple)]:
    rr=[q for q in collection if q['opening_deg']==150 and q['azimuth_deg']==0 and q['total_force_mN']==.9 and q['tilt_deg'] in x and (q['plane_E_MPa'] is None or q['plane_E_MPa']==100)]
    rr.sort(key=lambda q:q['tilt_deg']);ax[1,0].plot([q['tilt_deg'] for q in rr],[100*q['mechanics']['nominal_normal_strain'] for q in rr],'o-',color=col,label=label)
ax[1,0].axhline(1,color=orange,ls='--');ax[1,0].set(xlabel='Misalignment (degrees)',ylabel='Nominal strain (%)',title='Support rotation matters more than local indentation here');ax[1,0].legend(fontsize=8)
off=C['height_cases'];rr=[q for q in off if q['opening_deg']==150];vals=[q['mechanics']['linear_diagnostic_ratio'] for q in rr];ax[1,1].bar(range(1,17),vals,color=[green if v<=1 else orange for v in vals]);ax[1,1].axhline(1,color=blue,ls='--');ax[1,1].set(xlabel='Enumerated +/- 2 um height configuration',ylabel='Diagnostic ratio (not a failure ratio)',title='Initial contact heights only; not full shape tolerances')
fig.suptitle('Contact forces solved from gaps, not assigned equally',fontsize=16);fig.text(.5,.018,'E = 300 MPa assumed; no physical experiments. Diagnostic limits are not material allowables.\nLarge-strain cases show the limits of a linear model, not physical deformation predictions.',ha='center',fontsize=10);fig.tight_layout(rect=(0,.08,1,.95));fig.savefig(H/'contact_sensitivity.png',dpi=170);plt.close(fig)
fig,ax=plt.subplots(1,2,figsize=(13,5.8))
for j,item in enumerate(G['models']):
    for curve,col in zip(item['orientation_curves'],[blue,green,purple]):ax[j].plot(curve['beta_deg'],np.array(curve['height_mm'])*1000,color=col,label=f'Azimuth {curve["azimuth_deg"]:g} deg')
    minimum=item['mesh_centroid_analysis']['minimum'];ax[j].scatter([minimum['beta_deg']],[minimum['height_mm']*1000],color=orange,zorder=5,s=70)
    ax[j].set(xlabel='Angle of +x axis to support normal (degrees)',ylabel='Mass-centre height above flat plane (um)',title=f'R4-{item["opening_deg"]}: dry homogeneous grain');ax[j].legend(fontsize=8);ax[j].grid(alpha=.2)
fig.suptitle('A preferred resting orientation does not establish a settling probability',fontsize=15)
fig.text(.5,.025,'0 degrees: all four rounded ends point toward the support. Mass centres estimated from supplied STL meshes.\nNo interparticle contacts, frictional arrest, wet forces, or dynamic grooming are simulated.',ha='center',fontsize=10);fig.tight_layout(rect=(0,.12,1,.94));fig.savefig(H/'gravity_orientation.png',dpi=170);plt.close(fig)
fig,ax=plt.subplots(1,2,figsize=(12,5.5))
for j,item in enumerate(G['models']):
    al=math.radians(item['opening_deg']/2);r=.24*math.sin(al)*1000;h=item['mesh_centroid_analysis']['face_down_height_mm']*1000;verts=np.array([[r,0],[0,r],[-r,0],[0,-r]])
    ax[j].add_patch(Polygon(verts,facecolor='#dbeef2',edgecolor=blue,lw=2));ax[j].scatter(verts[:,0],verts[:,1],s=45,color=blue)
    for phi,col in [(0,green),(45,orange)]:
        p=h*math.tan(math.radians(30))*np.array([math.cos(math.radians(phi)),math.sin(math.radians(phi))]);ax[j].plot([0,p[0]],[0,p[1]],color=col,lw=2);ax[j].scatter(*p,color=col,s=65,label=f'Gravity projection, azimuth {phi} deg')
    ax[j].set(xlim=(-260,260),ylim=(-260,260),aspect='equal',xlabel='Foot-plane y (um)',ylabel='Foot-plane z (um)',title=f'R4-{item["opening_deg"]}: ideal four-tip support at 30 deg');ax[j].legend(fontsize=8,loc='lower left');ax[j].grid(alpha=.15)
fig.suptitle('Tipping and sliding are separate requirements',fontsize=16)
fig.text(.5,.025,'The gravity projection lies inside this ideal support polygon. Without other retention, sliding requires mu >= tan(30 deg) = 0.577.\nThis is not proof of slope, winter-interface, wind, or wet-bed stability.',ha='center',fontsize=10);fig.tight_layout(rect=(0,.13,1,.94));fig.savefig(H/'slope_support.png',dpi=170);plt.close(fig)
print('Rendered three scientific comparison figures.')
