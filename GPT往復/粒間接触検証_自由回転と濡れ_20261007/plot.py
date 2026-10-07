from pathlib import Path
import os,json,math
from pair_geometry import H,ROOT,np,arcs,point
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.scratch/mpl'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
P=json.loads((H/'pair_results.json').read_text(encoding='utf-8'));C=json.loads((H/'cluster_results.json').read_text(encoding='utf-8'));W=json.loads((H/'wet_cost_results.json').read_text(encoding='utf-8'))
colors={'R4':'#235b91','C3':'#0d8378','S3':'#8956a8'}
plt.rcParams.update({'font.size':10,'figure.facecolor':'#fcfcfe','axes.facecolor':'#fcfcfe','axes.spines.top':False,'axes.spines.right':False})
fig=plt.figure(figsize=(13,5.7))
for j,model in enumerate(['R4','C3','S3']):
 ax=fig.add_subplot(1,3,j+1,projection='3d')
 for arc in arcs(model):
  ts=np.linspace(arc[2],arc[3],300);q=np.array([point(arc,t,.24,np.eye(3)) for t in ts]);ax.plot(*q.T,color=colors[model],lw=7,solid_capstyle='round')
 ax.set(xlim=(-.28,.28),ylim=(-.28,.28),zlim=(-.28,.28),xlabel='x (mm)',ylabel='y (mm)',zlabel='z (mm)',title={'R4':'R4: two open arcs + closed hoop','C3':'C3: cyclic openings in three planes','S3':'S3: three closed hoops (control)'}[model]);ax.set_box_aspect([1,1,1]);ax.view_init(24,37)
fig.suptitle('Independent grains: candidate topology, not a mat or mesh',fontsize=15);fig.text(.5,.035,'Centreline rendering; actual circular wire diameter 44 um, centreline radius 240 um. C3 is unvalidated; S3 is only a support-shape control.',ha='center',fontsize=10);fig.subplots_adjust(left=.025,right=.965,bottom=.14,top=.88,wspace=.1);fig.savefig(H/'three_shapes.png',dpi=170);plt.close(fig)
fig,axes=plt.subplots(3,3,figsize=(12,9))
for row,model in enumerate(['R4','C3','S3']):
 for col,pose in enumerate([0,3,7]):
  ax=axes[row,col];x=next(x for x in C['fixtures'] if x['model']==model and x['pose_id']==pose);ax.set_title(model+' / prescribed pose '+str(pose))
  if not x['neighbor_geometry_valid']:
   ax.text(.5,.5,'Neighbors overlap\nForce cases excluded',ha='center',va='center',transform=ax.transAxes);ax.set_xticks([]);ax.set_yticks([]);continue
  vals=np.array([{'infeasible_outer':0,'unresolved':1,'feasible_inner':2}[f['classification']] for f in x['force_cases']]).reshape(3,4)
  ax.imshow(vals,cmap=ListedColormap(['#efc5b3','#fff1a8','#a6dcd3']),vmin=0,vmax=2,aspect='auto');ax.set_xticks(range(4),[0,.1,.3,.6]);ax.set_yticks(range(3),[0,.1,.3]);ax.set_xlabel('Internal friction assumption');ax.set_ylabel('Platen friction assumption')
  for iy,ix in np.ndindex(vals.shape):ax.text(ix,iy,['No','?','Yes'][int(vals[iy,ix])],ha='center',va='center')
fig.suptitle('Force and moment balance at prescribed contact sites',fontsize=15);fig.text(.5,.025,'Yes: feasible in the inner cone. No: infeasible even in the outer cone. These are static model outcomes, not success rates.\nThree fixed neighbors, approximate contact sites (height bracket 0.02 um), no settling, bending, cohesion or 50 C material validation.',ha='center',fontsize=10);fig.tight_layout(rect=[0,.08,1,.95]);fig.savefig(H/'fixture_balance.png',dpi=170);plt.close(fig)
fig,axs=plt.subplots(1,3,figsize=(14,5.4))
for model in colors:
 vals=next(x for x in P['calipers'] if x['model']==model)['widths_mm'];axs[0].plot(sorted(np.array(vals)*1000),color=colors[model],label=model)
axs[0].set(xlabel='Sorted prescribed direction index',ylabel='Caliper width (um)',title='Width variation across 270 directions');axs[0].legend()
for r in [11,22]:
 rows=[x for x in W['capillary'] if x['T_C']==50 and x['r_um']==r];axs[1].semilogy([x['contact_angle_deg'] for x in rows],[x['force_over_R4_weight'] for x in rows],marker='o',label='Sphere radius '+str(r)+' um')
axs[1].axhline(1,color='gray',ls='--');axs[1].set(xlabel='Assumed contact angle (degrees)',ylabel='Bridge force / R4 grain weight',title='Water bridge scale at 50 C');axs[1].legend()
models=[x['model'] for x in W['cost']];axs[2].bar(models,[x['conditional_EAC_JPY']/1e6 for x in W['cost']],color=[colors[m] for m in models]);axs[2].axhline(19,color='#d06c35',ls='--',label='Assumed annual budget');axs[2].set(ylabel='Conditional EAC (million JPY/year)',title='Same grain count; unquoted 500 JPY/kg');axs[2].legend(fontsize=9)
fig.suptitle('Changing shape, wet forces and cost together',fontsize=15);fig.text(.5,.025,'Width is geometry only. Liquid bridge existence is assumed; crossed-wire wetting is not solved.\nCosts: 2,000 m2 x 0.45 m, 10 years, 8%, annual replacement 2% (not permitted environmental release). No new process cost included.',ha='center',fontsize=10);fig.tight_layout(rect=[0,.11,1,.94]);fig.savefig(H/'width_wet_cost.png',dpi=170);plt.close(fig)
# Show one balanced fixture and the normalized contact forces.
x=next(x for x in C['fixtures'] if x['model']=='C3' and x['pose_id']==3);f=next(f for f in x['force_cases'] if f['mu_top']==0 and f['mu_internal']==.6)['inner'];fig=plt.figure(figsize=(8,7));ax=fig.add_subplot(111,projection='3d')
objects=[(np.array(x['central_rotation']),np.zeros(3),'#0d8378',4)]+[(np.array(s['rotation']),np.array(s['center']),'#a8b5c6',2) for s in x['supports']]
for Q,c,color,lw in objects:
 for arc in arcs('C3'):
  ts=np.linspace(arc[2],arc[3],180);q=np.array([point(arc,t,.24,Q)+c for t in ts]);ax.plot(*q.T,color=color,lw=lw)
for j,(p,force) in enumerate(zip(x['points'],f['forces_normalized'])):
 p=np.array(p);v=np.array(force);v=v/max(1,np.linalg.norm(v))*.12;ax.quiver(*p,*v,color='#b34229',linewidth=2);ax.text(*p,str(j),color='#b34229')
ax.set(xlabel='x (mm)',ylabel='y (mm)',zlabel='z (mm)',title='C3 pose 3: three fixed supporting grains\nPlaten friction 0; internal friction assumed 0.6');ax.set_box_aspect([1,1,1]);ax.view_init(24,37);fig.text(.5,.025,'Central grain is free of an artificial clamp. Static force balance does not establish stiffness or stable packing.\nContact arrows are normalized for display; grey support grains are fixed by assumption.',ha='center',fontsize=9);fig.tight_layout(rect=[0,.08,1,1]);fig.savefig(H/'C3_fixture.png',dpi=170);plt.close(fig)
print('Rendered four scientific figures')
