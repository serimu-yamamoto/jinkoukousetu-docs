"""Original schematic, not a manufactured geometry. No third-party images."""
from pathlib import Path
import math

p=Path(__file__).resolve().parent
def cgrain(cx,cy,r,stroke,color,ends=True):
    a=math.asin(.24)
    x=cx+r*math.cos(a)
    dy=r*math.sin(a)
    path=f'<path d="M {x} {cy+dy} A {r} {r} 0 1 1 {x} {cy-dy}" fill="none" stroke="{color}" stroke-width="{stroke}"/>'
    if ends:
        path+=''.join(f'<circle cx="{x}" cy="{cy+s*dy}" r="{stroke*5/6}" fill="{color}"/>' for s in [-1,1])
    return path

s=['''<svg xmlns="http://www.w3.org/2000/svg" width="1440" height="1030" viewBox="0 0 1440 1030">
<defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#147eac"/></marker></defs>
<style>text{font-family:Meiryo,'Noto Sans CJK JP',sans-serif;fill:#173149}.title{font-size:30px;font-weight:700}.h{font-size:23px;font-weight:700}.t{font-size:20px}.small{font-size:17px}.num{font-size:28px;font-weight:700}.line{stroke:#9aaab5;stroke-width:2;fill:none}.water{stroke:#147eac;stroke-width:4;fill:none;marker-end:url(#arrow)}</style>
<rect width="1440" height="1030" fill="#f4f7f8"/>
<text x="42" y="55" class="title">冬の保持と雨の排水を分けた開放粒 W1</text>
<text x="42" y="90" class="t">G3からの配置改良案。完成形状・実性能・製造費は未確定。図は縮尺をそろえていない。</text>
<rect x="30" y="117" width="670" height="506" rx="15" fill="white"/>
<rect x="718" y="117" width="692" height="506" rx="15" fill="white"/>
<text x="54" y="157" class="h">A　1粒内の機能を分ける</text>
''']
s.append(cgrain(333,344,111,26.64,'#637b8b'))
s.append('''<path d="M 235 315 Q 277 320 277 343 Q 277 367 235 371" fill="#d8a93b" stroke="#997325" stroke-width="2"/>
<path d="M 268 327 l -5 4 m 10 6 l -6 3 m 6 8 l -6 2 m 4 8 l -6 2" stroke="#997325" stroke-width="2"/>
<path d="M 350 263 L 350 422" class="water" stroke-dasharray="7 5"/>
<path d="M 293 252 L 235 218 L 66 218" class="line"/>
<text x="66" y="203" class="t">丸い外面：滑走時の接触</text>
<path d="M 238 342 L 105 369 L 59 369" class="line"/>
<text x="57" y="400" class="t">内側の厚い保持座</text>
<text x="57" y="429" class="small">凹凸0 / 1 / 2µmを比較</text>
<path d="M 454 317 L 553 256" class="line"/>
<text x="480" y="216" class="t">先端・細い腕</text>
<text x="480" y="243" class="small">凹凸加工を避ける</text>
<path d="M 353 389 L 522 442" class="line"/>
<text x="421" y="472" class="t">盲穴にせず空気を逃がす</text>
<text x="55" y="531" class="small">外形0.6mm、線径60µm、先端100µmは参照寸法。</text>
<text x="55" y="558" class="small">保持座の形・追加体積・ランダム姿勢は次の3D検証対象。</text>
<text x="55" y="588" class="small">中心の穴 ≠ 充填床の連続した水の通り道</text>
<text x="742" y="157" class="h">B　冬は3つの破壊面と排水を同時に見る</text>
<path d="M 751 245 Q 792 200 831 240 Q 876 206 926 243 Q 980 198 1034 241 Q 1085 206 1147 240 Q 1224 204 1277 242 L 1372 238 L 1372 302 L 751 302 Z" fill="#dcecf6"/>
<text x="790" y="269" class="t">天然雪：乾燥 → 湿雪 → 融解・再凍結</text>
''')
for y in [348,428]:
    for x in [808,934,1060,1186,1312]:
        s.append(cgrain(x,y,25,7,'#718797'))
s.append('''<path d="M 749 487 L 793 472 L 837 489 L 892 466 L 946 487 L 998 469 L 1051 488 L 1099 472 L 1153 490 L 1216 466 L 1268 487 L 1312 475 L 1375 490" stroke="#a9977e" stroke-width="13" fill="none"/>
<path d="M 877 313 L 877 471 L 1365 525" class="water"/>
<path d="M 1123 310 L 1123 468" class="water"/>
<text x="756" y="198" class="small">① 雪／粒　② 粒床内部　③ 粒／下地</text>
<text x="753" y="564" class="small">水を外へ出す出口能力と、粒を外へ出さない保持が必要。</text>
<text x="753" y="592" class="small">網・シート・マットは導入しない。下地保持は未実証。</text>
<rect x="30" y="643" width="1380" height="348" rx="15" fill="#173149"/>
<text x="54" y="686" class="h" style="fill:white">C　同時に満たす必要がある予算（すべて仮条件下の計算）</text>
<text x="65" y="740" class="num" style="fill:#b6dfe9">残留空気 2.55%</text>
<text x="65" y="778" class="t" style="fill:white">空隙のうちの割合</text>
<text x="65" y="814" class="small" style="fill:white">仮価格500円/kg・年額1,900万円で</text>
<text x="65" y="844" class="small" style="fill:white">重量補償できる中性浮力の境界。</text>
<text x="65" y="875" class="small" style="fill:white">洪水保持や成功率の合格値ではない。</text>
<text x="523" y="740" class="num" style="fill:#b6dfe9">雨の流入 約96 L/s</text>
<text x="523" y="778" class="t" style="fill:white">2,000m²・30°・200mm/h</text>
<text x="523" y="814" class="small" style="fill:white">透水のよい粒でも出口不足なら蓄水。</text>
<text x="523" y="844" class="small" style="fill:white">水の排出と整地・泥除去・再接続は別。</text>
<text x="523" y="875" class="small" style="fill:white">現地設計降雨・場外流入は未設定。</text>
<text x="972" y="740" class="num" style="fill:#b6dfe9">冬の追加保持 2.55 kPa</text>
<text x="972" y="778" class="t" style="fill:white">雪厚1m・450kg/m³・30°</text>
<text x="972" y="814" class="small" style="fill:white">μ=0.2・水圧0・仮の力比1.5。</text>
<text x="972" y="844" class="small" style="fill:white">材料の実測強度ではない。</text>
<text x="972" y="875" class="small" style="fill:white">融解時の最弱面を照合する。</text>
<text x="65" y="944" class="t" style="fill:#ffd27f">物理試験0件。雪の滑走感・50℃・健康環境適合・90%超の成功は未証明。</text>
</svg>''')
(p/'構造と成立条件.svg').write_text(''.join(s),encoding='utf-8')
print('Schematic generated; conceptual placement, not final CAD.')
