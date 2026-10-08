from pathlib import Path
import sys,json,math
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P.parents[1]/'.deps'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.grid':True,'grid.alpha':.22,'figure.dpi':160})
R=json.loads((P/'results.json').read_text())
fig,ax=plt.subplots(1,2,figsize=(12,4.8),layout='constrained')
colors=['#1d6996','#0f8554','#d95f02']
for k,color in zip([3e5,1e6,5e6],colors):
 c=[q for q in R['normal_cases'] if q['K1_Pa_m']==k and q['v_m_s']==20]
 ax[0].semilogx([q['tau_s'] for q in c],[q['delta_mu'] for q in c],'-o',color=color,label=f'K1 = {k/1e6:g} MPa/m')
 ax[1].loglog([q['tau_s'] for q in c],[q['max_sink_mm'] for q in c],'-o',color=color)
ax[0].axhline(.01,color='#555',ls='--',label='Illustrative component budget 0.01')
ax[0].set(xlabel='Relaxation time (s)',ylabel='Normal-deformation contribution to COF',title='Low normal loss does not establish low total friction')
ax[0].legend(fontsize=8,loc='best');ax[0].set_ylim(0,.011)
ax[1].set(xlabel='Relaxation time (s)',ylabel='Maximum sinkage during one pass (mm)',title='Sinkage must be assessed independently')
fig.suptitle('H32 prescribed-pressure model: 400 N, 70 mm x 1.6 m, 20 m/s\nHypothetical stiffness and relaxation; no artificial-material measurements',fontsize=12)
fig.savefig(P/'figure1_normal_loss_and_sinkage.png');plt.close(fig)
fig,ax=plt.subplots(1,2,figsize=(12,4.8),layout='constrained')
# Release curves measured from peak; logarithmic slip axis makes short and long tails visible.
xx=[10**(-7+5*i/400) for i in range(401)]
for d,color in zip([1e-5,1e-4,1e-3],colors):
 y=[max(0,250*(1-x/d)) for x in xx]
 ax[0].semilogx([x*1e6 for x in xx],y,color=color,label=f'Release distance {d*1e6:g} um; no residual')
d=1e-5
ax[0].semilogx([x*1e6 for x in xx],[25+max(0,225*(1-x/d)) for x in xx],'--',color='#a1387a',label='10 um; 25 N residual')
ax[0].set(xlabel='Additional slip after peak (um)',ylabel='Force on illustrative 0.005 m2 plane (N)',title='Same peak support, different release and tail')
ax[0].legend(fontsize=8);ax[0].set_xlim(.1,10000);ax[0].set_ylim(0,265)
c=[q for q in R['repeat_cases'] if q['period_s']==2]
ax[1].semilogx([q['tau_s'] for q in c],[q['first_max_sink_mm'] for q in c],'-o',color='#1d6996',label='First pass')
ax[1].semilogx([q['tau_s'] for q in c],[q['steady_max_sink_mm'] for q in c],'-s',color='#d95f02',label='Repeated-pulse steady state')
ax[1].set(xlabel='Relaxation time (s)',ylabel='Maximum sinkage (mm)',title='Slow recovery can leave accumulated sinkage')
ax[1].set_yscale('log');ax[1].legend(fontsize=8)
fig.suptitle('H32 separate shear release from normal load history\nIllustrative laws only; no claim of fracture toughness or skiing performance',fontsize=12)
fig.savefig(P/'figure2_release_and_repetition.png');plt.close(fig)
print('Saved 2 independent model figures; no third-party figures reused.')
