# 第105巡・再現資料
サーバー上で `python3 -B GPT往復/温暖形成と開放環粒の製造監査_20261010/reproduce.py --check` を実行する。
初回生成のみ `--check` を外す。Python標準ライブラリだけを使用。設定はスクリプトと結果のinputsに記載。
共通部品は [formation_routes.py](../../計算部品/formation_routes.py)。作業時は同内容の ~/firn/lib/ を使用し、公開照合後に今回のコピーを削除する。

- [報告](../GPT回答_多方向探索第105巡_温暖形成と開放環粒の製造条件_20261010.md)
- [計算](reproduce.py)、[結果](results.json)、[35件の数値検証](validation.json)
- [形状ソース](open_rim_grain.scad)：2つの環＋6支柱。ポリゴン近似、描画・製造は未実施。
- [出典範囲](sources.json)：原著条件と仮定を分離。ライブ本文取得失敗時は出版社の検索索引本文を使用したことも記録。
- [Claude依頼](claude_handoff.md)、[研究状態](research_state.json)
- [旧本文保存確認](index_preservation.json)、[公開前監査](publication_audit.json)、[公開対象ハッシュ](manifest.json)

材料体積は円環断面積×(上下環の合計厚さ＋中間高さ×支柱の周方向占有率)。
密度・寸法・充填・品質歩留まり・製造時間は設計仮定。供給固体を良品量と同一視しない。
window_features_per_second は良品に対応する窓数、window_features_before_quality_per_second は品質選別前の加工数の仮定。
回収は新規原料を減らしても延べ処理量を減らさない。収支は定常閉ループの仮定で、汚染・劣化・再加工可能性を実証していない。
同時成形では側面除去工程の前提が変わるため、今回の303.75tをそのまま使わず再計算する。

物理試験0件、成功確率null。点列の幾何確認を、流体解析・強度・排水・50℃滑走・人体／環境安全の証明にしない。
