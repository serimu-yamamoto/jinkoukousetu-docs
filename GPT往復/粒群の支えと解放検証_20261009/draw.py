"""Original plots; data attribution in report and sources.json. Not ski-performance predictions."""
import sys,csv,json,math
from pathlib import Path
P=Path(__file__).resolve().parent
extra=P.parents[1]/'.deps'
if extra.is_dir():sys.path.insert(0,str(extra))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=json.loads((P/'results.json').read_text(encoding='utf8'))
D=list(csv.DictReader((P/'derived_snow_rows.csv').open(encoding='utf8')))
plt.rcParams.update({'font.size':11,'svg.hashsalt':'H49','axes.spines.top':False,'axes.spines.right':False})
C={'FC&DH':'#ba713e','DF&RG':'#2874a6','SH':'#429075'}
def save(fig,name):
 fig.savefig(P/(name+'.png'),dpi=170,bbox_inches='tight',metadata={'Software':'H49 original plot'})
 fig.savefig(P/(name+'.svg'),bbox_inches='tight',metadata={'Date':None})
 s=(P/(name+'.svg')).read_text(encoding='utf8');(P/(name+'.svg')).write_text('\n'.join(z.rstrip() for z in s.splitlines())+'\n',encoding='utf8',newline='\n');plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(12.4,5.2),layout='constrained')
for cat,col in C.items():
 rr=[r for r in D if r['category']==cat and r['E_ROI01_MPa']]
 E=[float(r['E_ROI01_MPa']) for r in rr];S=[float(r['strength_kPa']) for r in rr];phi=[float(r['phi']) for r in rr]
 axs[0].loglog(E,S,'o',color=col,label=f'{cat} (n={len(rr)})',alpha=.8)
 f=R['data_summary'][cat]['fit_primary'];xx=[min(E)*(max(E)/min(E))**(i/100) for i in range(101)];yy=[math.exp(f['log_intercept'])*v**f['log_OLS_exponent'] for v in xx];axs[0].loglog(xx,yy,color=col,lw=1)
 axs[1].semilogy(phi,E,'o',color=col,alpha=.8)
axs[0].set(xlabel='Effective modulus, ROI 01 (MPa)',ylabel='Parent mean compressive strength (kPa)',title='A | Strength and stiffness vary together differently');axs[0].legend(fontsize=9)
axs[1].set(xlabel='Voxel-based ice volume fraction',ylabel='Effective modulus, ROI 01 (MPa)',title='B | Density alone cannot specify the response')
for id,offset in [('408',(35,-5)),('415',(35,25))]:
 r=next(x for x in D if x['ID']==id);axs[1].annotate('ID '+id,(float(r['phi']),float(r['E_ROI01_MPa'])),xytext=offset,textcoords='offset points',arrowprops={'arrowstyle':'->'},fontsize=10)
fig.suptitle('Public weak-snow-layer measurements | Independent descriptive reanalysis',fontsize=16)
fig.supxlabel('Schottner et al., EnviDat 648 (CC BY 4.0). 62 complete parent rows. Not groomed fresh-snow acceptance targets.',fontsize=10)
save(fig,'01_public_snow_data')
curves=list(csv.DictReader((P/'link_curves.csv').open(encoding='utf8')))
fig,axs=plt.subplots(2,2,figsize=(12.4,8.8),layout='constrained')
colors=['#256f91','#ba6d38','#448d70']
for w,col in zip([.002,.02,.1],colors):
 rr=[r for r in curves if float(r['activation_width'])==w and float(r['strain'])<=.22]
 axs[0,0].plot([float(r['strain']) for r in rr],[float(r['capped_stress_Pa'])/1000 for r in rr],color=col,label=f'Release, width {w:g}')
 axs[0,0].plot([float(r['strain']) for r in rr],[float(r['uncapped_stress_Pa'])/1000 for r in rr],color=col,ls='--',lw=1)
axs[0,0].set(xlabel='Model shear strain',ylabel='Link stress budget (kPa)',title='A | Dashed: links remain engaged; solid: release',ylim=(0,16));axs[0,0].legend(fontsize=8)
for h,col in zip([.001,.005,.02],colors):
 rows=[r for r in R['ensemble'] if r['release_force_N']==.003 and r['residual_fraction']==.05]
 axs[0,1].plot([r['activation_width'] for r in rows],[1000*r['peak_to_fullrelease_m'][str(h)] for r in rows],'o-',color=col,label=f'Active band {1000*h:g} mm')
axs[0,1].set(xlabel='Activation-window width (strain)',ylabel='Peak to complete release (mm)',title='B | Local band thickness changes release distance');axs[0,1].legend(fontsize=9)
for c,col in zip([.3,.5,1],colors):
 rr=[r for r in R['winter'] if r['projection']==c]
 axs[1,0].plot([r['sharing_links'] for r in rr],[1000*r['minimum_link_force_N'] for r in rr],'o-',color=col,label=f'Force projection {c:g}')
axs[1,0].axhline(3,color='#444',ls='--',lw=1);axs[1,0].set(xlabel='Winter load-sharing links (hypothesis)',ylabel='Minimum force per link (mN)',title='C | Weak summer clips can fail winter retention',xticks=[2,3,6]);axs[1,0].legend(fontsize=9)
for chi,col in zip([.01,.1,1],colors):
 rr=[r for r in R['wear'] if r['exposure_fraction']==chi]
 axs[1,1].loglog([r['damaged_material_fraction_per_exposure']*100 for r in rr],[r['steady_replacement_fraction_year']*100 for r in rr],'o-',color=col,label=f'Exposed bed fraction {chi:g}')
axs[1,1].axhline(2,color='#444',ls='--',lw=1);axs[1,1].set(xlabel='Damaged mass / exposed mass per event (%)',ylabel='Annual replacement / bed mass (%)',title='D | Hypothetical 120 damage events per year');axs[1,1].legend(fontsize=9)
fig.suptitle('H49 | Controlled release must coexist with winter support and low damage',fontsize=16)
fig.supxlabel('All curves here are uncalibrated hypotheses. Fc = 3 mN for A/B, residual fraction 0.05; no measured success rate.',fontsize=10)
save(fig,'02_release_winter_cost')
print('Two original figures generated (PNG/SVG).')
