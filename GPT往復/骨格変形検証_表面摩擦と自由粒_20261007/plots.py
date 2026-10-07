import json
from elastic_free import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
B=json.loads((H/'brace_results.json').read_text(encoding='utf-8'));E=json.loads((H/'elastic_results.json').read_text(encoding='utf-8'));C=json.loads((H/'economics_results.json').read_text(encoding='utf-8'))
fig=plt.figure(figsize=(12,4))
for i,kind in enumerate([None,'Y3','T6']):
 ax=fig.add_subplot(1,3,i+1,projection='3d')
 for u,v,lo,hi in grain_arcs('C3'):
  t=np.linspace(lo,hi,101);p=.24*(np.cos(t)[:,None]*u+np.sin(t)[:,None]*v);ax.plot(*p.T,color='#245b82',lw=3)
 if kind:
  for p,q in brace_segments(kind):ax.plot(*np.array([p,q]).T,color='#df8126',lw=2)
 ax.set(xlim=(-.27,.27),ylim=(-.27,.27),zlim=(-.27,.27),xlabel='x (mm)',ylabel='y (mm)',zlabel='z (mm)',title='C3'+(' + '+kind if kind else ' (unbraced)'));ax.set_box_aspect((1,1,1));ax.view_init(24,35)
fig.suptitle('Added internal members: centre spokes vs tip-to-back ties (centreline schematic)');fig.tight_layout();fig.savefig(H/'01_structures.png',dpi=180);plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(11,4.8))
for kind,col in [('Y3','#245b82'),('T6','#df8126')]:
 rows=[x for x in B['cases'] if x['brace']==kind];d=[x['brace_radius_mm']*2000 for x in rows];axs[0].plot(d,[x['response']['required_uniform_E_for_diagnostic_MPa']/1000 for x in rows],'-o',label=kind,color=col);axs[1].plot(d,[x['clearance']['robust_margin_lower_mm']*1000 for x in rows],'-o',label=kind,color=col)
axs[0].axhline(6.709881621,color='gray',ls='--',label='Unbraced C3');axs[0].set(xlabel='Brace diameter (micrometre)',ylabel='Required uniform E (GPa)',title='Prescribed forces, pose 3; diagnostic only');axs[0].legend();axs[1].axhline(0,color='black',ls='--');axs[1].set(xlabel='Brace diameter (micrometre)',ylabel='New-member clearance margin (micrometre)',title='Saved four-grain fixture; includes height bracket');axs[1].legend();fig.suptitle('Stiffness gain competes with geometric clearance');fig.tight_layout();fig.savefig(H/'02_stiffness_clearance.png',dpi=180);plt.close(fig)
fig,ax=plt.subplots(figsize=(10,5));names=['C3','R4','S3','C3-T6-20','C3-T6-28','C3-T6-36','C3-T6-44'];rows=[next(x for x in C['cases'] if x['name']==name and x['density_kg_m3']==960) for name in names];bars=ax.bar(names,[x['conditional_EAC_JPY']/1e6 for x in rows],color=['#245b82']*3+['#df8126']*3+['#a3a3a3']);ax.axhline(19,color='firebrick',ls='--',label='Assumed annual budget');ax.set(ylabel='Equivalent annual cost (million JPY, pretax)',title='2,000 m2 pilot / 450 mm / 500 JPY per kg / 960 kg per m3');ax.legend();ax.bar_label(bars,fmt='%.2f',padding=3);ax.set_ylim(0,26);fig.text(.5,.01,'Same grain count; unquoted prices. Grey: no clearance margin. No performance certification.',ha='center',fontsize=9);fig.tight_layout(rect=[0,.04,1,1]);fig.savefig(H/'03_cost.png',dpi=180);plt.close(fig)
print('3 figures saved')
