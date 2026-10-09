"""Original diagnostic plots from assumed model; not empirical results."""
import sys,json,csv
from pathlib import Path
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P.parents[1]/'.deps'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=json.loads((P/'results.json').read_text(encoding='utf-8'))
C=list(csv.DictReader((P/'force_paths.csv').open(encoding='utf-8')))
plt.rcParams.update({'font.size':10,'figure.dpi':160,'svg.fonttype':'none'})
F=R['force_reference_N'];x=[float(c['opening_um']) for c in C]
fig,axs=plt.subplots(1,3,figsize=(13,4.5),layout='constrained')
for L,color in [(1,'#1e8486'),(10,'#c3753e'),(50,'#606b95')]:
    d0=L/10;df=20
    xx=[0,d0,df,25];ff=[0,F*1000,0,0]
    axs[0].plot(xx,ff,label=f'Length {L} um',color=color)
axs[0].set_title('A. Thinner is stiffer, same final opening');axs[0].legend(fontsize=8)
axs[1].plot(x,[float(c['total_stays_N'])*1000 for c in C],color='#b54b44',label='Mechanical path stays engaged')
axs[1].plot(x,[float(c['chemical_N'])*1000 for c in C],color='#1e8486',label='Chemical path alone');axs[1].set_title('B. Mechanical support can prevent release');axs[1].legend(fontsize=8)
axs[2].plot(x,[float(c['total_releases_N'])*1000 for c in C],color='#1e8486',label='Prescribed synchronized release')
axs[2].plot(x,[float(c['chemical_N'])*1000 for c in C],color='#c3753e',ls='--',label='Residual chemical tail')
axs[2].set_title('C. Required trajectory, mechanism unproven');axs[2].legend(fontsize=8)
for a in axs:a.set_xlabel('Local opening [um]');a.set_ylabel('Force [mN]');a.grid(alpha=.2);a.set_xlim(0,25)
fig.suptitle('H65: assumed 50 C parameters, not measured protein or snow',fontsize=13)
for ext in ['png','svg']:fig.savefig(P/('force_and_release.'+ext),bbox_inches='tight')
plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(11.5,4.7),layout='constrained')
for K,color in [(50,'#b54b44'),(500,'#c3753e'),(5000,'#1e8486')]:
    xx=[0,1+F/K*1e6,20];yy=[0,F*1000,0]
    axs[0].plot(xx,yy,'o-',color=color,label=f'Fixture K={K} N/m')
    axs[0].annotate('',xy=((xx[1]+xx[2])/2,(yy[1]+yy[2])/2),xytext=(xx[1],yy[1]),arrowprops={'arrowstyle':'->','color':color})
axs[0].set_title('D. Soft fixtures create snap-back');axs[0].set_xlabel('Crosshead displacement u [um]');axs[0].set_ylabel('Force [mN]');axs[0].legend(fontsize=8);axs[0].grid(alpha=.2)
axs[0].text(.03,.54,'u = local opening + F / K\nFolded branch is not stable\nunder crosshead displacement control.',transform=axs[0].transAxes,fontsize=8,bbox={'facecolor':'white','alpha':.9,'edgecolor':'none'})
ll=[r['length_um'] for r in R['thickness']];mass=[r['mass_kg'] for r in R['thickness']];beta=[r['fraction_if_parallel_100N_m']*100 for r in R['thickness']]
axs[1].loglog(ll,mass,'o-',color='#1e8486');axs[1].set_xlabel('Connector length [um]');axs[1].set_ylabel('Installed connector mass [kg]',color='#1e8486');axs[1].set_title('E. Less mass, more initial load fraction')
a2=axs[1].twinx();a2.semilogx(ll,beta,'s--',color='#c3753e');a2.set_ylabel('Chemical load fraction [%]',color='#c3753e');a2.set_ylim(85,101);axs[1].grid(alpha=.2)
fig.suptitle('Assumed sigma=1 MPa, E=10 MPa, G=10 J/m2; no physical trials',fontsize=12)
for ext in ['png','svg']:fig.savefig(P/('fixture_and_thickness.'+ext),bbox_inches='tight')
plt.close(fig)
print('2 original figures rendered, PNG+SVG')
