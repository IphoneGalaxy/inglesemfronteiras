-- ============================================================
-- EnglishFlow — Schema Supabase (Postgres)
-- Corrigido conforme review GLM 5.2
-- Execute no SQL Editor do Supabase:
-- https://rrfnfqlijjirxonhtpde.supabase.co
-- ============================================================

-- 1. EXTENSIONS
create extension if not exists "uuid-ossp";

-- 2. ENUM TYPES (CHECK constraints)
-- N/A — usando TEXT + CHECK para compatibilidade

-- 3. TABLES

-- Users (independente — login via access_code)
create table if not exists public.users (
    id          uuid primary key default uuid_generate_v4(),
    telegram_id text unique,
    name        text not null,
    plan        text not null default 'basico' check (plan in ('basico','pro','premium','todos')),
    access_code text unique not null,
    email       text,
    is_staff    boolean default false,
    plan_expires_at timestamptz,
    created_at  timestamptz default now(),
    active      boolean default true
);

-- Materials
create table if not exists public.materials (
    id          serial primary key,
    title       text not null,
    description text default '',
    filename    text,
    file_type   text default 'pdf' check (file_type in ('pdf','video','audio','image','other')),
    plan_level  text default 'todos' check (plan_level in ('todos','basico','pro','premium')),
    user_id     uuid references public.users(id),  -- se preenchido → exclusivo para este aluno
    created_at  timestamptz default now(),
    updated_at  timestamptz default now()
);

-- Material Progress
create table if not exists public.material_progress (
    id            serial primary key,
    user_id       uuid not null references public.users(id),
    material_id   integer not null references public.materials(id) on delete cascade,
    completed     boolean default false,
    completed_at  timestamptz,
    unique(user_id, material_id)
);

-- Payments
create table if not exists public.payments (
    id            serial primary key,
    user_id       uuid references public.users(id),
    plan          text check (plan in ('basico','pro','premium')),
    amount        numeric(10,2) not null,  -- ✅ C1 corrigido: NUMERIC em vez de REAL
    pix_code      text,
    status        text default 'pending' check (status in ('pending','confirmed','rejected')),
    provider_txid text unique,             -- ✅ A3: idempotência
    confirmed_at  timestamptz,
    created_at    timestamptz default now(),
    updated_at    timestamptz default now()
);

-- 4. INDEXES (✅ A4)
create index if not exists idx_users_telegram    on public.users(telegram_id);
create index if not exists idx_users_access_code on public.users(access_code);
create index if not exists idx_materials_user    on public.materials(user_id);
create index if not exists idx_progress_user     on public.material_progress(user_id);
create index if not exists idx_progress_material on public.material_progress(material_id);
create index if not exists idx_payments_user     on public.payments(user_id);
create index if not exists idx_payments_status   on public.payments(status);

-- 5. SECURITY DEFINER FUNCTION (✅ C3 — RLS cross-table para materials)
create or replace function public.user_can_see_material(mat_id integer)
returns boolean
language sql
security definer
stable
as $$
    select exists (
        select 1 from public.materials m
        join public.users u on u.id = auth.uid()
        where m.id = mat_id
          and (
              m.plan_level = 'todos'
              or m.plan_level = u.plan
              or m.user_id = auth.uid()
          )
    );
$$;

-- 6. ROW LEVEL SECURITY

-- Users
alter table public.users enable row level security;

create policy "Usuarios veem propria row"
    on public.users for select
    using (id = auth.uid() or is_staff = true);

create policy "Staff ve todos"
    on public.users for select
    using (is_staff = true);

create policy "Service role gerencia users"  -- bot via service_role
    on public.users for all
    using (true)
    with check (true);

-- Materials (✅ A1: write policies)
alter table public.materials enable row level security;

create policy "Qualquer um ve materiais do seu plano"
    on public.materials for select
    using (public.user_can_see_material(id));

create policy "Staff insere materiais"
    on public.materials for insert
    with check (
        exists (select 1 from public.users where id = auth.uid() and is_staff = true)
        or auth.role() = 'service_role'
    );

create policy "Staff atualiza materiais"
    on public.materials for update
    using (
        exists (select 1 from public.users where id = auth.uid() and is_staff = true)
    )
    with check (
        exists (select 1 from public.users where id = auth.uid() and is_staff = true)
    );

create policy "Staff deleta materiais"
    on public.materials for delete
    using (
        exists (select 1 from public.users where id = auth.uid() and is_staff = true)
    );

-- Material Progress (✅ A1)
alter table public.material_progress enable row level security;

create policy "Usuario gerencia proprio progresso"
    on public.material_progress for all
    using (user_id = auth.uid())
    with check (user_id = auth.uid());

-- Payments
alter table public.payments enable row level security;

create policy "Usuario ve proprios pagamentos"
    on public.payments for select
    using (user_id = auth.uid());

create policy "Staff ve todos pagamentos"
    on public.payments for select
    using (
        exists (select 1 from public.users where id = auth.uid() and is_staff = true)
    );

-- 7. STORAGE BUCKET (✅ M1)
-- Execute separadamente se bucket não existir:
-- insert into storage.buckets (id, name, public) values ('materiais', 'materiais', false);

-- 8. FUNCTIONS
-- Trigger: updated_at
create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

create trigger materials_updated_at
    before update on public.materials
    for each row execute function public.set_updated_at();

create trigger payments_updated_at
    before update on public.payments
    for each row execute function public.set_updated_at();
