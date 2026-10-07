# 出典と使用範囲

閲覧日2026-10-07。原文や図の大量転載は行わず、参照位置と適用範囲を示す。

1. [Lobo, Vandenberghe, Boyd, Lebret: Applications of Second-Order Cone Programming](https://stanford.edu/~boyd/papers/socp.html)。二次錐最適化と摩擦を含む応用の一次資料。本巡の静的な円形摩擦円錐の表現へ使用。物理接触則が自動的に解けるとは読まない。
2. [CVXPY: Solver Features](https://www.cvxpy.org/tutorial/solvers/index.html)、[Clarabel: Solver Settings](https://clarabel.org/stable/api_settings/)。使用可能な解法と許容誤差の公式資料。本巡はCVXPY 1.9.3 / Clarabel 0.11.1。数値収束と現物性能を区別する。
3. [Yoshihiro Kanno: Primal-dual algorithm for quasi-static contact problem with Coulomb's friction, arXiv:2101.11763v2](https://arxiv.org/html/2101.11763v2)。第1節、第2.1〜2.4節を参照。接触とすべりの相補条件、摩擦力とすべり方向、安易な凸最適化への置換の違いを確認。論文の全アルゴリズムを実装したという主張ではない。本巡は固定接点の静的緩和と、別の変位整合検査。
4. [第14巡](../GPT回答_多方向探索第14巡_骨格変形と内部補強の費用条件_20261007.md)、参照コミット d815801d0a0272033c9428e8b4b7b4b811d105bf。elastic_free.py、elastic_results.json、brace_results.json、economics_results.jsonを利用。
5. [第13巡](../GPT回答_多方向探索第13巡_粒間接触と三方向開口の比較_20261007.md)。cluster_results.jsonとnumerical_audit.jsonの固定接点・精度比較を利用。実物の接点配置とは扱わない。
6. [第8巡](../GPT回答_多方向探索第8巡_曲がる接点の非線形着脱と保持力の限界_20261007.md)。0.0173mN/個、0.000105mm³/個という限定したクリップ尺度を参照。異なる形状・荷重方向へ性能保証を移さず、理想的な物量比較にのみ使う。

追加保持力の円錐射影、短い受けの面積予算、数値比較、図は本研究で導出・作成したもの。外部の実験値・見積書・製造保証・特許の新規性確認ではない。
