"""Standalone research figure. Curves are counterexamples, not measured performance."""
import sys,os,json,math
from pathlib import Path
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H.parents[1]/'.deps'))
os.environ['MPLCONFIGDIR']=str(H.parents[1]/'.scratch'/'mpl')
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from calculate import arch
font=Path('C:/Windows/Fonts/meiryo.ttc')
if font.exists():
    font_manager.fontManager.addfont(str(font))
    plt.rcParams['font.family']=font_manager.FontProperties(fname=str(font)).get_name()
plt.rcParams.update({'font.size':11,'axes.unicode_minus':False,'svg.fonttype':'none'})
P=json.loads((H/'inputs.json').read_text(encoding='utf-8'))
R=json.loads((H/'results.json').read_text(encoding='utf-8'))

def main():
    fig,axs=plt.subplots(2,2,figsize=(14,10),layout='constrained')
    fig.suptitle('同じ硬さ・同じ最大支持力でも、滑り心地は決まらない\n反例模型と内部機構の条件計算（実物性能の予測ではない）',fontsize=18)
    ref=next(x for x in R['ski_reference'] if x['angle_deg']==45)
    dm=ref['depth_mm'];N=P['ski_reference']['normal_force_N']
    ds=np.linspace(0,dm,400)
    ax=axs[0,0];ax.plot(ds,N*(ds/dm)**2,color='#173c56',lw=3,label='全案で同じ初回押込み')
    for r,c in [(0,'#77a7ba'),(.3,'#e19c34'),(.7,'#bc554e')]:
        d=np.linspace(r*dm,dm,400)
        ax.plot(d,N*((d-r*dm)/(dm-r*dm))**2,color=c,ls='--',lw=2,label=f'除荷後の残留深さ {r:.0%}')
    ax.set(title='A  初回の硬さだけでは、溝の残り方が不明',xlabel='押込み深さ (mm)',ylabel='法線力 (N)');ax.legend(fontsize=9);ax.grid(alpha=.2)
    ax=axs[0,1];u=np.linspace(0,5,800);peak=ref['initial_failure_force_N']
    for c,col,label in zip(P['post_peak']['models'],['#16846e','#bc554e'],['早く抵抗が下がる反例','抵抗が長く続く反例']):
        f=peak*(c['residual_ratio']+(1-c['residual_ratio'])*np.exp(-u/c['decay_length_mm']))
        ax.plot(u,f,color=col,lw=3,label=label)
    ax.set(title='B  最大値74.48 Nが同じでも、その後が違う',xlabel='最大値に達した後の横移動 (mm)',ylabel='横抵抗 (N)');ax.legend(fontsize=9);ax.grid(alpha=.2)
    ax=axs[1,0];c=P['arch'];row,F,U=arch(c['a_mm'],c['h_mm'],c['r_mm'],c['E_MPa']);w=np.linspace(0,2.2*c['h_mm'],800)
    ax.plot(w*1000,F(w)*1000,color='#805fa6',lw=3);ax.axhline(0,color='#789',lw=.7)
    ax.scatter([row['peak_displacement_mm']*1000],[row['peak_N']*1000],color='#bc554e',zorder=3)
    ax.annotate('0.768 mN\n荷重制御の限界点',xy=(row['peak_displacement_mm']*1000,row['peak_N']*1000),xytext=(18,.8),arrowprops={'arrowstyle':'->'},fontsize=10)
    ax.scatter([0,40],[0,0],color='#16846e');ax.text(38,-.27,'反転後\n安定位置',fontsize=9,ha='center')
    ax.set(title='C  内部機構の理想二本棒模型',xlabel='頂点の押込み (µm)',ylabel='押込み力 (mN)');ax.grid(alpha=.2)
    ax=axs[1,1];vals=R['dissipation_cases'];x=np.arange(4)
    ax.bar(x,[P['energy']['reserved_other_mu']]*4,color='#b7c5cf',label='他の抵抗を仮に0.08とする')
    ax.bar(x,[v['mechanical_mu'] for v in vals],bottom=P['energy']['reserved_other_mu'],color=['#16846e','#64a88c','#e2b364','#bc554e'],label='面積当たりの変形損失から算出')
    ax.axhline(.1,color='#bc554e',ls='--',label='仮の全抵抗枠0.10')
    ax.set_xticks(x,['硬い雪の参考\n0.86','仮定\n50','仮定\n100','仮定\n300']);ax.set_ylim(0,.16)
    ax.set(title='D  衝撃をよく吸収するだけでは、滑りは軽くならない',xlabel='新しく踏む面積当たりの散逸 (J/m²)',ylabel='力/法線荷重');ax.legend(fontsize=8,loc='upper left');ax.grid(axis='y',alpha=.2)
    fig.savefig(H/'応答比較.png',dpi=170);plt.close(fig)
    svg='''<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="920" viewBox="0 0 1500 920">
<style>text{font-family:Meiryo,'Noto Sans CJK JP',sans-serif;fill:#18354b}.h{font-size:28px;font-weight:bold}.t{font-size:22px}.s{font-size:18px}.red{fill:#ab443b}.green{fill:#17785d}</style>
<defs><marker id="a" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto"><path d="M0 0L10 5L0 10Z" fill="#416d86"/></marker></defs>
<rect width="1500" height="920" fill="#f2f6f8"/>
<text x="35" y="48" class="h">S1機能案：通常の支持・エッジの解放・整地の復帰を分ける</text>
<text x="35" y="88" class="t">配置を確定した製造図ではありません。内側機構と、残すべき荷重経路を示す検討図です。</text>
<rect x="25" y="120" width="710" height="445" rx="14" fill="white"/><rect x="755" y="120" width="720" height="445" rx="14" fill="white"/>
<text x="50" y="164" class="h">① 板からの力は外側の支持部へ</text>
<path d="M110 233H650" stroke="#263e50" stroke-width="8"/><text x="115" y="218" class="s">スキーの底面</text>
<path d="M175 248V408M585 248V408" stroke="#5d8ba3" stroke-width="28"/>
<path d="M177 282V374M585 282V374" stroke="#416d86" stroke-width="3" marker-end="url(#a)"/>
<path d="M300 393L390 354L480 393" fill="none" stroke="#ad735e" stroke-width="10"/>
<circle cx="300" cy="393" r="8" fill="#263e50"/><circle cx="390" cy="354" r="8" fill="#263e50"/><circle cx="480" cy="393" r="8" fill="#263e50"/>
<text x="292" y="442" class="s">内側の切替機構（配置は概念）</text>
<text x="50" y="491" class="t">仮の最大接点荷重72mNに対し、</text>
<text x="50" y="528" class="t red">内側へ入る力を1.07%未満に抑える条件。</text>
<text x="780" y="164" class="h">② エッジの過負荷で内側の状態を変える</text>
<path d="M838 278L1090 278" stroke="#416d86" stroke-width="5" marker-end="url(#a)"/><text x="835" y="244" class="s">横力 → 内部の動きへ変換</text>
<path d="M894 398L1080 332L1266 398" fill="none" stroke="#ad735e" stroke-width="10"/>
<path d="M894 398L1080 464L1266 398" fill="none" stroke="#ad735e" stroke-width="5" stroke-dasharray="9 6"/>
<circle cx="894" cy="398" r="9" fill="#263e50"/><circle cx="1266" cy="398" r="9" fill="#263e50"/>
<text x="814" y="519" class="t">材料破断に頼らず、位置・接続状態を変える仮説。</text>
<rect x="25" y="585" width="1450" height="277" rx="14" fill="#e0ebef"/>
<text x="50" y="632" class="h">③ 準静的に同じ向きへ押すだけでは、二安定の機構は元へ戻らない</text>
<text x="55" y="682" class="t">逆向きの機械動作・粒の向きの変更・戻し経路が必要。振動ローラーだけで戻るとは未確認。</text>
<text x="55" y="727" class="t">内側機構の理想寸法：支点間160µm、高さ20µm、棒径24µm、反転移動40µm。</text>
<text x="55" y="771" class="s">全体の開口、保持、冬の固着、50℃の反復耐久、人体・板の安全、量産費は、組込み後に再検証。</text>
<text x="55" y="815" class="s">前回W2の356µm開口・保護余裕を、この機能図へ自動的に引き継がない。外枠・ヒンジの費用も未算入。</text>
<text x="35" y="899" class="s">物理試験0件。機械的な接続・双安定性は先行研究が存在し、発明の新規性・特許性を主張した図ではありません。</text>
</svg>'''
    (H/'S1_三つの荷重経路.svg').write_text(svg,encoding='utf-8')
    print('Wrote research plot and concept diagram.')

if __name__=='__main__':main()
