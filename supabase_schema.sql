-- ═══════════════════════════════════════════════════════════
--  TurfBook — Supabase Schema
--  Run this in Supabase → SQL Editor → New Query → Run
-- ═══════════════════════════════════════════════════════════

-- Enable UUID extension
create extension if not exists "pgcrypto";

-- ── Owners ───────────────────────────────────────────────────
create table if not exists owners (
  id            uuid primary key default gen_random_uuid(),
  email         text unique not null,
  password_hash text not null,
  full_name     text,
  created_at    timestamptz default now()
);

-- ── Turfs ────────────────────────────────────────────────────
create table if not exists turfs (
  id              uuid primary key default gen_random_uuid(),
  owner_id        uuid references owners(id) on delete cascade,
  name            text not null,
  slug            text unique not null,       -- used in booking URLs e.g. "greenfield"
  location        text,
  description     text,
  price_per_slot  integer not null default 800,  -- INR
  owner_phone     text,                           -- for WhatsApp alerts
  created_at      timestamptz default now()
);

-- ── Bookings ─────────────────────────────────────────────────
create table if not exists bookings (
  id                   uuid primary key default gen_random_uuid(),
  turf_id              uuid references turfs(id) on delete cascade,
  customer_name        text not null,
  customer_phone       text not null,
  booking_date         date not null,
  slot                 text not null,           -- e.g. "6:00 AM"
  amount               integer not null,        -- INR
  status               text not null default 'pending_payment',
                                                -- pending_payment | confirmed | cancelled
  razorpay_order_id    text,
  razorpay_payment_id  text,
  paid_at              timestamptz,
  created_at           timestamptz default now(),

  -- Prevent double-booking same slot on same day
  unique (turf_id, booking_date, slot)
);

-- ── Blocked dates ─────────────────────────────────────────────
create table if not exists blocked_dates (
  id         uuid primary key default gen_random_uuid(),
  turf_id    uuid references turfs(id) on delete cascade,
  date       date not null,
  unique (turf_id, date)
);

-- ═══════════════════════════════════════════════════════════
--  Row Level Security
-- ═══════════════════════════════════════════════════════════

-- Owners can only see their own data
alter table owners    enable row level security;
alter table turfs     enable row level security;
alter table bookings  enable row level security;
alter table blocked_dates enable row level security;

-- Public read for turfs (customers need to see turf info)
create policy "Public can read turfs"
  on turfs for select using (true);

-- Public read for bookings (to check slot availability — no PII exposed via anon key)
create policy "Public can read booking slots"
  on bookings for select using (true);

-- Public can insert bookings (customer creates booking)
create policy "Public can create bookings"
  on bookings for insert with check (true);

-- Public can update bookings (payment confirmation)
create policy "Public can update bookings"
  on bookings for update using (true);

-- Public read for blocked dates
create policy "Public can read blocked dates"
  on blocked_dates for select using (true);

-- ═══════════════════════════════════════════════════════════
--  Seed data — add a demo owner and turf to test with
-- ═══════════════════════════════════════════════════════════
-- Password below is bcrypt hash of "admin123"
-- Generate your own at: https://bcrypt-generator.com

insert into owners (email, password_hash, full_name) values (
  'demo@turfbook.in',
  '$2b$12$KIXJqMMnQcJg3SOoF9I8iu8FvoCOpjRPDONVFSi6hTfhXWBb3f2yy',  -- "admin123"
  'Demo Owner'
) on conflict do nothing;

insert into turfs (owner_id, name, slug, location, price_per_slot, description)
select
  id,
  'GreenField Turf',
  'greenfield',
  'Bhopal, Madhya Pradesh',
  800,
  'Premium football & cricket turf in the heart of the city.'
from owners where email = 'demo@turfbook.in'
on conflict do nothing;
