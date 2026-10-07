from allocation import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
A=json.loads((H/'allocation_results.json').read_text(encoding='utf-8'));M=json.loads((H/'minimax_results.json').read_text(encoding='utf-8'));K=json.loads((H/'contact_audit_results.json').read_text(encoding='utf-8'));S=json.loads((H/'seat_requirements.json').read_text(encoding='utf-8'));old=json.loads((H.parent/'骨格変形検証_表面摩擦と自由粒_20261007/elastic_results.json').read_text(encoding='utf-8'));br=json.loads((H.parent/'骨格変形検証_表面摩擦と自由粒_20261007/brace_results.json').read_text(encoding='utf-8'))
names=['R4','C3','C3-T6-28','S3'];saved=[];energy=[];minimax=[];labels=[]
for name in names:
 mt=0 if name.startswith('C3') else .1;labels.append(name+'\nplate mu='+str(mt))
 if name=='C3-T6-28':r=next(q for q in br['cases'] if q['brace']=='T6' and q['brace_radius_mm']==.014)['response']
 else:r=next(q for q in old['cases'] if q['model']==name and q['pose_id']==3 and q['mu_top']==mt and q['mu_internal']==.6)['response']
 saved.append(r['required_uniform_E_for_diagnostic_MPa']/1000)
 x=next(q for q in A['fixtures'] if q['name']==name and q['pose_id']==3);r=next(q for q in x['energy_relaxations'] if q['mu_top']==mt and q['mu_internal']==.6);energy.append(r['response']['required_uniform_E_for_diagnostic_MPa']/1000)
 x=next(q for q in M['fixtures'] if q['name']==name and q['pose_id']==3);r=next(q for q in x['cases'] if q['mu_top']==mt and q['mu_internal']==.6);minimax.append(r['dense_response']['required_uniform_E_for_diagnostic_MPa']/1000)
fig,ax=plt.subplots(figsize=(10,5));x=np.arange(4);w=.25
for dx,vals,col,label in [(-w,saved,'#9fa7ad','Saved force witness'),(0,energy,'#285e82','Minimum energy'),(w,minimax,'#d17b26','Minimum diagnostic')]:bars=ax.bar(x+dx,vals,w,label=label,color=col);ax.bar_label(bars,fmt='%.2f',padding=3,fontsize=9)
ax.set(xticks=x,xticklabels=labels,ylabel='Conditional required uniform E (GPa)',title='Pose 3 / 0.9 mN / internal mu=0.6 / fixed geometry');ax.legend();ax.set_ylim(0,8);fig.text(.5,.01,'Static force choices only. Large-deformation values are diagnostics, not physical displacements.',ha='center',fontsize=9);fig.tight_layout(rect=[0,.04,1,1]);fig.savefig(H/'01_force_allocation.png',dpi=170);plt.close(fig)
fig,ax=plt.subplots(figsize=(10,5));groups=[('C3',3),('C3-T6-28',3),('S3',0),('S3',7)];x=np.arange(4)
for dx,method,col in [(-.18,'energy','#285e82'),(.18,'minimax','#d17b26')]:
 vals=[next(q for q in K['kinematic_checks'] if q['name']==name and q['pose_id']==pose and q['method']==method)['kinematics']['max_mismatch_mm']*1000 for name,pose in groups];bars=ax.bar(x+dx,vals,.36,label=method,color=col);ax.bar_label(bars,fmt='%.4g',padding=3,fontsize=9)
ax.set(xticks=x,xticklabels=[name+'\npose '+str(pose) for name,pose in groups],yscale='log',ylim=(1e-5,10),ylabel='Residual contact displacement (micrometre)',title='At 9 micronewton: allow sliding opposite friction at active contacts');ax.legend();fig.text(.5,.01,'A residual tests this force witness at these fixed contacts; it does not exclude another equilibrium.',ha='center',fontsize=9);fig.tight_layout(rect=[0,.04,1,1]);fig.savefig(H/'02_kinematic_consistency.png',dpi=170);plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(11,5));rows=S['designs'];areas=[max(v['minimum_nominal_area_um2'] for v in q['sizes']) for q in rows];bars=axs[0].bar([q['name'] for q in rows],areas,color='#285e82');axs[0].bar_label(bars,fmt='%.1f',padding=3);axs[0].axhline(400,color='#d17b26',ls='--',label='20 x 20 micrometre nominal area');axs[0].set(ylabel='Minimum nominal bearing area (square micrometre)',title='Missing-force budget / E=300 MPa / strain=1%');axs[0].legend(fontsize=8);axs[0].tick_params(axis='x',rotation=15)
axs[1].axis('off');axs[1].text(.02,.93,'Short bearing seat: design envelope',weight='bold',fontsize=12);axs[1].text(.02,.77,'20 x 20 micrometre area\n20 micrometre compression path\n6 assumed members per grain',fontsize=11);axs[1].text(.02,.52,'Added material volume: 0.000048 mm3 / grain\nAt unchanged grain count and 960 kg/m3:\n2,000 m2 pilot, 450 mm depth, 500 JPY/kg\nAdded material: about 0.56 million JPY',fontsize=10);axs[1].text(.02,.18,'Not included: mating shape, connection to frame,\nentry, release, hidden protection, mold or tooling.\nThis is NOT a validated holding mechanism.',fontsize=10,color='#9b3e28');fig.tight_layout();fig.savefig(H/'03_bearing_envelope.png',dpi=170);plt.close(fig);print('3 figures saved')
