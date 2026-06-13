import os
import random
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import google.generativeai as genai

PROGRAMS_DIR = Path("programs")

PROMPT = """情報工学の学習テーマを1つ自由に選び、Pythonプログラムを生成してください。

テーマ候補（これ以外でもOK）:
- ソートアルゴリズム（バブル、マージ、クイック、ヒープ、基数など）
- データ構造（スタック、キュー、連結リスト、二分探索木、AVL木、ハッシュテーブルなど）
- グラフアルゴリズム（BFS、DFS、ダイクストラ、ベルマンフォード、クラスカルなど）
- 数学・数値計算（素数判定、最大公約数、行列演算、高速フーリエ変換など）
- 文字列アルゴリズム（KMP法、ラビンカープ、トライ木、サフィックス配列など）
- 動的計画法（ナップサック問題、最長共通部分列、編集距離など）
- 機械学習基礎（パーセプトロン、k-NN、k-means、線形回帰など）
- 暗号・セキュリティ（Caesar暗号、RSA基礎、ハッシュ関数の仕組みなど）
- シミュレーション（ライフゲーム、モンテカルロ法、シミュレーテッドアニーリングなど）

条件:
- 完全に動作するコードであること
- コメントで処理の説明を入れること（日本語OK）
- 50〜200行程度

以下の形式で回答してください（この形式を厳守）:

FILE: <スネークケースのファイル名.py>
COMMIT: <英語のコミットメッセージ（動詞で始める例: Add merge sort with step-by-step visualization）>

```python
# コードをここに書く
```
"""


def generate_one() -> tuple[str, str, str]:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-2.0-flash")

    response = model.generate_content(PROMPT)
    text = response.text

    filename_match = re.search(r"^FILE:\s*(\S+\.py)", text, re.MULTILINE)
    filename = (
        filename_match.group(1).strip()
        if filename_match
        else f"program_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
    )

    commit_match = re.search(r"^COMMIT:\s*(.+)", text, re.MULTILINE)
    commit_msg = (
        commit_match.group(1).strip()
        if commit_match
        else f"Add {filename.replace('.py', '').replace('_', ' ')}"
    )

    code_match = re.search(r"```python\n(.*?)```", text, re.DOTALL)
    if not code_match:
        print("Error: コードブロックが見つかりませんでした", file=sys.stderr)
        print(text, file=sys.stderr)
        sys.exit(1)

    return filename, code_match.group(1), commit_msg


def run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    if result.stdout.strip():
        print(result.stdout)


def main() -> None:
    skip_chance = float(os.environ.get("SKIP_CHANCE", "0"))
    if random.random() < skip_chance:
        print("今日はスキップします")
        return

    count = random.choices([1, 2, 3, 4], weights=[40, 30, 20, 10])[0]
    print(f"今日は {count} 個生成します")

    PROGRAMS_DIR.mkdir(exist_ok=True)

    for i in range(count):
        print(f"\n--- {i + 1}/{count} 個目を生成中 ---")
        filename, code, commit_msg = generate_one()

        filepath = PROGRAMS_DIR / filename
        if filepath.exists():
            suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = PROGRAMS_DIR / f"{filepath.stem}_{suffix}.py"

        filepath.write_text(code, encoding="utf-8")
        print(f"生成: {filepath}")

        run(["git", "add", str(filepath)])
        run(["git", "commit", "-m", commit_msg])
        print(f"コミット: {commit_msg}")

    run(["git", "pull", "--rebase"])
    run(["git", "push"])
    print(f"\n完了！{count} 個のプログラムをコミットしました")


if __name__ == "__main__":
    main()
