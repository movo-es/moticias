-- MOTICIAS · migración 002 · plataforma-2027 (borrador del 8-11-2026; cada cambio hijo aplica solo su parte)
-- Qué: sala de prensa, datasets de segundo nivel, cargos «Quién decide», motor de envíos, auscultador y PLUS.
-- El esquema `conocimiento` (pgvector) va en la migración 003 del cambio conocimiento-v1, porque es compartido con MOVO.
-- SE PUEDE APLICAR DOS VECES (todo es IF NOT EXISTS). RLS y políticas por rol se añaden en cada hijo.

-- Sala de prensa
create table if not exists press_releases (
  id uuid primary key default gen_random_uuid(),
  vertical_id text not null references verticals(id),
  org_id uuid references organizations(id),
  contact_id uuid references contacts(id),
  title text not null,
  body_md text not null,
  attachments jsonb not null default '[]'::jsonb,
  status text not null default 'recibida' check (status in ('recibida','publicada','retirada')),
  verified_at timestamptz,
  ghost_post_id text,
  ghost_url text,
  assessment jsonb,
  distribution jsonb,
  received_at timestamptz not null default now(),
  published_at timestamptz
);

-- Fuentes de segundo nivel: registros estructurados
create table if not exists datasets (
  id bigserial primary key,
  vertical_id text not null references verticals(id),
  dataset text not null,            -- subvenciones | contratos | nombramientos | preguntas | fiscalizacion | ...
  source_id text not null,          -- id en portal/data/sources.json
  ref text,                         -- referencia oficial (BDNS, expediente, BOE-A-...)
  date date,
  fields jsonb not null default '{}'::jsonb,
  url text,
  created_at timestamptz not null default now(),
  unique (vertical_id, dataset, source_id, ref)
);

-- Quién decide
create table if not exists cargos (
  id uuid primary key default gen_random_uuid(),
  vertical_id text not null references verticals(id),
  org_id uuid references organizations(id),
  persona text not null,
  cargo text not null,
  desde date,
  hasta date,
  email_profesional text,
  tel_profesional text,
  verificado_en date,
  vigente boolean not null default true
);
create table if not exists cargo_fuentes (
  cargo_id uuid not null references cargos(id) on delete cascade,
  tipo text not null check (tipo in ('boe','boletin','borme','web-oficial','comunicado')),
  url text not null,
  fecha date,
  primary key (cargo_id, url)
);

-- Motor de envíos
create table if not exists plantillas (
  id text primary key,
  vertical_id text not null references verticals(id),
  canal text not null check (canal in ('email','sms','whatsapp','voz')),
  nombre text not null,
  cuerpo text not null,
  aprobada_meta boolean not null default false,  -- WhatsApp
  cliente_id uuid,
  updated_at timestamptz not null default now()
);
create table if not exists secuencias (
  id uuid primary key default gen_random_uuid(),
  vertical_id text not null references verticals(id),
  plan_id uuid,
  nombre text not null,
  pasos jsonb not null default '[]'::jsonb,  -- [{orden, audiencia_id|segmento, canales[], plantilla_id, avance:{tipo: tiempo|acuses|aprobacion, valor}}]
  updated_at timestamptz not null default now()
);
create table if not exists ejecuciones (
  id uuid primary key default gen_random_uuid(),
  secuencia_id uuid not null references secuencias(id),
  tipo text not null default 'real' check (tipo in ('real','simulacro')),
  lanzada_por uuid references profiles(id),
  estado text not null default 'en-curso' check (estado in ('en-curso','pausada','terminada','cancelada')),
  paso_actual int not null default 0,
  workflow_run_id text,
  iniciada_en timestamptz not null default now(),
  terminada_en timestamptz
);
create table if not exists envios (
  id bigserial primary key,
  ejecucion_id uuid references ejecuciones(id) on delete cascade,
  destinatario text not null,
  contact_id uuid references contacts(id),
  canal text not null check (canal in ('email','sms','whatsapp','voz')),
  plantilla_id text references plantillas(id),
  estado text not null default 'enviado' check (estado in ('enviado','entregado','leido','acusado','fallido','baja')),
  intentos int not null default 1,
  proveedor_id text,
  at timestamptz not null default now()
);
create index if not exists envios_ejecucion on envios (ejecucion_id, estado);
create table if not exists bajas (
  vertical_id text not null references verticals(id),
  destinatario text not null,
  canal text not null,
  at timestamptz not null default now(),
  primary key (vertical_id, destinatario, canal)
);

-- Auscultador
create table if not exists entities (
  id uuid primary key default gen_random_uuid(),
  vertical_id text not null references verticals(id),
  cliente_id uuid,                  -- organización cliente de Amarantia (null = del grupo)
  nombre text not null,
  alias text[] not null default '{}',
  risk_keywords text[] not null default '{}',
  umbral_pico real not null default 3,     -- desviaciones
  umbral_tendencia real not null default -0.15,
  activa boolean not null default true
);
create table if not exists baselines (
  entity_id uuid not null references entities(id) on delete cascade,
  day date not null,
  volumen int not null default 0,
  sentimiento_medio real,
  primary key (entity_id, day)
);
create table if not exists alerts (
  id uuid primary key default gen_random_uuid(),
  entity_id uuid not null references entities(id),
  nivel text not null check (nivel in ('vigilar','atencion','crisis')),
  estado text not null default 'nueva' check (estado in ('nueva','vista','confirmada','descartada','en-accion')),
  confirmacion text not null default 'sin-confirmar' check (confirmacion in ('confirmado','sin-confirmar','rumor')),
  motivo text,
  evidencias jsonb not null default '[]'::jsonb,  -- [{senal_id, url, resumen}]
  abierta_en timestamptz not null default now(),
  cerrada_en timestamptz,
  por uuid references profiles(id)
);
alter table if exists senales add column if not exists entity_id uuid references entities(id);
alter table if exists senales add column if not exists confirmacion text check (confirmacion in ('confirmado','sin-confirmar','rumor'));
alter table if exists senales add column if not exists alcance int;

-- PLUS
create table if not exists planes (
  id uuid primary key default gen_random_uuid(),
  vertical_id text not null references verticals(id),
  cliente_id uuid not null,
  escenario text not null,
  propietario text,
  version int not null default 1,
  aprobado_en timestamptz,
  contrato_encargado_url text
);
create table if not exists audiencias (
  id uuid primary key default gen_random_uuid(),
  plan_id uuid not null references planes(id) on delete cascade,
  tipo text not null check (tipo in ('interna','stakeholders','clientes','medios','publico')),
  nombre text not null,
  contactos jsonb not null default '[]'::jsonb,  -- [{nombre, email, tel, canales[]}] o referencia a contacts/cargos
  base_juridica text
);
create table if not exists aprobaciones (
  id bigserial primary key,
  ejecucion_id uuid not null references ejecuciones(id) on delete cascade,
  paso int not null,
  quien uuid references profiles(id),
  decision text not null check (decision in ('aprobado','rechazado')),
  at timestamptz not null default now()
);
