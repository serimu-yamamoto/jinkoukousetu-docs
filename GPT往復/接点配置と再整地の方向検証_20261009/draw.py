"""Original figures of prescribed linear networks, not physical material images."""
import sys,json,csv
from pathlib import Path
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P.parents[1]/'.deps'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
R=json.loads((P/'results.json').read_text(encoding='utf-8'))
read=lambda name:list(csv.DictReader((P/name).open(encoding='utf-8')))
N=read('nodes.csv');E=read('edges_and_masks.csv');C=read('repair_curve.csv')
xyz=np.array([[float(r[a])*1000 for a in ['x_m','y_m','z_m']] for r in N])
plt.rcParams.update({'font.size':10,'figure.dpi':170,'svg.fonttype':'none'})
colors=['#237d98','#9b4c89','#bd7227','#3b9467']
def save(fig,name):
 fig.savefig(P/(name+'.png'));fig.savefig(P/(name+'.svg'));plt.close(fig)
fig,axs=plt.subplots(1,3,figsize=(12.5,5.3))
fig.subplots_adjust(top=.80,bottom=.18,left=.06,right=.985,wspace=.30)
for ax,key,label in zip(axs,['one_direction_restore','balanced_cluster_restore','four_direction_spread_restore'],['One orientation family','Balanced, centre-first','Four tilts, spread order']):
 for edge in E:
  if edge['crosses_cut']!='True':continue
  a,b=xyz[int(edge['node_i'])],xyz[int(edge['node_j'])];v=b-a
  ax.plot([a[0],b[0]],[a[1],b[1]],color='#dce2e5',lw=1,zorder=1)
  if edge[key]=='True':
   axis=0 if abs(v[0])>1e-10 else 1;idx=2*axis+(0 if v[axis]*v[2]>0 else 1)
   ax.plot([a[0],b[0]],[a[1],b[1]],color=colors[idx],lw=2.5,zorder=2)
 ax.set_title(label+'\n30 repaired links / 60 cut links',fontsize=11,pad=10);ax.set_xlabel('x [mm]');ax.set_ylabel('y [mm]');ax.set_aspect('equal');ax.grid(alpha=.12)
fig.legend(handles=[Line2D([0],[0],color=c,lw=3,label=l) for c,l in zip(colors,['x+ tilt','x- tilt','y+ tilt','y- tilt'])],loc='lower center',bbox_to_anchor=(.5,.02),ncol=4,frameon=False)
fig.suptitle('H66: interface links in xy projection; hypothetical network, not a material micrograph',fontsize=12,y=.985)
save(fig,'01_contact_layouts')
fig,axs=plt.subplots(1,2,figsize=(12.5,4.8),layout='constrained')
keys=['plane_cut','dispersed_loss_66','one_direction_restore','balanced_spread_restore','balanced_cluster_restore','four_direction_spread_restore']
labels=['Plane\ncut','Dispersed\nloss','One-family\nrepair','Two-family\nspread','Balanced\ncentre-first','Four-tilt\nspread']
x=np.arange(len(keys));w=.25
for j,(field,lab,col) in enumerate(zip(['Kx_ratio','Ky_ratio','Kz_ratio'],['x shear','y shear','z normal'],['#237d98','#bd7227','#3b9467'])):
 vals=[next(r for r in R['summary'] if r['case']==key)[field] for key in keys]
 axs[0].bar(x+(j-1)*w,vals,w,label=lab,color=col)
axs[0].set_xticks(x,labels,fontsize=8);axs[0].set_ylim(0,1.08);axs[0].set_ylabel('Stiffness / intact reference');axs[0].set_title('Same link count does not mean same support');axs[0].legend(fontsize=8);axs[0].grid(axis='y',alpha=.15)
for key,label,col in [('one_direction','One family','#bd7227'),('balanced_spread','Two-family spread','#9b4c89'),('four_direction_spread','Four-tilt spread','#237d98')]:
 rows=[r for r in C if r['case']==key]
 axs[1].plot([int(r['restored']) for r in rows],[float(r['minimum_xy_shear_ratio']) for r in rows],'-o',color=col,label=label)
axs[1].set_title('Repair must recover weak shear directions');axs[1].set_xlabel('Restored interface links');axs[1].set_ylabel('Weakest xy stiffness / intact reference');axs[1].set_ylim(-.03,1.08);axs[1].legend(fontsize=8);axs[1].grid(alpha=.15)
fig.suptitle('Linear, stress-free springs with clamped top/bottom planes; no friction or fracture evolution')
save(fig,'02_support_and_repair')
fig,axs=plt.subplots(1,3,figsize=(13,4.8),layout='constrained')
for key,label,col in [('balanced_spread_restore','Two-family spread','#9b4c89'),('balanced_cluster_restore','Balanced centre-first','#3b9467'),('four_direction_spread_restore','Four-tilt spread','#237d98')]:
 vals=[r['minimum_xy_shear_ratio'] for r in R['local_damage'] if r['layout']==key]
 base=next(r['minimum_xy_shear_ratio'] for r in R['summary'] if r['case']==key)
 axs[0].plot(range(4),[base]+vals,'-o',label=label,color=col)
axs[0].set_xticks(range(4),['Before','Centre','Corner 1','Corner 2'],fontsize=8);axs[0].set_ylabel('Weakest xy stiffness / intact reference');axs[0].set_title('Local damage: no universal spread winner');axs[0].legend(fontsize=7);axs[0].set_ylim(0,1);axs[0].grid(alpha=.15)
for key,label,col in [('one_direction_restore','One family','#bd7227'),('four_direction_spread_restore','Four tilts','#237d98')]:
 rows=[r for r in R['jitter'] if r['case']==key]
 axs[1].plot([100*r['jitter_fraction'] for r in rows],[r['Kx_ratio'] for r in rows],'-o',label=label,color=col)
axs[1].set_xlabel('Coordinate jitter bound / spacing [%]');axs[1].set_ylabel('x shear stiffness / intact reference');axs[1].set_title('Small geometric noise does not fix bias');axs[1].set_ylim(0,1);axs[1].legend(fontsize=8);axs[1].grid(alpha=.15)
for om,col in [(0,'#237d98'),(500000,'#bd7227')]:
 rows=[r for r in R['cost'] if r['added_annual_OandM_JPY']==om]
 axs[2].plot([100*r['assumed_avoidance_fraction'] for r in rows],[r['max_extra_capex_JPY']/1e6 for r in rows],'-o',label=f'Added O&M {om/1e6:.1f} M JPY/y',color=col)
axs[2].set_title('Hypothetical investment ceiling');axs[2].set_xlabel('Assumed replacement avoidance [%]');axs[2].set_ylabel('Extra capex ceiling [M JPY]');axs[2].legend(fontsize=8);axs[2].grid(alpha=.15)
fig.suptitle('Sensitivity and cost bounds only: no measured repair rate, life, price quote or physical trials')
save(fig,'03_damage_jitter_cost')
print('Three original figure pairs saved')
