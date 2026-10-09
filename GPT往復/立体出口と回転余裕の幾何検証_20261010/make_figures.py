from mobility import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
M=json.loads((D/'mobility_results.json').read_text(encoding='utf-8'))
Pth=json.loads((D/'path_results.json').read_text(encoding='utf-8'))
C=json.loads((D/'correction_results.json').read_text(encoding='utf-8'))
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,ax=plt.subplots(1,3,figsize=(15,4.8),layout='constrained')
caps=[0,.1,.5,1];angles=[0,90,180,270]
z=np.array([[next(r['rise_per_mm'] for r in M['mobility'] if r['model']=='C3' and r['pose']==3 and r['heading_deg']==ang and r['rotation_component_cap']==cap) for cap in caps] for ang in angles])
im=ax[0].imshow(z+0.01,norm=LogNorm(vmin=.01,vmax=60),cmap='YlOrRd',aspect='auto')
for i in range(4):
 for j in range(4):ax[0].text(j,i,f'{z[i,j]:.3f}',ha='center',va='center',color='black' if z[i,j]<5 else 'white',fontsize=9)
ax[0].set(xticks=range(4),xticklabels=caps,yticks=range(4),yticklabels=angles,xlabel='Cap on each component of R omega / forward speed',ylabel='Horizontal heading (deg)',title='A  C3: minimum instantaneous plate rise / travel')
for data,label,color in [(Pth['rows'],'Original path','#bb4b29'),(C['corrected_path_endpoints'],'With sideways travel = -0.1 s','#006d77')]:
 rows=[r for r in data if r.get('model','C3')=='C3' and r.get('sideways_per_forward',-.1)==-.1]
 x=[r['travel_mm']*1000 for r in rows]
 lo=[min(v['clearance_lower_mm'] for v in r['support_distances'])*1000 for r in rows]
 hi=[min(v['clearance_upper_mm'] for v in r['support_distances'])*1000 for r in rows]
 ax[1].plot(x,hi,'o-',label=label,color=color)
 ax[1].fill_between(x,lo,hi,color=color,alpha=.2)
ax[1].axhline(0,color='gray',ls='--',lw=1)
ax[1].set(xlabel='Forward travel (micrometres)',ylabel='Minimum support clearance (micrometres)',title='B  Endpoints only; interpolation is not certified')
ax[1].legend(fontsize=8)
rel=[r for r in M['relief'] if r['model']=='C3' and r['pose']==3]
ax[2].bar([str(r['heading_deg']) for r in rel],[r['max_at_20_um_um'] for r in rel],color='#457b9d')
ax[2].set(xlabel='Horizontal heading (deg)',ylabel='Required normal relief (micrometres)',title='C  No whole-grain rotation; 20 micrometre travel')
for a0 in ax[1:]:a0.grid(axis='y',alpha=.2)
fig.suptitle('Cycle 99 | Rigid geometry diagnostics, not ski performance or 50 C measurements',fontsize=13)
fig.savefig(D/'mobility_and_correction.png',dpi=160);plt.close(fig)
from pair_geometry import arcs,point
f=next(f for f in F if f['model']=='C3' and f['pose_id']==3)
fig=plt.figure(figsize=(11,5.5),layout='constrained')
ax=fig.add_subplot(121,projection='3d')
def drawgrain(rot,center,color,alpha,lw):
 for arc in arcs('C3'):
  ts=np.linspace(arc[2],arc[3],101)
  pts=np.array([point(arc,t,R,rot)+center for t in ts])*1000
  ax.plot(pts[:,0],pts[:,1],pts[:,2],color=color,alpha=alpha,lw=lw)
for n in f['supports']:drawgrain(np.array(n['rotation']),np.array(n['center']),'gray',.45,1.5)
drawgrain(np.array(f['central_rotation']),np.zeros(3),'#006d77',1,2.5)
last=next(r for r in C['corrected_path_endpoints'] if r['sideways_per_forward']==-.1 and r['travel_mm']==.02)
drawgrain(np.array(last['rotation']),np.array(last['center_mm']),'#c05027',.95,1.5)
ax.set(xlabel='x (um)',ylabel='y (um)',zlabel='z (um)',title='Three fixed neighbours; central C3 before / after')
ax.view_init(24,135);ax.set_box_aspect([1,1,1])
ax2=fig.add_subplot(122)
pts=[r for r in C['corrected_path_endpoints'] if r['sideways_per_forward']==-.1]
ax2.plot([-r['center_mm'][0]*1000 for r in pts],[r['center_mm'][1]*1000 for r in pts],'o-',color='#006d77')
ax2.set(xlabel='Forward displacement -x (um)',ylabel='Side displacement y (um)',title='Prescribed lateral correction (not force-driven)')
ax2.grid(alpha=.2)
fig.suptitle('Geometry from cycle 13 | Curves are wire centre-lines; wire radius = 22 um',fontsize=13)
fig.savefig(D/'fixture_and_path.png',dpi=160)
print('Two original geometry and diagnostic figures generated')

import scipy
(D/'runtime_versions.json').write_text(json.dumps({'numpy':np.__version__,'scipy':scipy.__version__,'matplotlib':matplotlib.__version__},indent=2)+'\n',encoding='utf-8',newline='\n')
