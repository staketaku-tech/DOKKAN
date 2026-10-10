# DokkanDamageCalc

公開元: https://github.com/staketaku-tech/DOKKAN

`DOKKAN.py` を `streamlit run DOKKAN.py` で起動します。必要なパッケージは `requirements.txt` にあります。

- DEFの算出は元のDEFシミュレーターの式を共有しています。
- 属性補正・全属性ガード0.8はDEFを引く前、ガード0.5はDEFを引く後に適用します。
- 実戦タブは画面反映済み、被弾時、確認後の発動効果を区別し、被弾タイミングごとに比較します。
- 画面DEFからの再計算は端数差が出る場合があります。DEFタブの基礎ステータスを使用すると同じ式・同じ入力で一致します。
- 各行は代替的な被弾タイミングの比較です。限定効果の有効状態を入力し、被弾後の支援は発動後の行に入れてください。
- 0ダメージは2桁ダメージ相当です。乱数・属性防御UP・敵ATK変化などを網羅する厳密なゲーム再現ではありません。

ガード仕様の検証資料: https://xn--n9jvd7d3d0ad5cwnpcu694dohxad89g.com/archives/gwrgrw.html

テスト: `python -m unittest discover -s tests -v`
