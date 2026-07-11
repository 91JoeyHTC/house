-- 租屋地圖・共用標註 資料表 (在 Supabase 專案的 SQL Editor 執行)
create table if not exists annotations (
  listing_id text primary key,   -- 用物件原始連結當唯一鍵
  fav        boolean default false,
  note       text,
  updated_at timestamptz default now()
);
alter table annotations enable row level security;
-- 允許匿名 anon 讀寫 (小型私人共用板;凡有網址+anon key 者皆可讀寫)
create policy "anon_read"   on annotations for select using (true);
create policy "anon_insert" on annotations for insert with check (true);
create policy "anon_update" on annotations for update using (true) with check (true);
