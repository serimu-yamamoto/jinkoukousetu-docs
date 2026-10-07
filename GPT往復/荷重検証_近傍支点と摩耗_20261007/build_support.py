"""Review geometry only. No material, ski, weather or safety validation.
Requires the previous cycle's build_seats.py in its sibling repository folder.
"""
import sys,json,math,struct
from pathlib import Path
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H.parents[1]/'.deps'))
sys.path.insert(0,str(H.parent/'幾何検証_内側保持座_20261007'))
import numpy as np
import manifold3d as md
import build_seats as old
P=json.loads((H/'inputs.json').read_text(encoding='utf-8'))
rb=P['local_support']['sphere_radius_mm'];s=P['local_support']['center_offset_z_mm'];rho=P['seat']['rho']

def bumps(N,offset=s):
    return md.Manifold.sphere(rb,N).translate((-rho,0,offset))+md.Manifold.sphere(rb,N).translate((-rho,0,-offset))

def save_stl(m,name):
    v,f=old.arrays(m)
    with (H/name).open('wb') as out:
        out.write(b'Units mm; nominal W2 short supports; no texture or load validation'.ljust(80,b' '))
        out.write(struct.pack('<I',len(f)))
        for ids in f:
            a,b,c=v[ids];n=np.cross(b-a,c-a);length=np.linalg.norm(n)
            if length:n/=length
            out.write(struct.pack('<12fH',*n,*a,*b,*c,0))

def figure():
    N=16;core=old.backbone(N);seat=old.seats(P['seat'],N);pair=bumps(N)
    svg=['''<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="1100" viewBox="0 0 1500 1100">
<style>text{font-family:Meiryo,'Noto Sans CJK JP',sans-serif;fill:#173149}.h{font-size:28px;font-weight:bold}.t{font-size:22px}.s{font-size:18px}.green{fill:#167353}.warn{fill:#a54934}</style>
<rect width="1500" height="1100" fill="#f2f6f8"/><text x="35" y="50" class="h">丸い支点を保持部の近くへ：省材料候補 W2</text>
<text x="35" y="90" class="t">保護の幾何条件を改善。50℃での強度・滑走感・摩耗寿命を実証した図ではありません。</text>
<rect x="25" y="120" width="700" height="410" fill="white" rx="14"/><rect x="745" y="120" width="730" height="410" fill="white" rx="14"/>
<text x="50" y="160" class="h">前回 W1a</text><text x="770" y="160" class="h">W2：半径30µmの支点を上下へ追加</text>
<text x="50" y="197" class="s">青：骨格 / 黄：冬の保持用に検討中の座</text><text x="770" y="197" class="s">緑：球を2個重ねる。中心の上下間隔は10µm。</text>''']
    svg.append(old.project([(core,'#5d8ba3'),(seat,'#dfac51')],360,332,460))
    svg.append(old.project([(core,'#5d8ba3'),(seat,'#dfac51'),(pair,'#52a381')],1090,332,460))
    svg.append('''<text x="50" y="469" class="t">外向き形状差2µm込みの保証下限</text><text x="50" y="506" class="h">8.00µm</text>
<text x="770" y="469" class="t">同じ幾何条件での保証下限</text><text x="770" y="506" class="h green">10.69µm（理想形状・剛体平面）</text>
<rect x="25" y="550" width="700" height="470" fill="white" rx="14"/><rect x="745" y="550" width="730" height="470" fill="#e4eef2" rx="14"/>
<text x="50" y="592" class="h">摩耗すると、形状と強度は別々に変わる</text>
<text x="55" y="647" class="t">全保護面が半径方向へ均等に8µm摩耗</text>
<text x="60" y="708" class="s">W1a：保護余裕の下限</text><text x="420" y="708" class="h warn">0µm</text>
<text x="60" y="757" class="s">W2：保護余裕の下限</text><text x="420" y="757" class="h green">2.69µm</text>
<text x="60" y="826" class="s">共通の細い骨格：曲げ剛性 EI</text><text x="480" y="826" class="h warn">約29%</text>
<text x="55" y="883" class="t">保護余裕が残っても、十分な強度とは限らない。</text>
<text x="55" y="929" class="s">摩耗速度・寿命・局部欠損の値ではない。</text>
<text x="55" y="969" class="s">追加材が雪の保持面を一部隠す問題も残る。</text>
<text x="770" y="592" class="h">支点を高くし過ぎない</text>
<text x="775" y="648" class="t">中心ずれ ±5µm と ±20µm は、</text>
<text x="775" y="687" class="t">今回の保証下限では同じ10.69µm。</text>
<text x="775" y="743" class="s">±20µmの方が実際の最小余裕を増す可能性はある。</text>
<text x="775" y="779" class="s">有限方向の比較は全方向の最適性証明ではない。</text>
<text x="775" y="837" class="t">±5µmは省材料の試作候補。</text>
<text x="775" y="884" class="s">硬いほど接触変形は減るが、接触圧は増える。</text>
<text x="775" y="925" class="s">粒全体が動く量を、そのまま保護損失にしない。</text>
<text x="775" y="969" class="s">必要なのは、支点と保持座の相対変形の実測。</text>
<text x="35" y="1063" class="s">数値照合・形状データ・費用仮定を同梱。物理試験0件、実証成功確率は未算定。図の形状は無荷重・無加工模様。</text></svg>''')
    (H/'近傍支点_保護余裕と摩耗.svg').write_text(''.join(svg),encoding='utf-8')

def main():
    result=json.loads((H/'results.json').read_text(encoding='utf-8'))
    levels=[]
    for N in P['mesh_quality']:
        core=old.backbone(N);seat=old.seats(P['seat'],N);base=core+seat;m=base+bumps(N)
        check=old.meshcheck(m)
        check.update(quality=N,W1a_volume_mm3=base.volume(),net_support_added_volume_mm3=m.volume()-base.volume())
        levels.append(check)
    conv=abs(levels[-1]['volume_mm3']-levels[-2]['volume_mm3'])/levels[-1]['volume_mm3']
    addconv=abs(levels[-1]['net_support_added_volume_mm3']-levels[-2]['net_support_added_volume_mm3'])/levels[-1]['net_support_added_volume_mm3']
    assert conv<.01 and addconv<.01
    assert levels[-1]['volume_mm3']<=result['cost_upper']['total_volume_upper_mm3']
    save_stl(m,'W2_short_support.stl')
    scad='''// Units mm. Research review; texture, loads and production tolerances omitted.
$fn=128;
R=0.25; r=0.03; re=0.05; gap=0.02; theta=asin((2*re+gap)/(2*R));
offset=0.005; // provisional low-volume candidate, not a mechanical optimum
union(){
 rotate([0,0,theta]) rotate_extrude(angle=360-2*theta) translate([R,0]) circle(r=r);
 for(s=[-1,1]) translate([R*cos(theta),s*R*sin(theta),0]) sphere(r=re);
 translate([-0.22,0,0]) scale([0.04,0.035,0.02]) sphere(r=1);
 for(s=[-1,1]) translate([-0.22,0,s*offset]) sphere(r=0.03);
}
'''
    (H/'近傍支点.scad').write_text(scad,encoding='utf-8');figure()
    out=dict(levels=levels,last_relative_volume_change=conv,last_relative_added_volume_change=addconv,
             manifold_version='3.5.4',numpy_version=np.__version__,units='mm',
             no_roughness_or_tolerance_in_mesh=True,physical_validation=False)
    (H/'mesh_validation.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(out))

if __name__=='__main__':main()
