# 第24巡の再計算資料

[報告書](../GPT回答_多方向探索第24巡_枝状結晶と結晶相を使い分ける粒の製造再生_20261008.md)を先に読む。物理試験は0件。計算は製造と再生の条件・質量収支で、雪状性能や成功確率を予測しない。

## 再現

Python標準ライブラリで計算できる。図はmatplotlib3.11.2を使用。リポジトリのルートで実行する。以下のpythonは利用環境のPython実行ファイルへ読み替える。

```powershell
rtk summary python -X utf8 "GPT往復/結晶形成検証_相分率と製造再生_20261008/calculate.py"
rtk summary python -m pip install --target .deps matplotlib==3.11.2
rtk summary python -X utf8 "GPT往復/結晶形成検証_相分率と製造再生_20261008/plot.py"
```

## 内容

- [inputs.json](inputs.json)：引用値・仮定・単位・H24-A/Bの配合差を明記。
- [calculate.py](calculate.py)：液量、捕集外の再利用、仮原価、熱量、相の変化、共通予算。
- [results.json](results.json)：全条件。H24-Bの熱量は高価相を除いた母材量で独立再計算。
- [validation.json](validation.json)：23項目の数値整合照合と未検証事項。物理試験の合格数ではない。
- [plot.py](plot.py)：元データから2図を生成。図は計算結果。
- [液処理と熱量の図](01_recipe_and_heat.png)、[相分率と費用の図](02_phase_and_cost.png)。
- [sources.md](sources.md)：一次資料7件と確認範囲、矛盾・未取得項目。
- [publication-manifest.json](publication-manifest.json)：今回の公開対象のSHA256。自己参照を避け、このmanifest自身は一覧外。

## モデルの境界

20液量・180製造原価・9少量相費用・12H24-A熱条件・60熱拡散尺度・40相変化・108H24-B材料と熱費の条件を計算。入力の組合せの数は成功率を構成しない。

濃度w/vとwt％、処理総量と槽容量、新規材料と工程内循環、廃棄管理量と環境放出、粒の加熱回数とコース整地回数を区別した。H24-Aの低融点相10％をH24-Bの低融点母材95％の例へ流用しない。熱回収・歩留まり・相変換率・単価は適用根拠のない値を実測扱いしない。

図の作成にだけ使う.depsとGit作業情報は公開対象外。ユーザー指定に従い、公開照合後のローカル作業クローンを削除する。
