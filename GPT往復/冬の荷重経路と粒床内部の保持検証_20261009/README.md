# 冬の荷重経路と粒床内部の保持検証

[第90巡の報告](../GPT回答_多方向探索第90巡_雪の固着を粒床と地盤までつなぐ冬季設計_20261009.md)。

- [出典](sources.md)：2026年の公開要旨、2025年野外論文、1977年PEシート反例。取得範囲を区別。
- [模型](model.md)、[入力](inputs.json)、[再計算コード](reproduce.py)、[計算結果](results.json)、[30算術照合](validation.json)。
- [描画コード](draw.py)、[層別荷重と保持](winter_load_path.png)、[表面強化だけの限界](surface_only_plateau.png)。
- [未実施の試験仕様](protocol.md)、[Claudeへの依頼](claude_handoff.md)、[研究状況](research_state.json)。
- [索引変更記録](index_changes.json)、[文書監査](audit.py)、[監査結果](audit.json)、[公開対象ハッシュ](manifest.json)。

再計算はこのフォルダで python reproduce.py。Python標準ライブラリのみ。図の再生成はmatplotlib導入後に python draw.py。二図とも独自の仮計算であり、原著の図を転載していない。

物理試験0件、成功確率null。局部力の比と仮荷重比1.5は施工用の安全率ではない。正本はGitHub main、公開バイト照合後はローカル研究ファイルとGit履歴を削除する。
