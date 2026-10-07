"""Finite-thickness enlarged shape sample, not a validated skiing grain.
CAD uses a 100x geometric enlargement of the reference free curved strip.
Only this free strip is meshed: no physical mating-cylinder or integrated grain
is certified by the zero-thickness centreline contact model.
"""
import json,math
from collections import Counter
from pathlib import Path
D=Path(__file__).resolve().parent
P=json.loads((D/'inputs.json').read_text(encoding='utf-8'))
s=100.;Rs=P['dimensional']['shell_radius_mm']*s
t=P['dimensional']['strip_thickness_mm']*s;width_mm=P['dimensional']['strip_width_mm']*s
phi=P['reference']['phi_rad'];N=256
vertices=[]
for j in range(N+1):
 a=-phi+2*phi*j/N
 for r,z in [(Rs-t/2,-width_mm/2),(Rs+t/2,-width_mm/2),(Rs-t/2,width_mm/2),(Rs+t/2,width_mm/2)]:
  vertices.append((r*math.sin(a),r*math.cos(a),z))
faces=[]
def quad(a,b,c,d):faces.extend([(a,b,c),(a,c,d)])
for i in range(N):
 q=4*i;p=q+4
 quad(q+1,q+3,p+3,p+1)
 quad(q,p,p+2,q+2)
 quad(q+2,p+2,p+3,q+3)
 quad(q,q+1,p+1,p)
quad(0,2,3,1);q=4*N;quad(q,q+1,q+3,q+2)
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def dot(a,b):return sum(x*y for x,y in zip(a,b))
volume=sum(dot(vertices[a],cross(vertices[b],vertices[c]))/6 for a,b,c in faces)
undirected=Counter();directed=Counter()
lines=['solid enlarged_free_clip_mm']
for f in faces:
 a,b,c=(vertices[i] for i in f);normal=cross(sub(b,a),sub(c,a));length=math.sqrt(dot(normal,normal));assert length>0
 normal=tuple(x/length for x in normal)
 lines.append(' facet normal '+' '.join(f'{x:.12g}' for x in normal));lines.append('  outer loop')
 for v in [a,b,c]:lines.append('   vertex '+' '.join(f'{x:.12g}' for x in v))
 lines.extend(['  endloop',' endfacet'])
 for i,j in zip(f,f[1:]+f[:1]):undirected[tuple(sorted((i,j)))]+=1;directed[(i,j)]+=1
lines.append('endsolid enlarged_free_clip_mm')
(D/'曲線接点_100倍形状確認用.stl').write_text('\n'.join(lines)+'\n',encoding='ascii')
analytic=2*phi*Rs*t*width_mm
check=dict(scale=100,units='mm',centreline_radius_mm=Rs,thickness_mm=t,width_mm=width_mm,half_angle_rad=phi,
 vertices=len(vertices),triangles=len(faces),mesh_volume_mm3=volume,analytic_volume_mm3=analytic,
 relative_volume_error=abs(volume-analytic)/analytic,
 closed_two_faces_per_edge=all(n==2 for n in undirected.values()),
 oriented_edge_pairs=all(directed[(j,i)]==n for (i,j),n in directed.items()),
 positive_volume=volume>0,
 scope='Finite free shape only. STL contains no mating pin, protective grain body, manufacturing tolerance, surface finish or safety validation.')
assert check['closed_two_faces_per_edge'] and check['oriented_edge_pairs'] and check['positive_volume'] and check['relative_volume_error']<1e-4
(D/'形状検証.json').write_text(json.dumps(check,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
scad='''// Enlarged FREE strip only; units mm. No snow performance is demonstrated.
// BVP contact uses a centreline idealization; this finite CAD is NOT its exact contact solution.
scale_factor=100;
Rs=0.05*scale_factor;
t=0.005*scale_factor;
b=0.1*scale_factor;
phi=2.1;
N=256;
function pt(r,i)=[r*sin((-phi+2*phi*i/N)*180/PI),r*cos((-phi+2*phi*i/N)*180/PI)];
points=concat([for(i=[0:N]) pt(Rs+t/2,i)],[for(i=[N:-1:0]) pt(Rs-t/2,i)]);
linear_extrude(height=b,center=true,convexity=10) polygon(points);
'''
(D/'曲線接点_100倍形状確認用.scad').write_text(scad,encoding='utf-8')
print(json.dumps(check,ensure_ascii=False))
