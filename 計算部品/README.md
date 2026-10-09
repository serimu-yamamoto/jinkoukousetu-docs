# 再利用する計算部品

- [restoration_process.py](restoration_process.py)：保持水切りと分流復旧の収支。[第107巡](../GPT往復/分流水切りと60分復旧の成立条件_20261010/README.md)。実機能力・実物損傷未検証。

- [rim_grain_hex.py](rim_grain_hex.py)：環粒のHex8弾性と開口の毛管圧尺度。[第106巡](../GPT往復/開放環粒の三次元支持と毛管残水の比較_20261010/README.md)。大窓メッシュ未収束。

- [formation_routes.py](formation_routes.py)：環粒の幾何、乾燥・延べ加工・原料回収の収支。[第105巡](../GPT往復/温暖形成と開放環粒の製造監査_20261010/README.md)。

- [flared_ligament.py](flared_ligament.py)：可変幅支柱のQ4平面応力、断面と局所流路の積分。[第104巡](../GPT往復/拡大流路と支持剛性の連成監査_20261010/README.md)。

- [graded_contact.py](graded_contact.py)：区分一次剛性と自由回転の片側接触。handover_contacts.pyの幾何を再利用。[第103巡](../GPT往復/受け面の剛性勾配と薄枝実現条件の検証_20261010/README.md)。

- [handover_contacts.py](handover_contacts.py)：第102巡の圧縮のみの局所接触・重なり面積・曲面受渡し。標準ライブラリのみ。50℃や実粒の物性は未較正。
- [入力・再現・限界](../GPT往復/曲面補償と面積受渡しの有限形状検証_20261010/README.md)。正本はこのGitHub。サーバーの ~/firn/lib へ展開して利用できる。今回の作業用コピーは公開照合後に削除する。
