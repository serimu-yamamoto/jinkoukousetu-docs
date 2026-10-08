"""Check numerical reproducibility and document integrity, not real-material success."""
import json,re,shutil,subprocess,sys,tempfile
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import quote
P=Path(__file__).resolve().parent
ROOT=P.parents[1]
BASE="b4014e27c86096725c70cc09c0774c1ce394867c"
REPORT=P.parent/"GPT回答_多方向探索第53巡_一体発泡で戻る粒と量産の成立条件_20261009.md"
checks=[]
def check(name,ok):
    if not ok:raise AssertionError(name)
    checks.append({"name":name,"passed":True})
def read(p):return p.read_text(encoding="utf-8").replace("\r\n","\n")
r=json.loads(read(P/"results.json"))
doc=read(REPORT)
check("no physical success or 90 percent claim generated",
      r["physical_tests"]==0 and r["success_probability"] is None and "90％超という保証は作っていない" in doc)
files=["results.json","numerical-checks.json","source-values.csv","cutting.csv","particles.csv","water.csv","buoyancy.csv","grooming.csv","cost.csv","end-seal.csv"]
with tempfile.TemporaryDirectory(prefix="reproduce-",dir=P) as tmp:
    t=Path(tmp);shutil.copy2(P/"model.py",t/"model.py")
    subprocess.run([sys.executable,"-X","utf8",str(t/"model.py")],check=True,capture_output=True)
    check("all ten numerical outputs reproduce byte for byte",
          all((P/f).read_bytes()==(t/f).read_bytes() for f in files))
num=json.loads(read(P/"numerical-checks.json"))
check("15 consistency checks passed",len(num)==15 and all(x["passed"] for x in num))
broken=[]
for dest in re.findall(r"\]\(([^)]+)\)",doc):
    if re.match(r"https?://|#",dest):continue
    if dest.endswith("/publication-manifest.json") or dest.endswith("/document-checks.json"):continue
    if not (REPORT.parent/dest).is_file():broken.append(dest)
check("all report links to substantive local artifacts exist",not broken)
check("reported geometric results match model",
      round(100*r["cutting"]["500um_cube_affected_at_one19p6um_cell"],2)==21.72
      and round(100*r["cutting"]["500um_profile_two_end_affected_at_one19p6um_cell"],2)==7.84
      and round(r["selected_mass_candidate"]["mass_at_phi055_t"],2)==140.03)
check("mass and manufacturing geometry limits disclosed",
      all(x in doc for x in ("同じ形状","温度点","24時間","72時間","体積比","58面","良品歩留まり100％")))
check("50 and 60 C are not fabricated measurement inputs",
      50 not in r["source_audit"]["temperature_figure_points_C"]
      and 60 not in r["source_audit"]["temperature_figure_points_C"]
      and r["source_audit"]["50C_sample_identified"] is False
      and r["source_audit"]["60C_sample_identified"] is False)
cached=ROOT/".git/docs-before53.json"
if cached.exists():old=json.loads(read(cached))
else:
    old={}
    for name in ("README.md","GPT往復/README.md","回覧板.md"):
        u="https://raw.githubusercontent.com/serimu-yamamoto/jinkoukousetu-docs/"+BASE+"/"+quote(name,safe="/")
        with urlopen(u,timeout=20) as f:old[name]=f.read().decode("utf-8")
old={k:v.replace("\r\n","\n") for k,v in old.items()}
for name,anchor,history in [
    ("README.md","## 最新の独立検証とClaudeへの受け渡し","## 第52巡の独立検証（履歴）"),
    ("GPT往復/README.md","## 最新の受け渡し","## 第52巡の受け渡し")]:
    text=read(ROOT/name)
    start=text.index(anchor);end=text.index(history,start)
    restored=text[:start]+anchor+text[end+len(history):]
    check("prior history preserved exactly: "+name,restored==old[name])
board=read(ROOT/"回覧板.md")
board=re.sub(r"\n\n\*\*第53巡の一体発泡・小粒化検証：\*\*[^\n]*","",board,count=1)
board=board.replace("第53巡・一体発泡と小粒化","第52巡・復帰材料と乾湿寸法")
oldline=re.search(r"^\*\*今回の最新報告：\*\*.*$",old["回覧板.md"],re.M).group(0)
board=re.sub(r"^\*\*今回の最新報告：\*\*.*$",lambda m:oldline,board,count=1,flags=re.M)
check("prior board entries and instructions preserved exactly",board==old["回覧板.md"])
check("3 original figures present in PNG and SVG",
      all((P/(n+ext)).stat().st_size>1000 for n in ("01-size-and-mass","02-rain-and-grooming","03-concept") for ext in (".png",".svg")))
textfiles=[REPORT]+[p for p in P.iterdir() if p.suffix in (".md",".py",".csv",".json",".svg")]
check("new text is LF-only without trailing spaces",
      all(b"\r" not in p.read_bytes() and all(line==line.rstrip() for line in read(p).splitlines()) for p in textfiles))
(P/"document-checks.json").write_text(json.dumps({"checks":checks,"count":len(checks),"all_passed":True},ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
print(json.dumps({"document_checks":len(checks),"all_passed":True,"physical_material_validation":False},ensure_ascii=False))
