-- =====================================================================
-- MOTICIAS · 015 · Agenda de eventos (cambio `agenda-de-eventos`, decisiones de Rainer del 15 y 16-11-2026)
-- Los eventos públicos viven en el repositorio (data/eventos/). Aquí, solo lo privado:
-- · agenda_envios: lo que llega por «Subir mi evento» (con la persona responsable y los permisos tal como se marcaron).
-- · agenda_organizadores: qué entidades del CRM organizan qué evento y quién es su responsable.
-- · crm_contactos: correo, teléfono, web o formulario de una cuenta o persona, con su NIVEL (directo · prensa · general
--   · centralita), su URL de fuente y su fecha. Nada deducido: si no hay ninguno, la ficha queda «por localizar».
-- · agenda_comprobaciones: cada visita del comprobador a un enlace de inscripción.
-- · agenda_avisos: cambios de fecha, sede o enlace que detecta el barrido, y enlaces caídos.
-- · agenda_barridos: cuándo corrió el barrido semanal y qué encontró.
-- · crm_actividades.tipo admite `evento_agenda` («Evento en la agenda»).
-- Misma regla de siempre: solo el gestor, con su llave; nadie borra. SE PUEDE APLICAR DOS VECES.
-- =====================================================================

create table if not exists agenda_envios (
  id                    uuid primary key default gen_random_uuid(),
  creado_at             timestamptz not null default now(),
  estado                text not null default 'recibido' check (estado in ('recibido', 'en_revision', 'datos_pedidos', 'convertido', 'descartado', 'spam')),
  evento                jsonb not null,                                    -- campos del evento tal como llegaron
  evento_id             text check (evento_id is null or evento_id ~ '^\d{4}-\d{2}(-\d{2})?-[a-z0-9-]+$'),  -- data/eventos/<id> al convertirlo
  entidad               jsonb not null,                                    -- {nombre, tipo, web}
  nombre                text not null check (length(btrim(nombre)) between 2 and 120),
  cargo                 text check (cargo is null or length(cargo) <= 160),
  correo                text not null check (length(correo) <= 200 and correo ~ '^[^@\s]+@[^@\s]+\.[^@\s]+$'),
  telefono              text check (telefono is null or length(regexp_replace(telefono, '\D', '', 'g')) between 9 and 15),
  permiso_tratamiento_at timestamptz not null,
  permiso_boletin_at    timestamptz,
  permiso_comercial_at  timestamptz,
  permisos_texto        jsonb not null,                                    -- el texto exacto de cada casilla
  huella_origen         text check (huella_origen is null or length(huella_origen) <= 80),  -- sha256 de IP + día (límite por origen)
  cuenta_id             uuid references crm_cuentas(id),
  persona_id            uuid references crm_personas(id),
  historial             jsonb not null default '[]'::jsonb,               -- [{cuando, quien, que}]
  actualizado_at        timestamptz not null default now()
);
create index if not exists agenda_envios_estado on agenda_envios (estado, creado_at desc);
create index if not exists agenda_envios_origen on agenda_envios (huella_origen, creado_at desc);

create table if not exists agenda_organizadores (
  id          bigint generated always as identity primary key,
  evento_id   text not null check (evento_id ~ '^\d{4}-\d{2}(-\d{2})?-[a-z0-9-]+$'),
  cuenta_id   uuid not null references crm_cuentas(id),
  persona_id  uuid references crm_personas(id),                          -- responsable identificado (o null: «por identificar»)
  creado_at   timestamptz not null default now(),
  creado_por  text,
  unique (evento_id, cuenta_id)
);
create index if not exists agenda_organizadores_cuenta on agenda_organizadores (cuenta_id);

create table if not exists crm_contactos (
  id            uuid primary key default gen_random_uuid(),
  cuenta_id     uuid not null references crm_cuentas(id),
  persona_id    uuid references crm_personas(id),
  canal         text not null check (canal in ('correo', 'telefono', 'web', 'formulario')),
  valor         text not null check (length(btrim(valor)) between 3 and 300),
  nivel         text not null check (nivel in ('directo', 'prensa', 'general', 'centralita')),
  fuente_url    text not null check (fuente_url ~ '^https?://'),
  fuente_fecha  date not null,
  notas         text check (notas is null or length(notas) <= 500),
  creado_at     timestamptz not null default now(),
  creado_por    text,
  archivado_at  timestamptz
);
create unique index if not exists crm_contactos_unico on crm_contactos (cuenta_id, canal, lower(valor)) where archivado_at is null;

create table if not exists agenda_comprobaciones (
  id         bigint generated always as identity primary key,
  evento_id  text not null,
  url        text not null,
  ok         boolean not null,
  estado_http smallint,
  destino    text,
  error      text check (error is null or length(error) <= 300),
  ms         integer,
  origen     text not null default 'agente',
  at         timestamptz not null default now()
);
create index if not exists agenda_comprobaciones_evento on agenda_comprobaciones (evento_id, at desc);

create table if not exists agenda_avisos (
  id           bigint generated always as identity primary key,
  evento_id    text,
  tipo         text not null check (tipo in ('enlace_caido', 'cambio_fecha', 'cambio_sede', 'cambio_enlace', 'cancelado', 'aplazado', 'nuevo', 'otro')),
  detalle      text not null check (length(detalle) <= 1000),
  fuente_url   text,
  origen       text not null default 'barrido',
  creado_at    timestamptz not null default now(),
  resuelto_at  timestamptz,
  resuelto_por text
);
create index if not exists agenda_avisos_abiertos on agenda_avisos (creado_at desc) where resuelto_at is null;

create table if not exists agenda_barridos (
  id         bigint generated always as identity primary key,
  at         timestamptz not null default now(),
  origen     text not null default 'barrido',
  ok         boolean not null,
  resumen    text check (resumen is null or length(resumen) <= 2000),
  resultado  jsonb not null default '{}'::jsonb                          -- {nuevos, cambios, revisados, contactos, errores}
);

-- Tipo de actividad nuevo en el historial del CRM
alter table crm_actividades drop constraint if exists crm_actividades_tipo_check;
alter table crm_actividades add constraint crm_actividades_tipo_check check (tipo in ('llamada', 'correo_entrante', 'correo_saliente',
  'reunion', 'linkedin', 'whatsapp', 'nota_de_prensa', 'propuesta', 'contrato', 'factura', 'nota', 'evento_agenda'));

-- ---------- permisos: solo el gestor, con su llave; nadie borra ----------
do $$
declare t text;
begin
  foreach t in array array['agenda_envios', 'agenda_organizadores', 'crm_contactos', 'agenda_comprobaciones', 'agenda_avisos', 'agenda_barridos'] loop
    execute format('alter table %I enable row level security', t);
    execute format('revoke all on %I from public, anon, authenticated', t);
    execute format('drop policy if exists gestor on %I', t);
    execute format('create policy gestor on %I for all to anon using (privado.gestor_ok()) with check (privado.gestor_ok())', t);
    execute format('grant select, insert on %I to anon', t);
  end loop;
end $$;
-- Se corrigen (estado, responsable, archivar un contacto, resolver un aviso); las comprobaciones y los barridos solo crecen.
grant update on agenda_envios, agenda_organizadores, crm_contactos, agenda_avisos to anon;
grant usage on all sequences in schema public to anon;
