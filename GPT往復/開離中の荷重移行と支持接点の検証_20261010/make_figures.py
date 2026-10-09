from reproduce import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
M=json.loads((D/'results.json').read_text(encoding='utf-8'));L=json.loads((D/'load_sharing_results.json').read_text(encoding='utf-8'))
plt.rcParams.update({'font.size':10,'axes.grid':True,'grid.alpha':.22,'figure.facecolor':'white'})
fig,axs=plt.subplots(1,3,figsize=(13.5,4),layout='constrained')
# Bottom contact coordinates and fixed top load application point.
c=next(f for f in F if f['model']=='C3' and f['pose_id']==3);pp=np.array(c['points'])*1000
axs[0].scatter(pp[1:,0],pp[1:,1],s=65,label='Archived supports')
for j in [1,2,3]:axs[0].annotate(str(j),(pp[j,0]+5,pp[j,1]+5))
p4=np.array(M['ideal_helper_point_mm'])*1000
axs[0].scatter(*p4[:2],marker='s',s=70,label='Ideal helper only')
axs[0].scatter(*pp[0,:2],marker='x',s=80,label='Top load point')
axs[0].set(xlabel='x (um)',ylabel='y (um)',title='C3 pose 3: plan view');axs[0].axis('equal');axs[0].legend(fontsize=8)
muvals=[.1,.3,.6,1];rmvals=[None,1,2,3];matrix=np.array([[int(next(r for r in M['helper_cases'] if r['mu']==mu and r['removed_support']==rm and r['q']==0)['inner']['success']) for mu in muvals] for rm in rmvals])
axs[1].imshow(matrix,cmap='RdYlGn',vmin=0,vmax=1,aspect='auto');axs[1].grid(False)
axs[1].set(xticks=range(4),xticklabels=muvals,yticks=range(4),yticklabels=['All retained','Remove 1','Remove 2','Remove 3'],xlabel='Assumed internal friction',title='One ideal helper, vertical load')
for i in range(4):
 for j in range(4):axs[1].text(j,i,'Feasible' if matrix[i,j] else 'No balance',ha='center',va='center',fontsize=8)
mom=[r for r in M['two_support_moment'] if r['model']=='C3' and r['pose']==3 and r['q']==0]
axs[2].bar([str(r['removed_support']) for r in mom],[abs(r['axis_moment_per_NR']) for r in mom],color='#996633')
axs[2].set(xlabel='Removed support',ylabel='Unbalanced moment / (N R)',title='Two-support torque\nthat contact forces cannot balance')
fig.suptitle('Fixed-geometry diagnostics; added neighbor not built; no 50 C validation',fontsize=12)
fig.savefig(D/'contact_transfer.png',dpi=160);plt.close(fig)
fig,axs=plt.subplots(2,2,figsize=(12,8),layout='constrained')
colors={'intact':'#555555','dispersed':'#1b9e77','central_block':'#d95f02','edge_block':'#7570b3'}
for r in L['cases']:
 if r['lam']==1 and r['pattern']!='edge_block':
  x=np.arange(25);color=colors[r['pattern']]
  axs[0,0].plot(x,r['displacement'],'o-',label=r['pattern'],color=color,markersize=3)
  axs[0,1].plot(x,r['reactions'],'o-',label=r['pattern'],color=color,markersize=3)
axs[0,0].set(xlabel='Support location / d',ylabel='Nodal displacement / (q d / k)',title='Six unavailable supports, same count; lambda=1')
axs[0,1].set(xlabel='Support location / d',ylabel='Normal reaction / (q d)',title='Load transferred to remaining supports')
for p,color in colors.items():
 rows=[r for r in L['cases'] if r['pattern']==p]
 axs[1,0].loglog([r['lam'] for r in rows],[r['max_support_node_displacement'] for r in rows],'o-',color=color,label=p)
 axs[1,1].semilogx([r['lam'] for r in rows],[r['max_support_force'] for r in rows],'o-',color=color,label=p)
axs[1,0].set(xlabel='lambda = EI / (k d^3)',ylabel='Max nodal displacement / (q d / k)',title='Static displacement sensitivity; no calibrated units')
axs[1,1].set(xlabel='lambda = EI / (k d^3)',ylabel='Peak reaction / (q d)',title='Continuous missing region concentrates load')
for ax in axs.flat:ax.legend(fontsize=8)
fig.suptitle('Unilateral-spring beam surrogate; not measured ski comfort or snow performance',fontsize=13)
fig.savefig(D/'distributed_release.png',dpi=160);plt.close(fig)
import scipy
(D/'runtime_versions.json').write_text(json.dumps({'python':sys.version.split()[0],'numpy':np.__version__,'scipy':scipy.__version__,'matplotlib':matplotlib.__version__},indent=2)+'\n',encoding='utf-8',newline='\n')
print('Two figures generated')
