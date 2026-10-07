from pathlib import Path
import sys,os,json,math,struct
H=Path(__file__).resolve().parent;root=H.parent.parent
if (root/'.deps').exists():sys.path.insert(0,str(root/'.deps'))
os.environ.setdefault('MPLCONFIGDIR',str(root/'.scratch'/'mpl'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'#fbfcfe','axes.facecolor':'#fbfcfe'})
R=json.loads((H/'results.json').read_text(encoding='utf-8'));C=json.loads((H/'hoop_results.json').read_text(encoding='utf-8'))
fig=plt.figure(figsize=(14,5.3))
for j,(label,opening,kind) in enumerate([('R2-L: two open loops',64,'base'),('R3: straight braces conflict',64,'straight'),('R4-150: closed circular brace',150,'hoop')]):
    ax=fig.add_subplot(1,3,j+1,projection='3d');ph=np.linspace(math.radians(opening/2),2*math.pi-math.radians(opening/2),360);r=.24
    ax.plot(r*np.cos(ph),r*np.sin(ph),np.zeros_like(ph),lw=5,color='#255b92');ax.plot(r*np.cos(ph),np.zeros_like(ph),r*np.sin(ph),lw=5,color='#255b92')
    if kind=='straight':
        pts=np.array([[0,r,0],[0,0,r],[0,-r,0],[0,0,-r],[0,r,0]])
        ax.plot(*pts.T,color='#d06932',lw=2)
    if kind=='hoop':
        ph=np.linspace(0,2*math.pi,360);ax.plot(np.zeros_like(ph),r*np.cos(ph),r*np.sin(ph),color='#148779',lw=5)
    ax.set(xlim=(-.29,.29),ylim=(-.29,.29),zlim=(-.29,.29),xlabel='x (mm)',ylabel='y (mm)',zlabel='z (mm)',title=label);ax.set_box_aspect((1,1,1));ax.view_init(elev=23,azim=-55)
    ax.set_xticks([-.24,0,.24]);ax.set_yticks([-.24,0,.24]);ax.set_zticks([-.24,0,.24])
fig.suptitle('Change the load path while preserving an insertion corridor',fontsize=16,y=.99)
fig.text(.5,.035,'Centreline illustrations; stroke widths are explanatory. R4 STL files include rounded solid cross-sections.\nNominal geometry only. Uncalibrated material, loading and manufacturing assumptions.',ha='center',fontsize=10)
fig.subplots_adjust(left=.02,right=.98,bottom=.13,top=.87,wspace=.09);fig.savefig(H/'design_comparison.png',dpi=170);plt.close(fig)
fig,axs=plt.subplots(2,2,figsize=(13,9));blue='#255b92';green='#148779';orange='#d06932'
xs=[x for x in R['variants'] if x['brace_radius_um']==6]
axs[0,0].plot([x['angle_deg'] for x in xs],[x['surface_gap_lower_um'] for x in xs],'o-',color=orange,label='Straight brace: 12 um diameter')
axs[0,0].axhline(10.7685,color=green,label='R4-150: 44 um circular brace');axs[0,0].axhline(0,color='gray',ls='--');axs[0,0].set(xlabel='Straight brace attachment angle (degrees)',ylabel='Surface clearance bound (um)',title='Registered rigid insertion: geometry only');axs[0,0].legend(fontsize=8)
bs=C['balanced_models'];o=[x['opening_deg'] for x in bs];base=[x['unbraced']['responses'][0]['tip_directional_compliance_mm_N'] for x in bs];hoop=[x['hoop']['responses'][0]['tip_directional_compliance_mm_N'] for x in bs]
axs[0,1].plot(o,base,'o-',color=blue,label='Two open loops');axs[0,1].plot(o,hoop,'o-',color=green,label='+ circular brace, 44 um diameter');axs[0,1].set(xlabel='Opening angle (degrees)',ylabel='Mean displacement / total force (mm/N)',title='Four balanced tip forces along x; back clamped');axs[0,1].legend(fontsize=8)
models=[x for x in C['models'] if x['hoop_radius_um']==22];opening=[x['opening_deg'] for x in models];rho=[x['cost']['bulk_kg_m3'] for x in models];axs[1,0].plot(opening,rho,'o-',color=green);axs[1,0].axhline(158.018584,color=orange,ls='--',label='Hypothetical cost-derived cap');axs[1,0].set(xlabel='Opening angle (degrees)',ylabel='Assumed bulk density (kg/m3)',title='Same hypothetical particle count and material density');axs[1,0].legend(fontsize=8)
z=next(x for x in models if x['opening_deg']==150);b=next(x for x in bs if x['opening_deg']==150);vals=[b['hoop']['responses'][0]['linear_diagnostic_force_mN']]+[r['linear_diagnostic_force_mN'] for r in z['mechanics']['responses']];axs[1,1].bar(['4 tips x','1 tip x','1 tip y','1 tip z'],vals,color=[green,blue,blue,blue]);axs[1,1].axhline(.9,color=orange,ls='--',label='0.9 mN from earlier assumed load table');axs[1,1].set(ylabel='Total force scale (mN)',title='R4-150: end of chosen linear diagnostic window');axs[1,1].legend(fontsize=8)
fig.suptitle('R4: a geometric and mechanical candidate, not a validated snow material',fontsize=15)
fig.text(.5,.017,'E = 300 MPa assumed, not measured at 50 C. Diagnostic thresholds are not strength or safety limits.\nNo physical trials; no success probability estimated.',ha='center',fontsize=10)
fig.tight_layout(rect=(0,.08,1,.95));fig.savefig(H/'mechanics_and_cost.png',dpi=170);plt.close(fig)
# Solid mesh view of the two supplied manufacturing comparison shapes.
fig=plt.figure(figsize=(10.5,5.7));dt=np.dtype([('normal','<f4',(3,)),('v','<f4',(3,3)),('attr','<u2')])
for j,opening in enumerate([120,150]):
    b=(H/f'R4_open{opening}_wire44um.stl').read_bytes();n=struct.unpack_from('<I',b,80)[0];tri=np.frombuffer(b,dtype=dt,offset=84,count=n)['v']
    ax=fig.add_subplot(1,2,j+1,projection='3d');coll=Poly3DCollection(tri,facecolor='#76b8c6',edgecolor='none',alpha=1);ax.add_collection3d(coll)
    ax.set(xlim=(-.28,.28),ylim=(-.28,.28),zlim=(-.28,.28),xlabel='x (mm)',ylabel='y (mm)',zlabel='z (mm)',title=f'R4-{opening}: solid one-piece mesh');ax.set_box_aspect((1,1,1));ax.view_init(elev=22,azim=-52);ax.set_xticks([-.24,0,.24]);ax.set_yticks([-.24,0,.24]);ax.set_zticks([-.24,0,.24])
fig.suptitle('Rounded 44 um wires; 240 um centre radius',fontsize=15);fig.text(.5,.03,'Comparison geometry in millimetres. No production, durability or safety certification.',ha='center');fig.subplots_adjust(top=.85,bottom=.15,left=.02,right=.98);fig.savefig(H/'R4_solid_shapes.png',dpi=160);plt.close(fig)
print('Rendered three figures.')
