// Native SVG: no generated photograph, no claim of a completed engineering drawing.
// Run with Node.js. PNG generation is optional: supply the sharp module path as argv[2].
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
const here = path.dirname(fileURLToPath(import.meta.url));
const esc = s => String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
const text = (x,y,s,size=24,color='#19354b',weight=400) => `<text x="${x}" y="${y}" font-size="${size}" fill="${color}" font-weight="${weight}">${esc(s)}</text>`;
const box = (x,y,w,h,fill,stroke='none',rx=12) => `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${rx}" fill="${fill}" stroke="${stroke}"/>`;
const line = (x1,y1,x2,y2,color='#2b6c8d',width=4,extra='') => `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${color}" stroke-width="${width}" ${extra}/>`;
const arrow = (x1,y1,x2,y2,color='#087e8b') => line(x1,y1,x2,y2,color,7,'marker-end="url(#arrow)"');
let parts=[`<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1420" viewBox="0 0 1600 1420"><defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#087e8b"/></marker></defs><g font-family="Yu Gothic,Meiryo,Noto Sans CJK JP,sans-serif">`,box(0,0,1600,1420,'#f1f5f8'),box(0,0,1600,140,'#143448','none',0),text(48,61,'2億円案：接地式1台＋昼は上り1回',42,'white',700),text(50,106,'1km × 20mの仮定／構想・発注上限。実機性能と業者価格は未確定。',25,'#d8eaf3')];
parts.push(box(36,168,710,682,'white'),text(64,209,'配置：終点収納で昼の帰還をなくす',28,'#19354b',700));
parts.push(box(140,330,395,355,'#e1f0e8','#accabb'),box(117,278,441,48,'#fff1d0','#cdae69'),box(117,690,441,48,'#fff1d0','#cdae69'));
parts.push(text(174,310,'山頂収納 22m × 6m',25),text(174,723,'山麓収納 22m × 6m',25));
parts.push(line(131,332,131,683,'#567b98',8),line(545,332,545,683,'#567b98',8),line(112,325,112,688,'#c46b29',3),line(564,325,564,688,'#c46b29',3));
parts.push(box(85,246,61,24,'#47637a'),box(530,246,61,24,'#47637a'),text(203,263,'山側牽引・左右2系列',22));
parts.push(text(227,371,'実効整地幅20m',24),text(187,404,'機体荷重はローラーから床へ',20));
for(let j=0;j<5;j++)parts.push(box(142+j*78,530,75,43,'#168a92','#ffffff',2));
parts.push(text(196,561,'4m区画 × 5連',25,'white',700),arrow(338,510,338,433),text(369,488,'昼に上る',23));
parts.push(text(583,432,'長さ',23),text(577,464,'1,000m',23),text(577,548,'側方',21),text(577,577,'ガイド',21),text(574,606,'＋保護索',21));
parts.push(text(64,779,'営業前：山麓 → 昼整地 → 営業後：山頂',22),text(64,813,'帰還・大量補充は閉場後。毎回の折畳みなし。',22));
parts.push(box(772,168,792,352,'white'),text(800,209,'作業部：床に接する5区画',28,'#19354b',700));
parts.push(line(810,398,1530,398,'#89b19a',8),text(821,435,'支持床・人工フィルン：性能は別途試験',23));
parts.push(arrow(1170,263,1440,263),text(830,267,'山側へ牽引',23));
parts.push(line(879,300,1440,300,'#466176',9),line(1400,300,1440,387,'#b9742d',8),text(1374,337,'前刃',20));
for(const x of [1090,1220])parts.push(`<circle cx="${x}" cy="365" r="31" fill="#27798c" stroke="#143448" stroke-width="4"/>`,line(x,300,x,334,'#466176',7));
parts.push(`<path d="M 960 306 L 904 383 L 827 390" fill="none" stroke="#596e7f" stroke-width="9"/>`,text(807,338,'後部スカート',20),text(1040,480,'ローラー／振動は材料別に調整',23));
parts.push(box(772,542,792,308,'white'),text(800,584,'昼60分：最も重要な実証条件',28,'#19354b',700));
const blocks=[['退避等',12,'#6f879a'],['整地・短い停止',37.04,'#168a92'],['養生',10,'#d9a546']];
let bx=805;for(const [name,duration,color] of blocks){const bw=duration*11.5;parts.push(box(bx,618,bw,58,color,'none',3),text(bx+7,655,name,21,'white',700));bx+=bw;}
parts.push(text(805,714,'0.6m/s × 稼働率75% → 合計59.0分',27,'#19354b',700),text(805,759,'稼働率80%なら56.7分。養生20分では超過。',22),text(805,801,'0.6m/sで雪に近い品質を出せるか先に測る。',22));
parts.push(box(36,876,1528,483,'white'),text(66,922,'費用は「発注上限」：メーカー見積額ではない',31,'#19354b',700));
parts.push(box(66,950,468,175,'#e4f0ef'),text(89,989,'設備・工事・試験設計',26),text(89,1051,'1億5,000万円',42,'#087e8b',700),text(89,1098,'人工フィルンの全面購入は別',22));
parts.push(box(558,950,468,175,'#fff2d8'),text(580,989,'予備費＋消費税',26),text(580,1051,'4,800万円',42,'#93651e',700),text(580,1098,'予備費3,000万＋税1,800万',22));
parts.push(box(1050,950,480,175,'#163b51'),text(1074,989,'合計枠',26,'#d8eaf3'),text(1074,1051,'1億9,800万円',41,'white',700),text(1074,1098,'必要機能が全て枠内に入るか照会',22,'#d8eaf3'));
parts.push(text(70,1179,'成立条件①　安定した既存床・排水・管理道・上下端収納を利用できる',26),text(70,1224,'成立条件②　軽い接地機で0.6m/sの品質・牽引・再結合が成立する',26),text(70,1269,'成立条件③　長索高速ウインチなど、必要な仕様の実見積りが枠内に入る',26),text(70,1314,'豪雨の大量復旧は近傍回収＋管理道搬送。昼の軽整地とは分ける。',25));
parts.push(text(43,1397,'2026-10-05 / Codex    詳細・数量・計算・不成立条件は同日の再設計報告へ。寸法比は模式表現。',20,'#526a7d'),'</g></svg>');
const svg=parts.join('\n');
await fs.writeFile(path.join(here,'01_配置と予算.svg'),svg);
try {
  const require=createRequire(import.meta.url);
  const sharp=require(process.argv[2] || 'sharp');
  await sharp(Buffer.from(svg)).png().toFile(path.join(here,'01_配置と予算.png'));
  console.log('SVG and PNG written.');
} catch(error) { console.log('SVG written. PNG requires sharp: '+error.message); }
