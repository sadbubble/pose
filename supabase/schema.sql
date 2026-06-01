-- POSE — run once in Supabase SQL Editor (free tier, no credit card)
-- Dashboard → SQL → New query → paste → Run

create table if not exists events (
  id text primary key,
  type text not null default 'party',
  name text not null,
  date text,
  time text,
  location text,
  description text,
  host text,
  style text default 'gradient',
  poster text default '',
  font text default 'grotesk',
  kaspi text default '',
  questions text default '[]',
  created_at timestamptz not null default now()
);

create table if not exists rsvps (
  id text primary key,
  event_id text not null references events(id) on delete cascade,
  name text not null,
  status text not null check (status in ('going', 'maybe', 'cant')),
  avatar int default 1,
  answers text default '{}',
  created_at timestamptz not null default now()
);

create table if not exists comments (
  id text primary key,
  event_id text not null references events(id) on delete cascade,
  name text not null,
  text text not null,
  avatar int default 1,
  reactions text default '{}',
  created_at timestamptz not null default now()
);

create table if not exists updates (
  id text primary key,
  event_id text not null references events(id) on delete cascade,
  text text not null,
  created_at timestamptz not null default now()
);

alter table events enable row level security;
alter table rsvps enable row level security;
alter table comments enable row level security;
alter table updates enable row level security;

create policy "events_select" on events for select using (true);
create policy "events_insert" on events for insert with check (true);
create policy "rsvps_all" on rsvps for all using (true) with check (true);
create policy "comments_all" on comments for all using (true) with check (true);
create policy "updates_all" on updates for all using (true) with check (true);
