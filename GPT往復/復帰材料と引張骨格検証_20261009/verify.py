"""Verify reproducibility, local report links and history preservation, not material success."""
import csv, json, math, re, shutil, subprocess, sys, tempfile
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import quote
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BASE="a6da338c378c3d5ae41f85daa9f7053db2d1dc49"
REPORT=HERE.parent/"GPT回答_多方向探索第52巡_乾湿で戻る骨格と疲労を逃がす接続_20261009.md"
checks=[]
def check(name,condition):
    if not condition: raise AssertionError(name)
    checks.append({"name":name,"passed":True})
def read(p): return p.read_text(encoding="utf-8").replace("\r\n","\n")
r=json.loads(read(HERE/"results.json"))
check("probability remains unknown and physical experiments remain zero",
      r["success_probability"] is None and r["physical_tests"]==0)
with tempfile.TemporaryDirectory(prefix="reproduce-",dir=HERE) as td:
    t=Path(td);shutil.copy2(HERE/"model.py",t/"model.py")
    subprocess.run([sys.executable,"-X","utf8",str(t/"model.py")],check=True,capture_output=True)
    names=["results.json","numerical-checks.json","bridge.csv","members.csv","humidity.csv","cost.csv","source-values.csv"]
    check("standard-library rerun reproduces all seven numerical files byte for byte",
          all((HERE/n).read_bytes()==(t/n).read_bytes() for n in names))
check("all 14 numerical consistency checks pass",
      len(json.loads(read(HERE/"numerical-checks.json")))==14 and
      all(x["passed"] for x in json.loads(read(HERE/"numerical-checks.json"))))
doc=read(REPORT)
broken=[]
for target in re.findall(r"\]\(([^)]+)\)",doc):
    if re.match(r"https?://|#",target): continue
    if target.endswith("/publication-manifest.json"): continue
    if target.endswith("/document-checks.json"): continue
    if not (REPORT.parent/target).is_file(): broken.append(target)
check("all substantive report file links exist",not broken)
check("report carries limitations of geometry and cross-material source transfer",
      all(s in doc for s in ("三次元","別候補","250µm","未実証","50℃","物理試験は0件","受領や同意")))
check("report numerical headline matches conditional model results",
      "48.7％" in doc and "14.1％" in doc and
      round(100*r["mechanics"]["two_panel_volume_ratio"],1)==48.7 and
      round(100*(r["mechanics"]["unbraced_volume_ratio"]-1),1)==14.1)
check("humidity comparison is independent of optimized member geometry",
      round(100*r["humidity"]["fixed_dry_spun_max_strain"],2)==8.59 and
      round(100*r["humidity"]["matched_dry_spun_max_strain"],2)==4.18 and
      "149µm部材をこの250µmの計算で検証したことにはならない" in doc)
cache=ROOT/".git/docs-before52.json"
if cache.exists(): old=json.loads(read(cache))
else:
    old={}
    for name in ("README.md","GPT往復/README.md","回覧板.md"):
        url="https://raw.githubusercontent.com/serimu-yamamoto/jinkoukousetu-docs/"+BASE+"/"+quote(name,safe="/")
        with urlopen(url,timeout=20) as f: old[name]=f.read().decode("utf-8")
old={k:v.replace("\r\n","\n") for k,v in old.items()}
for name,anchor,history in [
 ("README.md","## 最新の独立検証とClaudeへの受け渡し","## 第51巡の独立検証（履歴）"),
 ("GPT往復/README.md","## 最新の受け渡し","## 第51巡の受け渡し")]:
    text=read(ROOT/name)
    start=text.index(anchor);end=text.index(history,start)
    restored=text[:start]+anchor+text[end+len(history):]
    check("prior history preserved exactly: "+name,restored==old[name])
board=read(ROOT/"回覧板.md")
board=re.sub(r"\n\n\*\*第52巡の復帰材料・引張骨格検証：\*\*[^\n]*","",board,count=1)
board=board.replace("第52巡・復帰材料と乾湿寸法","第51巡・結晶配置と寿命")
prior_line=re.search(r"^\*\*今回の最新報告：\*\*.*$",old["回覧板.md"],re.M).group(0)
board=re.sub(r"^\*\*今回の最新報告：\*\*.*$",lambda m:prior_line,board,count=1,flags=re.M)
check("board prior entries and instructions preserved exactly",board==old["回覧板.md"])
check("all three original figures exist in PNG and SVG",
      all((HERE/(n+ext)).stat().st_size>1000 for n in ("01-member-volume","02-humidity","03-concept") for ext in (".png",".svg")))
text_files=[REPORT]+[p for p in HERE.iterdir() if p.suffix in (".md",".py",".csv",".json",".svg")]
check("new text is UTF-8, LF-only and has no trailing spaces",
      all(b"\r" not in p.read_bytes() and
          all(line==line.rstrip() for line in read(p).splitlines()) for p in text_files))
(HERE/"document-checks.json").write_text(json.dumps({"checks":checks,"count":len(checks),"all_passed":True},ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
print(json.dumps({"document_checks":len(checks),"all_passed":True,"material_validation":False},ensure_ascii=False))
