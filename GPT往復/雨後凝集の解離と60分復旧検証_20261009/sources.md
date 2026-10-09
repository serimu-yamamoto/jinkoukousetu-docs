# 一次資料と読み取った範囲

取得日2026-10-09。原文の再配布は行わず、URL・式の参照・PDFハッシュをsource_audit.jsonに残す。

1. Fingerle, A.; Herminghaus, S., *Mechanisms of dissipation in wet granular matter*, arXiv:0708.2597v1（2007年投稿）。https://arxiv.org/abs/0708.2597
   PDF：https://arxiv.org/pdf/0708.2597
   式2〜6、球−平板衝突の方法と結果を読んだ。PDF2ページ目を画像照合。今回の材料・50℃・雨後復旧の実験ではない。PDF上の組版日付と投稿年を混同しない。式5の表示と式4の積分を別途照合した。

2. Bagheri, M.; Roy, S.; Pöschel, T. (2024), *Approximate expressions for the capillary force and the surface area of a liquid bridge between identical spheres*, Computational Particle Mechanics 11,2179–2190。
   https://link.springer.com/article/10.1007/s40571-024-00772-5
   HTMLの適用範囲、式17・24・27・28、比較部分を確認。Young–Laplace数値解への近似で、人工粒の実験ではない。θ=0、v=10⁻⁶〜10⁻²のみ実装。体積が減ると接触時の力は増えるという式24の性質を、排水後の反例に使用した。任意形状粒・多体水塊へ外挿しない。

3. IAPWS R1-76(2014), *Revised Release on the Surface Tension of Ordinary Water Substance*。
   https://iapws.org/technical-guidance/release/Surf-H2O
   https://iapws.org/technical-guidance/release/Surf-H2O.download
   3ページ目の式・係数・適用範囲を画像照合。水蒸気と平衡の純水の式である。今回の排水の汚れや実素材の接触角を与えない。本文の2.38MJ/kgは本表面張力資料からの引用ではなく、蒸発潜熱の丸めた比較仮定。

4. Kovalcinova et al. (2018), *Energy dissipation in sheared wet granular assemblies*, Physical Review E 98,032905。
   DOI：https://doi.org/10.1103/PhysRevE.98.032905
   著者公開PDF：https://web.njit.edu/~kondic/granular/2018_PRE_cohesive.pdf
   方法、力・仕事式、凝集と再形成の散逸を確認。2ページ目を画像照合。主解析は2D DEMで3D水橋式を使う。軟化したばね定数や摩擦係数を今回の材料定数として転記しない。図のZnI2水溶液を本材料に使う意味ではない。印刷定数と再積分を区別した。

## 既存資料との差分

- Claude台帳：調査台帳/物性値照合_自律ループv2v3.md、LF正規化SHA256はsource_audit.json。開始時点で前巡から変更なし。全v3コード・結果・稼働は未確認。
- 第10巡：振動の重力相似だけでは濡れた粒へ移せないこと、38分処理枠と分流槽を既に記載。本巡は水橋の仕事、相対運動、枝損傷、反復損失を追加した。
- 第50巡：濡れた粒内の復帰と排水口。本巡は自由粒間の凝集解離へ拡張。
- 第75巡：局所補強と柔軟根元、自由粒の水橋による移動。本巡は切り離す全距離と仕事・機械工程を追加。
- 材料採算2,000m²と整地1km×20mの面積は異なる。両方を表に残し、小面積の費用を全コースに転用しない。
