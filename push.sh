#!/usr/bin/env bash
# 一鍵推送到 GitHub:在 ~/repos/home 執行  ->  bash push.sh
set -e
cd "$(dirname "$0")"
rm -rf .git                      # 清掉沙箱建立的殘缺 .git
git init -q
git add index.html README.md supabase_setup.sql 租屋彙整.csv build.py geocode_cache.json
git commit -q -m "淡水/北投租屋互動地圖 (整層住家 15000-30000)"
git branch -M main
git remote add origin https://github.com/91JoeyHTC/house.git
git push -u origin main
echo "✅ 已推送。接著到 GitHub repo → Settings → Pages,Source 選 main / (root),"
echo "   幾分鐘後開 https://91JoeyHTC.github.io/house/"
