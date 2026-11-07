-- MOTICIAS · migración 001 · plataforma-v1 (borrador del 7-11-2026; se aplica en la fase 2 del cambio plataforma-v1)
-- Qué: tablas de la sala de redacción, suscriptores/CRM, leads, publicidad, señales compartidas y asesor, todas multi-vertical.
-- Por qué: ver openspec/changes/plataforma-v1/design.md. Nada específico de MOTICIAS: el vertical es un dato.
-- SE PUEDE APLICAR DOS VECES (todo es IF NOT EXISTS).

create extension if not exists pgcrypto;

create table if not exists verticals (
  id text primary key,
  name text not null,
  config jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now()
);

create table if not exists profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text not null,
  name text,
  role text not null default 'editor' check (role in ('superadmin','editor','comercial','anunciante')),
  vertical_ids text[] not null default '{}',
  created_at timestamptz not null default now()
);

create table if not exists editorial_items (
  id text not null,
  vertical_id text not null references verticals(id),
  kind text not null,
  status text not null default 'pendiente' check (status in ('borrador','pendiente','publicado','retirado')),
  priority int not null default 0,
  featured int not null default 0,
  approved_by uuid references profiles(id),
  approved_at timestamptz,
  ghost_post_id text,
  ghost_url text,
  published_at timestamptz,
  updated_at timestamptz not null default now(),
  primary key (vertical_id, id)
);

create table if not exists organizations (
  id uuid primary key default gen_random_uuid(),
  vertical_id text not null references verticals(id),
  name text not null,
  type text check (type in ('operador','administracion','consorcio','asociacion','consultora','industria','campus','prensa','otro')),
  region text,
  size text,
  licita boolean,
  website text,
  created_at timestamptz not null default now()
);

create table if not exists contacts (
  id uuid primary key default gen_random_uuid(),
  vertical_id text not null references verticals(id),
  email text not null,
  name text,
  org_id uuid references organizations(id),
  role text,
  source text check (source in ('ghost','brevo','formulario','manual')),
  consent_newsletter boolean not null default false,
  consent_group_offers boolean not null default false,
  consent_at timestamptz,
  tier text not null default 'lector' check (tier in ('lector','profesional','corporativa','anunciante')),
  ghost_member_id text,
  created_at timestamptz not null default now(),
  unique (vertical_id, email)
);

create table if not exists interests (
  contact_id uuid not null references contacts(id) on delete cascade,
  modo text,
  region text,
  topic text,
  weight real not null default 1,
  primary key (contact_id, modo, region, topic)
);

create table if not exists events (
  id bigserial primary key,
  contact_id uuid references contacts(id) on delete cascade,
  kind text not null check (kind in ('open','click','download','alert','visit','reply','request')),
  item_id text,
  topic text,
  at timestamptz not null default now(),
  meta jsonb not null default '{}'::jsonb
);
create index if not exists events_contact_at on events (contact_id, at desc);

create table if not exists leads (
  id uuid primary key default gen_random_uuid(),
  vertical_id text not null references verticals(id),
  contact_id uuid not null references contacts(id) on delete cascade,
  segment_id text not null,
  solution text not null,
  score real not null default 0,
  reason text,
  status text not null default 'nuevo' check (status in ('nuevo','contactado','reunion','propuesta','ganado','perdido')),
  owner uuid references profiles(id),
  updated_at timestamptz not null default now()
);

-- Campañas temáticas: plan editorial + solución + monetización + KPI sobre un tema con fecha.
-- El JSON de data/campanas/<id>.json es la fuente de verdad del plan; aquí, estado y resultados.
create table if not exists campanas_tematicas (
  id text not null,
  vertical_id text not null references verticals(id),
  name text not null,
  topic text,
  hook_date date,
  hook_verified boolean not null default false,
  start_date date,
  end_date date,
  status text not null default 'prevista' check (status in ('prevista','activa','cerrada')),
  segment_id text,
  solution text,
  monetization text not null default 'sin-publicidad' check (monetization in ('sin-publicidad','patrocinada','banner','mixta')),
  sponsor_advertiser_id uuid,
  kpis jsonb not null default '{}'::jsonb,
  results jsonb not null default '{}'::jsonb,
  owner text,
  updated_at timestamptz not null default now(),
  primary key (vertical_id, id)
);

create table if not exists advertisers (
  id uuid primary key default gen_random_uuid(),
  vertical_id text not null references verticals(id),
  org_id uuid references organizations(id),
  contact_id uuid references contacts(id),
  status text not null default 'activo'
);

create table if not exists campaigns (
  id uuid primary key default gen_random_uuid(),
  vertical_id text not null references verticals(id),
  advertiser_id uuid references advertisers(id),
  campana_id text,
  type text not null check (type in ('patrocinio','banner','contenido','edicion-a-medida','autopromocion')),
  name text not null,
  slots text[] not null default '{}',
  start_date date,
  end_date date,
  amount_eur numeric(10,2),
  status text not null default 'borrador' check (status in ('borrador','activo','pausado','terminado')),
  utm_campaign text,
  created_at timestamptz not null default now()
);

create table if not exists placements (
  id bigserial primary key,
  campaign_id uuid not null references campaigns(id) on delete cascade,
  slot text not null,
  item_id text,
  day date not null default current_date,
  impressions int not null default 0,
  clicks int not null default 0,
  unique (campaign_id, slot, item_id, day)
);

create table if not exists relaciones_solucion (
  vertical_id text not null references verticals(id),
  item_id text not null,
  solution text not null,
  segment_id text,
  motivo text,
  primary key (vertical_id, item_id, solution)
);

create table if not exists custom_editions (
  id text not null,
  vertical_id text not null references verticals(id),
  name text not null,
  owner_org_id uuid references organizations(id),
  filters jsonb not null default '{}'::jsonb,
  layout text not null default 'boletin',
  visibility text not null default 'oculto',
  schedule text,
  primary key (vertical_id, id)
);

create table if not exists senales (
  id uuid primary key default gen_random_uuid(),
  vertical_id text references verticals(id),
  at timestamptz not null default now(),
  source_url text,
  source_name text,
  kind text not null check (kind in ('noticia','norma','licitacion','nombramiento','incidente','riesgo','buena-practica','idea')),
  entities text[] not null default '{}',
  scope text,
  sentiment text check (sentiment in ('positivo','neutro','negativo')),
  relevance real not null default 0.5 check (relevance between 0 and 1),
  summary text,
  raw jsonb not null default '{}'::jsonb,
  used_by text[] not null default '{}'
);
alter table senales add column if not exists campana_id text;
create index if not exists senales_at on senales (at desc);
create index if not exists senales_entities on senales using gin (entities);

create table if not exists advisor_items (
  id uuid primary key default gen_random_uuid(),
  vertical_id text not null references verticals(id),
  week date not null,
  category text not null check (category in ('visibilidad','credibilidad','conocimiento','contactos','canales','ingresos')),
  title text not null,
  instruction text not null,
  priority int not null default 2,
  effort text not null default 'medio' check (effort in ('bajo','medio','alto')),
  status text not null default 'propuesto' check (status in ('propuesto','aceptado','hecho','descartado')),
  evidence text,
  created_at timestamptz not null default now()
);

create table if not exists metrics_daily (
  vertical_id text not null references verticals(id),
  day date not null,
  subscribers_by_tier jsonb not null default '{}'::jsonb,
  opens int not null default 0,
  clicks int not null default 0,
  leads_new int not null default 0,
  leads_by_solution jsonb not null default '{}'::jsonb,
  revenue_subs numeric(10,2) not null default 0,
  revenue_ads numeric(10,2) not null default 0,
  primary key (vertical_id, day)
);

-- Etiqueta de campaña temática en lo que se mide de punta a punta.
alter table editorial_items add column if not exists campana_id text;
alter table events add column if not exists campana_id text;
alter table leads add column if not exists campana_id text;
do $$ begin
  if not exists (select 1 from pg_constraint where conname = 'campanas_tematicas_sponsor_fk') then
    alter table campanas_tematicas add constraint campanas_tematicas_sponsor_fk
      foreign key (sponsor_advertiser_id) references advertisers(id);
  end if;
end $$;
create index if not exists events_campana on events (campana_id) where campana_id is not null;
create index if not exists leads_campana on leads (campana_id) where campana_id is not null;

-- RLS: todo cerrado por defecto; las políticas por rol llegan en la migración 002 con la sala de redacción.
do $$
declare t text;
begin
  for t in select unnest(array['verticals','profiles','editorial_items','organizations','contacts','interests','events','leads',
                               'campanas_tematicas','advertisers','campaigns','placements','relaciones_solucion','custom_editions','senales','advisor_items','metrics_daily'])
  loop
    execute format('alter table %I enable row level security', t);
  end loop;
end $$;
