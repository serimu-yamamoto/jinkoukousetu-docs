from pathlib import Path
import sys,json
P=Path(__file__).resolve().parent
local=P.parents[1]/'.research90/deps'
if local.exists():sys.path.insert(0,str(local))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
I=json.loads((P/'inputs.json').read_text(encoding='utf-8'));R=json.loads((P/'results.json').read_text(encoding='utf-8'))
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,ax=plt.subplots(1,2,figsize=(12,5.5),layout='constrained')
colors=['#187b8a','#cb7220','#6a54a3']
for h,color in zip(I['snow_normal_depths_m'],colors):
 for theta,style in [(0,'-'),(.1,'--')]:
  rows=[x for x in R['load_rows'] if x['h_m']==h and x['theta']==theta]
  ax[0].plot([x['c_required_Pa']/1000 for x in rows],[x['z_m']*1000 for x in rows],style,color=color,label=f'H={h:g} m; water={theta:g}')
ax[0].set(xlabel='Required additional stress c (kPa)',ylabel='Cut depth below artificial-bed surface (mm)',title='A. Snow + artificial material + retained water\nr = 0; assumed friction coefficient = 0.2')
ax[0].invert_yaxis();ax[0].legend(fontsize=8,loc='upper center',bbox_to_anchor=(.5,-.15),ncol=2);ax[0].grid(alpha=.2)
x=[0,1,2]
ax[1].plot(x,[y['ratio_R_over_D'] for y in R['peak_counterexample']],'o-',label='Assumed peak strength',color='#187b8a')
ax[1].plot(x,[y['ratio_R_over_D'] for y in R['residual_counterexample']],'s-',label='Assumed residual strength',color='#be4b4b')
ax[1].axhline(1.5,color='#555',linestyle='--',label='Diagnostic force ratio 1.5')
ax[1].axhline(1,color='#aaa',linestyle=':')
ax[1].set_xticks(x,['Snow / grain','Inside grain bed','Base / retention'])
ax[1].set(ylabel='Local resistance / driving stress',title='B. Strong interface can hide a weak interior\nH = 1 m; water = 0.1; r = 0.25',ylim=(0,2.6))
ax[1].legend(fontsize=8,loc='lower right');ax[1].grid(alpha=.2)
fig.suptitle('Winter load-path diagnostic: assumed inputs, no physical experiments',fontsize=14)
fig.savefig(P/'winter_load_path.png',dpi=160)
plt.close(fig)
fig,ax=plt.subplots(figsize=(7.5,4.5),layout='constrained')
ax.plot([x['surface_c_Pa']/1000 for x in R['surface_only_strength_sweep']],[x['minimum_ratio'] for x in R['surface_only_strength_sweep']],color='#be4b4b',lw=2)
ax.axhline(1.5,color='#555',ls='--',label='Diagnostic force ratio 1.5')
ax.set(xlabel='Additional strength at snow / grain interface (kPa)',ylabel='Minimum of the three resistance / driving ratios',ylim=(0,1.7),title='Strengthening only the top does not fix this interior failure\nSynthetic example; fixed internal residual c = 1 kPa')
ax.annotate(f'Plateau = {R["minimum_residual_ratio"]:.3f}',xy=(5,R['minimum_residual_ratio']),xytext=(4,1.05),arrowprops={'arrowstyle':'->'})
ax.grid(alpha=.2);ax.legend(loc='lower right')
fig.savefig(P/'surface_only_plateau.png',dpi=160)
plt.close(fig)
print('Rendered 2 diagnostic figures; no measurement data used.')
