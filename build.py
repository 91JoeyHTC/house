#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
租屋地圖・一鍵更新腳本
---------------------------------
流程:  更新 租屋彙整.csv  ->  python3 build.py  ->  index.html 自動更新

會做的事:
  1. 讀 租屋彙整.csv (utf-8-sig)
  2. 用「連結」去重 (反覆貼進同一物件也安全)
  3. 地理編碼: 先查 geocode_cache.json,只有新地址才連 OpenStreetMap Nominatim
     (免費、每秒 1 次,結果寫回快取;舊地址永遠不重抓)
  4. 依「連結」做穩定微幅分散,避免同路段物件完全重疊
  5. (選用) 幫每個「常用目的地」算通勤時間;地圖上會出現目的地下拉可即時切換
  6. 把新的 DATA 與目的地清單寫回 index.html

你手動的 ★ 收藏、備註、拖曳修正過的座標都存在瀏覽器 (key = 連結),
重跑本腳本不會被清掉。
"""
import csv, json, re, sys, time, hashlib, urllib.parse, urllib.request, os

HERE = os.path.dirname(os.path.abspath(__file__))
CSV_FILE   = os.path.join(HERE, "租屋彙整.csv")
HTML_FILE  = os.path.join(HERE, "index.html")
CACHE_FILE = os.path.join(HERE, "geocode_cache.json")

# ===================== CONFIG (通勤計算用,不填則跳過) =====================
COMMUTE = {
    # 常用目的地清單 —— 地圖上會變成下拉選單,可即時切換看不同地點的通勤。
    # name 必填;lat/lon 留 None 會自動查 (查一次就寫進 geocode_cache.json)。
    "destinations": [
        {"name": "克立淨", "addr": "台北市大安區樂業街13號"},
        {"name": "愛馬斯", "addr": "新北市中和區橋和路13號"},
        {"name": "雙連站", "addr": "台北捷運雙連站"},
        # 想加新地點: 複製一行,name 是下拉顯示的短名,addr 是查座標用的地址
    ],
    # OpenRouteService 免費金鑰 (開車/騎車);到 openrouteservice.org 註冊
    "ors_key":    "",
    # Google Maps 金鑰 (大眾運輸 transit;啟用 Directions API);每月 $200 免費額度足夠
    "google_key": "",
    # 要算哪些模式: "drive"/"cycle" 需 ors_key;"transit" 需 google_key
    "modes":      ["drive", "transit"],
}
# =========================================================================

NOMINATIM = "https://nominatim.openstreetmap.org/search"
UA = "rental-map-builder/1.0 (personal use)"

def load_cache():
    if os.path.exists(CACHE_FILE):
        return json.load(open(CACHE_FILE, encoding="utf-8"))
    return {}

def save_cache(cache):
    json.dump(cache, open(CACHE_FILE, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

def _nominatim(q):
    """單次查詢,回傳 (lat,lon) 或 None。"""
    url = NOMINATIM + "?" + urllib.parse.urlencode(
        {"q": q, "format": "json", "limit": 1, "countrycodes": "tw"})
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    res = json.load(urllib.request.urlopen(req, timeout=15))
    time.sleep(1.1)  # Nominatim 禮貌限速: 每秒 <=1 次
    if res:
        return (float(res[0]["lat"]), float(res[0]["lon"]))
    return None

def geocode(addr, cache):
    """回傳 (lat, lon);查不到回 None。含門牌號查不到時退化成路名層級再試。"""
    addr = (addr or "").strip()
    if not addr:
        return None
    if addr in cache:
        c = cache[addr]
        return (c["lat"], c["lon"])
    base = addr.replace("-", " ").strip()
    if "淡水" in base:
        base = "新北市 " + base
    elif "北投" in base and "台北" not in base:
        base = "台北市 " + base
    # 路名層級 (去掉 巷/弄/號/樓 等門牌細節,Nominatim 對台灣門牌常查不到)
    street = re.sub(r"(\d+\s*(號|樓|巷|弄|之\d+)).*$", "", base).strip()
    candidates = [base]
    if street and street != base:
        candidates.append(street)
    for q in candidates:
        try:
            r = _nominatim(q)
        except Exception as e:
            print(f"  ✗ 編碼錯誤 ({q}): {e}", file=sys.stderr)
            r = None
        if r:
            cache[addr] = {"lat": r[0], "lon": r[1], "src": "nominatim", "q": q}
            save_cache(cache)
            note = "" if q == base else f" (以路名 '{q}' 命中)"
            print(f"  ✓ 新地址已編碼: {addr} -> {r[0]:.5f},{r[1]:.5f}{note}")
            return r
    return None

def jitter(link, lat, lon):
    """依連結做穩定的小位移 (±~40m),同地址不同物件不會完全疊住。"""
    h = int(hashlib.md5((link or "").encode()).hexdigest(), 16)
    dlat = ((h        % 1000) / 1000 - 0.5) * 0.0007
    dlon = (((h >> 10) % 1000) / 1000 - 0.5) * 0.0007
    return round(lat + dlat, 6), round(lon + dlon, 6)

# ----------------------------- 通勤計算 -----------------------------------
def transit_seconds(coords, dlat, dlon):
    """大眾運輸秒數 (Google Directions);逐筆查,回傳 [秒 或 None,...]。"""
    key = COMMUTE["google_key"]
    if not key:
        print("    · transit 略過 (未填 google_key)")
        return [None] * len(coords)
    secs = []
    for i, (lat, lon) in enumerate(coords):
        url = "https://maps.googleapis.com/maps/api/directions/json?" + urllib.parse.urlencode({
            "origin": f"{lat},{lon}", "destination": f"{dlat},{dlon}",
            "mode": "transit", "key": key, "language": "zh-TW"})
        try:
            r = json.load(urllib.request.urlopen(url, timeout=20))
            legs = (r.get("routes") or [{}])[0].get("legs")
            secs.append(legs[0]["duration"]["value"] if legs else None)
        except Exception as e:
            print(f"    ✗ transit 第{i}筆失敗: {e}", file=sys.stderr)
            secs.append(None)
        time.sleep(0.05)
    print(f"    ✓ transit 完成 {len([s for s in secs if s])}/{len(coords)} 筆")
    return secs

def road_seconds(coords, dlat, dlon, mode):
    """開車/騎車秒數 (OpenRouteService matrix);回傳 [秒 或 None,...]。"""
    if not COMMUTE["ors_key"]:
        print(f"    · {mode} 略過 (未填 ors_key)")
        return [None] * len(coords)
    profile = {"drive": "driving-car", "cycle": "cycling-regular"}[mode]
    locations = [[c[1], c[0]] for c in coords] + [[dlon, dlat]]
    body = json.dumps({
        "locations": locations,
        "sources": list(range(len(coords))),
        "destinations": [len(coords)],
        "metrics": ["duration"],
    }).encode()
    req = urllib.request.Request(
        f"https://api.openrouteservice.org/v2/matrix/{profile}", data=body,
        headers={"Authorization": COMMUTE["ors_key"], "Content-Type": "application/json"})
    try:
        r = json.load(urllib.request.urlopen(req, timeout=60))
        durs = r.get("durations", [])
        secs = [row[0] if row and row[0] is not None else None for row in durs]
        print(f"    ✓ {mode} 完成 {len([s for s in secs if s])}/{len(coords)} 筆")
        return secs
    except Exception as e:
        print(f"    ✗ {mode} 失敗: {e}", file=sys.stderr)
        return [None] * len(coords)

def compute_commute(data, cache):
    """幫每個目的地、每個模式算通勤,寫進 d['通勤'][目的地][模式] = 分鐘。回傳目的地名清單。"""
    coords = [(d["lat"], d["lon"]) for d in data]
    names = []
    for dest in COMMUTE["destinations"]:
        name = dest.get("name", "").strip()
        if not name:
            continue
        dlat, dlon = dest.get("lat"), dest.get("lon")
        if dlat is None or dlon is None:
            g = geocode(dest.get("addr") or name, cache)
            if not g:
                print(f"  ✗ 目的地無法編碼,略過: {name}")
                continue
            dlat, dlon = g
            print(f"  ✓ 目的地 '{name}' 座標: {dlat:.5f},{dlon:.5f}")
        print(f"  → 計算通勤到「{name}」")
        got_any = False
        for d in data:
            d.setdefault("通勤", {})[name] = {}
        for mode in COMMUTE["modes"]:
            if mode == "transit":
                secs = transit_seconds(coords, dlat, dlon)
            elif mode in ("drive", "cycle"):
                secs = road_seconds(coords, dlat, dlon, mode)
            else:
                continue
            for d, s in zip(data, secs):
                if s is not None:
                    d["通勤"][name][mode] = round(s / 60)
                    got_any = True
        if got_any:
            names.append(name)
        else:  # 沒算到 (通常是還沒填金鑰) -> 移除空殼,地圖就不會顯示空的通勤選單
            for d in data:
                d["通勤"].pop(name, None)
    return names

# ----------------------------- 主流程 -------------------------------------
def main():
    cache = load_cache()
    rows = list(csv.DictReader(open(CSV_FILE, encoding="utf-8-sig")))
    print(f"CSV 讀入 {len(rows)} 筆")

    seen, data = set(), []
    for r in rows:
        r = {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in r.items()}
        link = r.get("連結", "")
        key = link or f"{r.get('標題')}|{r.get('地址')}"
        if key in seen:
            continue
        seen.add(key)
        geo = geocode(r.get("地址", ""), cache)
        if not geo:
            print(f"  · 跳過 (無座標): {r.get('標題')}")
            continue
        lat, lon = jitter(link, geo[0], geo[1])
        r["lat"], r["lon"] = lat, lon
        data.append(r)
    print(f"去重+編碼後: {len(data)} 筆")

    dest_names = compute_commute(data, cache)
    save_cache(cache)

    # 寫回 index.html
    html = open(HTML_FILE, encoding="utf-8").read()
    new_data = "const DATA=" + json.dumps(data, ensure_ascii=False) + ";"
    html, n = re.subn(r"const DATA=\[.*?\];", lambda m: new_data, html,
                      count=1, flags=re.S)
    if n != 1:
        print("✗ 找不到 index.html 裡的 const DATA=[...]; 無法寫入", file=sys.stderr)
        sys.exit(1)
    dests_js = "const COMMUTE_DESTS=" + json.dumps(dest_names, ensure_ascii=False) + ";"
    html, _ = re.subn(r"const COMMUTE_DESTS=\[.*?\];", lambda m: dests_js, html, count=1)
    open(HTML_FILE, "w", encoding="utf-8").write(html)
    print(f"✅ index.html 已更新 ({len(data)} 筆物件"
          + (f",通勤目的地: {', '.join(dest_names)}" if dest_names else "") + ")")

if __name__ == "__main__":
    main()
