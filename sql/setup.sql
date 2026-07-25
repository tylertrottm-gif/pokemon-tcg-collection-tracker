-- Run this script in the Supabase SQL Editor.
-- This MVP stores one private collection and does not yet include user accounts.

create table if not exists public.collection_items (
    card_id text primary key,
    card_name text not null,
    set_id text not null,
    set_name text not null,
    card_number text,
    rarity text,
    image_small text,
    quantity integer not null default 1 check (quantity > 0),
    date_added timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists collection_items_set_id_idx
    on public.collection_items (set_id);

create index if not exists collection_items_set_name_idx
    on public.collection_items (set_name);

grant usage on schema public to anon;
grant select, insert, update, delete on table public.collection_items to anon;

alter table public.collection_items enable row level security;

-- The Streamlit app uses the Supabase anon key stored in Streamlit secrets.
-- These policies permit that role to manage this single collection.
drop policy if exists "Collection items are readable" on public.collection_items;
create policy "Collection items are readable"
on public.collection_items
for select
to anon
using (true);

drop policy if exists "Collection items are insertable" on public.collection_items;
create policy "Collection items are insertable"
on public.collection_items
for insert
to anon
with check (true);

drop policy if exists "Collection items are updateable" on public.collection_items;
create policy "Collection items are updateable"
on public.collection_items
for update
to anon
using (true)
with check (true);

drop policy if exists "Collection items are deletable" on public.collection_items;
create policy "Collection items are deletable"
on public.collection_items
for delete
to anon
using (true);
