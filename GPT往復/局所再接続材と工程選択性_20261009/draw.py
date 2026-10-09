"""Original conceptual figures; no measured performance data."""
import sys,json,math
from pathlib import Path
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P.parents[1]/'.deps'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, FancyArrowPatch, Arc
R=json.loads((P/'results.json').read_text(encoding='utf-8'))
plt.rcParams.update({'font.size':10,'figure.dpi':160,'svg.fonttype':'none'})
fig,ax=plt.subplots(1,2,figsize=(12,4.6),layout='constrained')
names=['Full 5 um coat','Patches: 1 MPa, q=0.25','Ideal: 10 MPa, q=1']
vals=[R['full_5um_coating_dry_kg'],R['reference']['installed_dry_kg'],35.1]
ax[0].barh(names,vals,color=['#8a969d','#197c80','#aecbca']);ax[0].set_xscale('log');ax[0].invert_yaxis();ax[0].set_xlabel('Installed dry connector mass [kg, log]')
for i,v in enumerate(vals):ax[0].text(v*1.08,i,f'{v:,.1f}',va='center')
ax[0].set_xlim(10,130000);ax[0].set_title('A. Quantities under assumed joint strength')
x=[r['groom_s'] for r in R['kinetics']];y=[r['required_rate_ratio'] for r in R['kinetics']]
ax[1].loglog(x,y,'o-',color='#bb603b');ax[1].grid(alpha=.25);ax[1].set_xlabel('Allowed intended contact time [s]');ax[1].set_ylabel('Required k(intended) / k(unwanted)');ax[1].set_title('B. Same temperature is not a selective switch')
for a,b in zip(x,y):ax[1].annotate(f'{b:,.0f}',(a,b),xytext=(4,6),textcoords='offset points',fontsize=8)
fig.suptitle('H64 screening: 2,000 m2 x 0.45 m; no physical trials',fontsize=13)
fig.text(.53,-.095,'Assumed exponential recovery; h >= 0.8 at grooming,\nh <= 0.1 at unwanted contacts held for 5 h.',fontsize=8)
for ext in ['png','svg']:fig.savefig(P/('quantity_and_selectivity.'+ext),bbox_inches='tight')
plt.close(fig)
fig,axs=plt.subplots(1,3,figsize=(13,4.4),layout='constrained')
for a in axs:a.set_xlim(0,10);a.set_ylim(0,8);a.set_aspect('equal');a.axis('off')
a=axs[0];a.add_patch(Rectangle((.4,6.4),9.2,.5,facecolor='#abb3ba'));a.text(5,7.2,'Ski base / edge',ha='center')
for x in [2.7,7.3]:
    a.add_patch(Arc((x,3.8),3.8,3.8,theta1=45,theta2=315,lw=7,color='#197c80'))
    a.plot([x-1.9,x],[3.8,3.8],lw=5,color='#197c80')
    a.add_patch(Circle((x,3.8),.3,facecolor='#bb603b'))
a.annotate('Recessed repair sites',xy=(2.7,3.8),xytext=(.4,.6),arrowprops={'arrowstyle':'->'},fontsize=9)
a.text(5,5.7,'Open support skeleton',ha='center',fontsize=9);a.set_title('H64-M: repair within a grain')
a=axs[1]
a.plot([.7,3.5,4.1],[5,5,3.9],color='#197c80',lw=12);a.plot([9.3,6.5,5.9],[3,3,4.1],color='#197c80',lw=12)
a.add_patch(Rectangle((4.15,3.7),.7,.6,facecolor='#bb603b'));a.add_patch(Rectangle((5.15,3.7),.7,.6,facecolor='#bb603b'))
a.annotate('',xy=(4.95,4),xytext=(4.55,4),arrowprops={'arrowstyle':'->'});a.annotate('',xy=(5.05,4),xytext=(5.45,4),arrowprops={'arrowstyle':'->'})
a.text(5,6.1,'Alignment + moisture + dwell',ha='center',fontsize=9);a.text(5,1.1,'Fracture energy and tail length\nmust match snow, not just strength.',ha='center',fontsize=9);a.set_title('H64-P: paired internal patches')
a=axs[2]
for y,txt,col in [(6.2,'1. Dry / wet 50 C joint test','#197c80'),(4.5,'2. Snow-reference edge + glide','#197c80'),(2.8,'3. Rain recovery + winter bond','#197c80'),(1.1,'4. Scale only after measured gates','#bb603b')]:
    a.add_patch(Rectangle((.4,y-.5),9.2,1,facecolor=col,alpha=.13));a.text(5,y,txt,ha='center',va='center',fontsize=9)
a.set_title('Decision gates before full-course build')
fig.suptitle('Design hypotheses: shielding, manufacture and durability are unproven',fontsize=13)
fig.text(.05,-.01,'Not to scale. Protein beta-sheet nanostructure is not a snow-shaped grain. No exposed fixed mat is proposed.',fontsize=9)
for ext in ['png','svg']:fig.savefig(P/('contact_concepts.'+ext),bbox_inches='tight')
plt.close(fig)
print('2 original figures, PNG + SVG; uncalibrated screening data only')
