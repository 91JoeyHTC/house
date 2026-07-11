-- 租屋地圖・共用標註 資料表 (在 Supabase 專案的 SQL Editor 執行)
create table if not exists annotations (
  listing_id text primary key,   -- 用物件原始連結當唯一鍵
  fav        boolean default false,
  note       text,
  lat        double precision,   -- 拖曳修正後的座標 (null = 用資料原始座標)
  lon        double precision,
  updated_at timestamptz default now()
);
-- 若資料表已存在,補上位置欄位 (重複執行安全)
alter table annotations add column if not exists lat double precision;
alter table annotations add column if not exists lon double precision;
alter table annotations enable row level security;
-- 允許匿名 anon 讀寫 (小型私人共用板;凡有網址+anon key 者皆可讀寫)
create policy "anon_read"   on annotations for select using (true);
create policy "anon_insert" on annotations for insert with check (true);
create policy "anon_update" on annotations for update using (true) with check (true);
