"""Added internal braces: compare prescribed balanced contact loads.
Clearance audit of all new member pairs; no inference of capture or bed performance.
"""
import json,math,heapq,itertools
from elastic_free import H,np,build,evaluate,grain_arcs,brace_segments

def point_segment(p,a,b):
 v=b-a;t=np.clip((p-a)@v/(v@v),0,1);return float(np.linalg.norm(p-a-t*v))
def segment_segment(a,b,c,d):
 u=b-a;v=d-c;w=a-c;D=(u@u)*(v@v)-(u@v)**2;candidates=[point_segment(a,c,d),point_segment(b,c,d),point_segment(c,a,b),point_segment(d,a,b)]
 if D>1e-25:
  s=((u@v)*(v@w)-(v@v)*(u@w))/D;t=((u@u)*(v@w)-(u@v)*(u@w))/D
  if 0<=s<=1 and 0<=t<=1:candidates.append(float(np.linalg.norm(w+s*u-t*v)))
 return min(candidates)
def segment_arc(a,b,arc,Q,center,R=.24,tol=2e-6):
 u,v,lo,hi=arc;heap=[];best=math.inf;count=0
 def add(l,h):
  nonlocal best,count
  t=(l+h)/2;p=(R*(math.cos(t)*u+math.sin(t)*v))@Q.T+center;dd=point_segment(p,a,b);best=min(best,dd);cover=2*R*math.sin((h-l)/4);heapq.heappush(heap,(max(0,dd-cover),l,h));count+=1
 split=np.linspace(lo,hi,math.ceil((hi-lo)/(math.pi/4))+1)
 for l,h in zip(split[:-1],split[1:]):add(l,h)
 while heap and best-heap[0][0]>tol and count<200000:
  lower,l,h=heapq.heappop(heap)
  if lower>=best:continue
  m=(l+h)/2;add(l,m);add(m,h)
 low=min(best,heap[0][0]) if heap else best
 assert best-low<=tol
 return low,best,count

def clearance(fixture,kind,a):
 grains=[(np.array(fixture['central_rotation']),np.zeros(3))]+[(np.array(s['rotation']),np.array(s['center'])) for s in fixture['supports']];segments=[[(p@Q.T+c,q@Q.T+c) for p,q in brace_segments(kind)] for Q,c in grains];rows=[]
 for i,j in itertools.combinations(range(4),2):
  lows=[];ups=[];count=0
  for src,dst in [(i,j),(j,i)]:
   Q,c=grains[dst]
   for p,q in segments[src]:
    for arc in grain_arcs('C3'):
     lo,hi,n=segment_arc(p,q,arc,Q,c);lows.append(lo-a-.022);ups.append(hi-a-.022);count+=n
  for p,q in segments[i]:
   for r,s in segments[j]:
    dd=segment_segment(p,q,r,s)-2*a;lows.append(dd);ups.append(dd)
  rows.append(dict(pair=[i,j],lower_mm=min(lows),upper_mm=min(ups),nodes=count))
 return dict(pairs=rows,clearance_lower_mm=min(x['lower_mm'] for x in rows),clearance_upper_mm=min(x['upper_mm'] for x in rows),noninterfering=all(x['lower_mm']>=0 for x in rows),original_neighbor_height_bound_mm=.00002,robust_margin_lower_mm=min(x['lower_mm'] for x in rows)-.00004,robust_noninterfering=all(x['lower_mm']>=.00004 for x in rows),scope='New-member clearances for undeformed saved four-grain fixture, not a new first-contact search. Added chords stay inside original convex hull, so cannot newly reach the top plane.')

def main():
 C=json.loads((H.parent/'粒間接触検証_自由回転と濡れ_20261007/cluster_results.json').read_text(encoding='utf-8'));x=next(v for v in C['fixtures'] if v['model']=='C3' and v['pose_id']==3);f=np.array(next(v for v in x['force_cases'] if v['mu_top']==0 and v['mu_internal']==.6)['inner']['forces_normalized'])*.0009;rows=[]
 for kind,a in itertools.product(['Y3','T6'],[.01,.014,.018,.022]):
  m=build('C3',x['central_rotation'],x['points'],x['normals'],brace=kind,brace_a=a);res=evaluate(m,f,profiles=kind=='T6' and a==.014);gap=clearance(x,kind,a);L=sum(np.linalg.norm(p-q) for p,q in brace_segments(kind));V=math.pi*a*a*L+len(brace_segments(kind))*4*math.pi*a**3/3
  rows.append(dict(brace=kind,brace_radius_mm=a,pose_id=3,mu_top=0,mu_internal=.6,response=res,clearance=gap,added_volume_upper_mm3=V,claim_scope='The response is only a load-path sensitivity when added members interfere with fixed neighbors. No physical deformation claim beyond linear diagnostic.'));print(json.dumps({'brace':kind,'a':a,'valid_geometry':gap['noninterfering'],'Ereq':res['required_uniform_E_for_diagnostic_MPa']}),flush=True)
 (H/'brace_results.json').write_text(json.dumps(dict(physical_tests=0,success_probability=None,cases=rows),indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
