#!/usr/bin/env bash
# 更新後一鍵推上線:在 ~/repos/home 執行  ->  bash push.sh
# (保留 git 歷史;推到 github.com/91JoeyHTC/house 的 main 分支,GitHub Pages 會自動重建)
set -e
cd "$(dirname "$0")"
python3 build.py                       # 由 租屋彙整.csv 重新產生 index.html
git add -A
git commit -m "更新租屋資料" || echo "(沒有變更,略過 commit)"
git push origin main
echo "✅ 已推送。GitHub Pages 幾分鐘後更新:https://91joeyhtc.github.io/house/"
