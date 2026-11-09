-- MOTICIAS · migración 003 · sala-de-prensa-v1 (BORRADOR del 9-11-2026; NO APLICADA)
-- Qué: base de contactos de difusión, pedidos, planes de difusión, envíos e impactos de la sala de prensa.
-- Por qué: hasta que exista el proyecto Supabase `moticias` (semana 48), estos datos viven en el repositorio privado
-- movo-es/moticias-equipo (prensa/). Esta migración los recibe cuando se active. RLS: solo service_role; el gestor
-- accede por funciones cerradas. SE PUEDE APLICAR DOS VECES (todo es IF NOT EXISTS).

create table if not exists prensa_contactos (
  id text primary key,                      -- c-<hash>, el mismo que en contactos.json
  email text unique,
  nombre text, cargo text, organizacion text, medio_id text, linkedin text,
  tipo text not null check (tipo in ('redaccion','periodista','newsletter','decisor-b2b','profesional','particular')),
  base text not null check (base in ('interes-legitimo-prensa','consentimiento','contrato')),
  consentimiento jsonb,                     -- {fecha, texto, origen}
  estado text not null default 'activo' check (estado in ('activo','pendiente-opt-in','pausado','baja','rebotado')),
  intereses jsonb not null default '{}'::jsonb,   -- {submodos[], territorios[], temas[], inferidos, origen}
  bajas_sector text[] not null default '{}',
  origen text, informado_art14 boolean not null default false,
  sin_abrir_seguidos int not null default 0,
  creado timestamptz not null default now(), baja_en timestamptz
);
create table if not exists prensa_pedidos (
  nota_id text primary key,                 -- id de data/notas-de-prensa/
  cliente jsonb not null,                   -- {nombre, cargo, email, telefono, organizacion, web}
  plan text not null, objetivo text,
  asesor jsonb, por_que text[], difusion jsonb, metricas jsonb,
  creado timestamptz not null default now(), actualizado timestamptz
);
create table if not exists prensa_envios (
  id bigserial primary key,
  nota_id text not null references prensa_pedidos(nota_id),
  contacto_id text not null references prensa_contactos(id),
  ok boolean not null, detalle text, enviado_en timestamptz not null default now()
);
create table if not exists prensa_impactos (
  id text primary key,                      -- i-<hash de la URL canónica>
  nota_id text not null,
  url text not null, canonica text not null, medio_id text, medio text, dominio text,
  titulo text, fecha date, tipo text check (tipo in ('reproduccion','adaptacion','mencion','descartado')),
  estado text check (estado in ('verificado','revisar','descartado','rechazado')),
  contencion numeric, evidencia text[], tono text, metodo text,
  revisado_por text, revisado_en timestamptz, detectado_en timestamptz not null default now()
);
alter table prensa_contactos enable row level security;
alter table prensa_pedidos enable row level security;
alter table prensa_envios enable row level security;
alter table prensa_impactos enable row level security;
revoke all on prensa_contactos, prensa_pedidos, prensa_envios, prensa_impactos from anon, authenticated;
