# 淡水 / 北投 租屋地圖

整層住家 · 租金 15,000–30,000 · 資料抓自 591、永慶、信義。
互動地圖:依網站上色、可篩選(網站/地區/電梯/車位/租金上限/通勤上限)、可標註 ★ 收藏與備註、可拖曳修正標點位置。

---

## 定期更新物件(推薦流程)

不建議寫爬蟲自動抓 591/永慶/信義(無穩定 API、易被擋、常改版)。改用半自動:

1. 在 591/永慶設「儲存搜尋條件」,隔幾天看新上架的,把新物件貼進 `租屋彙整.csv`
   (欄位:網站,地區,標題,租金,坪數,樓層,格局,地址,電梯,車位,連結)
2. 執行一次:
   ```
   python3 build.py
   ```
3. `index.html` 就會自動更新。commit + push 即上線。

`build.py` 會自動:
- **用「連結」去重**——反覆貼同一物件也安全
- **地理編碼**——新地址才連 OpenStreetMap Nominatim(免費),結果存 `geocode_cache.json`,舊地址不重抓
- **穩定微幅分散**同路段物件,避免完全重疊

> 你的 ★ 收藏、備註、拖曳修正過的座標都存在瀏覽器(以「連結」為 key),重跑 `build.py` **不會**被清掉。

---

## 通勤時間(選用)

編輯 `build.py` 最上方的 `COMMUTE`:

```python
COMMUTE = {
    "dest_name": "台北車站",   # 目的地(留名稱即可,腳本會自動查座標)
    "dest_lat":  None,
    "dest_lon":  None,
    "ors_key":   "貼上 OpenRouteService 免費金鑰",   # 開車/騎車用
    "google_key":"貼上 Google Maps 金鑰",           # 大眾運輸用
    "modes":     ["drive", "transit"],
}
```

- **開車 / 騎車**:到 [openrouteservice.org](https://openrouteservice.org) 免費註冊拿 key(填 `ors_key`)。
- **大眾運輸**:到 Google Cloud 啟用 **Directions API** 拿 key(填 `google_key`)。一次算 250 筆約 $1.25,Google 每月送 $200 額度,實質免費。

填好後 `python3 build.py`,每筆物件會多出通勤分鐘數,地圖上會多一個「通勤上限」滑桿,popup 也會顯示 🚗/🚇 分鐘。金鑰留空則跳過該模式。

---

## 修改地圖上的標示位置

座標是路段級近似。要校正:

1. 在左側勾選 **「調整位置模式」**
2. 放大地圖,把標點**拖曳**到正確位置——放開即自動儲存
3. 想還原:點該物件 popup 的 **「↺ 重設位置」**

修正過的位置以「連結」為 key,更新資料(重跑 build.py)時會保留。

---

## 上線(GitHub Pages)

Settings → Pages → Source 選 `main` 分支 `/ (root)` → 儲存,幾分鐘後開
`https://91JoeyHTC.github.io/house/`。

## 多人 / 多裝置共用標註(選用)

1. 到 [supabase.com](https://supabase.com) 建免費專案。
2. SQL Editor 執行 `supabase_setup.sql`(含收藏、備註、位置修正)。
3. Project Settings → API 複製 `Project URL` 與 `anon public` key。
4. 編輯 `index.html` 最上方 `const CLOUD={url:"", key:""};`,填入兩個值。
5. 重新 commit——標註/備註/位置修正即多裝置同步。金鑰留空則為單機模式。
