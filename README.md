# 淡水 / 北投 租屋地圖

整層住家 · 租金 15,000–30,000 · 資料抓自 591、永慶、信義。
互動地圖:依網站上色、可篩選(網站/地區/電梯/車位/租金上限)、可標註 ★ 收藏與備註。

## 上線 (GitHub Pages)
Settings → Pages → Source 選 `main` 分支 `/ (root)` → 儲存,幾分鐘後即可用
`https://91JoeyHTC.github.io/house/` 開啟。

## 多人共用標註 (選用)
1. 到 supabase.com 建免費專案。
2. SQL Editor 執行 `supabase_setup.sql`。
3. Project Settings → API 複製 `Project URL` 與 `anon public` key。
4. 編輯 `index.html`,找到最上方 `const CLOUD={url:"", key:""};`,填入兩個值。
5. 重新 commit,線上版即多裝置/多人同步標註。金鑰留空則為單機模式。
