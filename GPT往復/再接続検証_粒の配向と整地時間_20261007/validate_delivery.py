"""Validate delivery structure; not a physical-material verification."""
from pathlib import Path
import ast,json,math,re,struct,sys
H=Path(__file__).resolve().parent;root=H.parent.parent
if (root/".deps").exists():sys.path.insert(0,str(root/".deps"))
import numpy as np
json_count=0
for p in H.glob("*.json"):
    json.loads(p.read_text(encoding="utf-8"));json_count+=1
py_count=0
for p in H.glob("*.py"):
    ast.parse(p.read_text(encoding="utf-8"));py_count+=1
stls=[]
dt=np.dtype([("normal","<f4",(3,)),("v","<f4",(3,3)),("attr","<u2")])
for p in H.glob("*.stl"):
    b=p.read_bytes();n=struct.unpack_from("<I",b,80)[0]
    assert len(b)==84+50*n,p.name
    data=np.frombuffer(b,dtype=dt,offset=84,count=n)
    v=data["v"].astype(float);normal=data["normal"].astype(float)
    assert np.isfinite(v).all() and np.isfinite(normal).all(),p.name
    cross=np.cross(v[:,1]-v[:,0],v[:,2]-v[:,0]);area2=np.linalg.norm(cross,axis=1)
    assert np.all(area2>0),p.name
    assert np.max(np.abs(np.linalg.norm(normal,axis=1)-1))<2e-4,p.name
    assert np.min(np.sum(normal*cross/area2[:,None],axis=1))>.999,p.name
    stls.append({"path":p.name,"triangles":n,"bytes":len(b)})
report=H.parent/"GPT回答_多方向探索第10巡_直交する開放輪と分流再生の設計条件_20261007.md"
links=0
for p in [*H.glob("*.md"),report]:
    text=p.read_text(encoding="utf-8")
    for dest in re.findall(r"!?\[[^\]]*\]\(([^\s)]+)\)",text):
        if dest.startswith(("http:","https:","#")):continue
        assert (p.parent/dest.split("#")[0]).exists(),(p.name,dest)
        links+=1
R=json.loads((H/"results.json").read_text(encoding="utf-8"))
X=json.loads((H/"crossed_results.json").read_text(encoding="utf-8"))
assert len(R["checks"])==12 and all(x["passed"] for x in R["checks"])
assert R["metadata"]["physical_success_probability"] is None
assert sum(len(m["tolerance_corners"]) for m in X["models"])==256
assert all(m["path"]["reverse_path_exists"] for m in X["models"])
print(json.dumps({"json_files":json_count,"python_files":py_count,"STLs":stls,"relative_links":links,
                  "numeric_checks":12,"physical_tests":0,"physical_success_probability":None},indent=2))
