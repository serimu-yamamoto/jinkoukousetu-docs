# 第42巡の監査用資料

[受け渡し本文](../GPT回答_多方向探索第42巡_摩耗後も滑りを保つ先端と接触相の配置_20261009.md)が入口。摩耗後形状を与えた接触感度、偏摩耗、再配置、追加保守費を扱う。

- [入力](inputs.json)：未校正の物性・費用・運用仮定。
- [導出と限界](model.md)、[再計算](reproduce.py)、[依存ライブラリ](requirements.txt)、[実行環境](environment.json)。
- [結果](results.json)：24数値照合。物理試験0件、成功確率null。
- [接触30条件](wear_contact_cases.csv)、[摩擦変化18境界](friction_drift_limits.csv)、[圧力の積分収束](pressure_convergence.csv)。
- [混合相25条件](heterogeneous_phase_cases.csv)、[再配置9条件](redistribution_cases.csv)、[保守費3条件](maintenance_cost_limits.csv)。
- [出典台帳](sources.json)、[原著の限定観測4点](source_observations.csv)。観測を50℃の実ソールへ移していない。
- [摩耗後の接触](wear_contact_response.png)、[荷重集中と処理費](phase_load_and_maintenance.png)：今回計算からの図。
- [公開ファイル照合表](publication-manifest.json)：自己ファイルを除く公開対象のSHA256。

Python 3.12でrequirements.txtのライブラリを導入し、このフォルダのreproduce.pyを実行する。--no-plotsは図の再生成を省略。研究中の.depsがあれば自動参照するが、GitHubへは含めない。第三者のPDF・ページ画像は再配布しない。

滑らかな摩耗形は設計感度用に与えたもので、局所摩耗則を時間積分した結果ではない。雪感、エッジの支持・解放、50℃、雨・冬・安全の合格を示さない。
