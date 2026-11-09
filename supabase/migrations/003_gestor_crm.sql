-- =====================================================================
-- MOTICIAS · 003 · GESTOR: EQUIPO, CRM Y REGISTRO (9 nov 2026)
--
-- Rainer, 9-11-2026: «Construye gestión de staff integrada con gestión de contenidos y patrocinios/publicidad. Ahí debe
-- existir un CRM (aprovecha lo hecho en movo) para gestionar suscriptores en sus diferentes categorías, clientes de
-- patrocinio y publicidad, fuentes de información, contactos en los medios relevantes…»
--
-- · Proyecto Supabase propio «moticias» (Frankfurt). El repositorio es público: aquí, y solo aquí, viven los nombres,
--   correos y teléfonos del equipo y del CRM.
-- · El CRM copia el módulo de MOVO (movo-es/movo, migraciones 433–437): tablas `crm_*` con su columna `producto`,
--   el estado como LIBRO DE SOLO AÑADIR (el de hoy es la última fila), las actividades de solo añadir, el siguiente paso
--   con fecha y «No contactar» para siempre. Lo que es de MOTICIAS (tipos de cuenta, estados de cada tipo, categorías de
--   suscriptor) vive en `verticals/movilidad.json → crm`, no aquí.
-- · Los suscriptores son los miembros de Ghost: no se copian. La ficha de una persona puede llevar su `ghost_member_id`.
-- · Quién entra: SOLO el gestor (api/gestor.py en Vercel). Cada petición lleva la cabecera `x-moticias-clave`; la base
--   guarda solo la huella (`gestor_llave`) y todas las políticas preguntan `gestor_ok()`. Sin la cabecera, la clave
--   pública (anon) no lee ni escribe nada. Nadie borra: no hay `grant delete` en ninguna tabla.
-- SE PUEDE APLICAR DOS VECES.
-- =====================================================================

create extension if not exists pgcrypto;

-- ---------- la llave del gestor ----------
create table if not exists gestor_llave (
  id      smallint primary key default 1 check (id = 1),
  huella  text not null check (huella ~ '^[0-9a-f]{64}$'),
  at      timestamptz not null default now()
);
alter table gestor_llave enable row level security;
revoke all on gestor_llave from public, anon, authenticated;
-- permisos: ninguno, solo por funciones gestor_llave

create or replace function gestor_ok() returns boolean
language sql stable security definer set search_path = public, extensions as $$
  select exists (
    select 1 from gestor_llave
    where huella = encode(extensions.digest(coalesce(
      nullif(current_setting('request.headers', true), '')::json ->> 'x-moticias-clave', ''), 'sha256'), 'hex')
  );
$$;
revoke all on function gestor_ok() from public;
grant execute on function gestor_ok() to anon, authenticated;

-- ---------- equipo del gestor ----------
create table if not exists equipo (
  id          text primary key check (id ~ '^[0-9a-f]{6,24}$'),
  email       text not null check (email = lower(btrim(email)) and email ~ '^[^@\s]+@[^@\s]+\.[^@\s]+$'),
  datos       jsonb not null,
  actualizado timestamptz not null default now()
);
create unique index if not exists equipo_email on equipo (email);

-- ---------- CRM (módulo de MOVO) ----------
create table if not exists crm_cuentas (
  id            uuid primary key default gen_random_uuid(),
  producto      text not null default 'moticias' check (producto ~ '^[a-z][a-z0-9_]{1,30}$'),
  tipo          text not null check (tipo in ('suscriptor', 'anunciante', 'patrocinador', 'fuente', 'medio', 'institucion', 'empresa', 'otro')),
  subtipo       text check (subtipo is null or length(subtipo) <= 60),
  nombre        text not null check (length(btrim(nombre)) between 2 and 200),
  razon_social  text check (razon_social is null or length(razon_social) <= 200),
  cif           text check (cif is null or cif ~ '^[A-Z0-9]{8,12}$'),
  sector        text check (sector is null or length(sector) <= 200),
  comunidad     text check (comunidad is null or length(comunidad) <= 80),
  provincia     text check (provincia is null or length(provincia) <= 80),
  municipio     text check (municipio is null or length(municipio) <= 120),
  web           text check (web is null or length(web) <= 300),
  dominio       text check (dominio is null or dominio ~ '^[a-z0-9.-]+\.[a-z]{2,}$'),
  origen        text not null default 'manual' check (length(origen) between 2 and 40),
  senal         text check (senal is null or length(senal) <= 500),
  responsable   text,
  etiquetas     text[] not null default '{}',
  notas         text check (notas is null or length(notas) <= 4000),
  datos         jsonb not null default '{}'::jsonb,
  creada_at     timestamptz not null default now(),
  creada_por    text,
  archivada_at  timestamptz
);
create index if not exists crm_cuentas_tipo on crm_cuentas (producto, tipo) where archivada_at is null;
create unique index if not exists crm_cuentas_dominio on crm_cuentas (producto, tipo, dominio) where dominio is not null and archivada_at is null;

create table if not exists crm_personas (
  id                   uuid primary key default gen_random_uuid(),
  cuenta_id            uuid references crm_cuentas(id),
  nombre               text check (nombre is null or length(btrim(nombre)) between 2 and 120),
  cargo                text check (cargo is null or length(cargo) <= 160),
  perfil               text not null default 'otro' check (length(perfil) <= 40),
  correo               text check (correo is null or (length(correo) <= 200 and correo ~ '^[^@\s]+@[^@\s]+\.[^@\s]+$')),
  telefono             text check (telefono is null or length(regexp_replace(telefono, '\D', '', 'g')) between 9 and 15),
  linkedin             text check (linkedin is null or length(linkedin) <= 300),
  ghost_member_id      text check (ghost_member_id is null or ghost_member_id ~ '^[0-9a-f]{24}$'),
  verificado           boolean not null default false,
  permiso_correo_at    timestamptz,
  permiso_correo_como  text check (permiso_correo_como is null or length(permiso_correo_como) <= 200),
  no_contactar_at      timestamptz,
  no_contactar_motivo  text check (no_contactar_motivo is null or length(no_contactar_motivo) <= 300),
  notas                text check (notas is null or length(notas) <= 2000),
  creada_at            timestamptz not null default now(),
  creada_por           text,
  archivada_at         timestamptz,
  check (nombre is not null or correo is not null or telefono is not null),
  check (permiso_correo_at is null or permiso_correo_como is not null)
);
create index if not exists crm_personas_cuenta on crm_personas (cuenta_id);
create index if not exists crm_personas_correo on crm_personas (lower(correo)) where correo is not null;
create unique index if not exists crm_personas_ghost on crm_personas (ghost_member_id) where ghost_member_id is not null;

-- «No contactar» es para siempre (como en MOVO): una vez puesto no se quita.
create or replace function crm_no_contactar_para_siempre() returns trigger language plpgsql as $$
begin
  if old.no_contactar_at is not null and new.no_contactar_at is null then
    raise exception 'No contactar es para siempre';
  end if;
  return new;
end $$;
drop trigger if exists t_no_contactar on crm_personas;
create trigger t_no_contactar before update on crm_personas for each row execute function crm_no_contactar_para_siempre();

-- El estado es un libro de solo añadir: el de hoy es la última fila de cada cuenta.
create table if not exists crm_estados (
  id           bigint generated always as identity primary key,
  cuenta_id    uuid not null references crm_cuentas(id),
  estado       text not null check (length(estado) between 2 and 40),
  motivo       text check (motivo is null or length(motivo) <= 300),
  nutrir_hasta date,
  quien        text,
  at           timestamptz not null default now()
);
create index if not exists crm_estados_cuenta on crm_estados (cuenta_id, id desc);

create table if not exists crm_actividades (
  id         bigint generated always as identity primary key,
  cuenta_id  uuid not null references crm_cuentas(id),
  persona_id uuid references crm_personas(id),
  tipo       text not null check (tipo in ('llamada', 'correo_entrante', 'correo_saliente', 'reunion', 'linkedin', 'whatsapp',
                                           'nota_de_prensa', 'propuesta', 'contrato', 'factura', 'nota')),
  notas      text check (notas is null or length(notas) <= 2000),
  quien      text,
  at         timestamptz not null default now()
);
create index if not exists crm_actividades_cuenta on crm_actividades (cuenta_id, at desc);

create or replace function crm_solo_anadir() returns trigger language plpgsql as $$
begin
  raise exception '% es de solo añadir', tg_table_name;
end $$;
drop trigger if exists t_estados_solo_anadir on crm_estados;
create trigger t_estados_solo_anadir before update or delete on crm_estados for each row execute function crm_solo_anadir();
drop trigger if exists t_actividades_solo_anadir on crm_actividades;
create trigger t_actividades_solo_anadir before update or delete on crm_actividades for each row execute function crm_solo_anadir();

create table if not exists crm_pasos (
  id          bigint generated always as identity primary key,
  cuenta_id   uuid not null references crm_cuentas(id),
  persona_id  uuid references crm_personas(id),
  que         text not null check (length(btrim(que)) between 2 and 200),
  fecha       date not null,
  responsable text,
  creado_por  text,
  creado_at   timestamptz not null default now(),
  hecho_at    timestamptz,
  hecho_por   text
);
create index if not exists crm_pasos_abiertos on crm_pasos (fecha) where hecho_at is null;
create index if not exists crm_pasos_cuenta on crm_pasos (cuenta_id);

-- Lo vendido a un anunciante o patrocinador. La creatividad pública vive en el repositorio (data/ads/<anuncio_id>.json);
-- el importe, el contacto y la factura, aquí.
create table if not exists crm_contratos (
  id            bigint generated always as identity primary key,
  cuenta_id     uuid not null references crm_cuentas(id),
  anuncio_id    text check (anuncio_id is null or anuncio_id ~ '^[a-z0-9-]{3,80}$'),
  concepto      text not null check (length(btrim(concepto)) between 2 and 200),
  nivel         text check (nivel is null or nivel in ('premium', 'estandar', 'basico', 'texto')),
  importe_cent  bigint check (importe_cent is null or importe_cent >= 0),
  desde         date,
  hasta         date,
  estado        text not null default 'propuesta' check (estado in ('propuesta', 'firmado', 'facturado', 'cobrado', 'anulado')),
  notas         text check (notas is null or length(notas) <= 2000),
  creado_por    text,
  creado_at     timestamptz not null default now(),
  check (hasta is null or desde is null or hasta >= desde)
);
create index if not exists crm_contratos_cuenta on crm_contratos (cuenta_id);

-- Registro del gestor: quién hizo qué (edición de piezas, IA, retiradas, publicidad, equipo). De solo añadir.
create table if not exists gestor_registro (
  id      bigint generated always as identity primary key,
  quien   text not null,
  accion  text not null check (length(accion) <= 60),
  objeto  text check (objeto is null or length(objeto) <= 200),
  detalle jsonb not null default '{}'::jsonb,
  at      timestamptz not null default now()
);
drop trigger if exists t_registro_solo_anadir on gestor_registro;
create trigger t_registro_solo_anadir before update or delete on gestor_registro for each row execute function crm_solo_anadir();

-- Vista de trabajo: cada cuenta con su estado de hoy, su siguiente paso y cuántas personas tiene.
create or replace view crm_cuentas_hoy with (security_invoker = true) as
select c.*,
       (select e.estado from crm_estados e where e.cuenta_id = c.id order by e.id desc limit 1) as estado,
       (select e.at from crm_estados e where e.cuenta_id = c.id order by e.id desc limit 1) as estado_at,
       (select p.que from crm_pasos p where p.cuenta_id = c.id and p.hecho_at is null order by p.fecha, p.id limit 1) as paso_que,
       (select p.fecha from crm_pasos p where p.cuenta_id = c.id and p.hecho_at is null order by p.fecha, p.id limit 1) as paso_fecha,
       (select count(*) from crm_personas x where x.cuenta_id = c.id and x.archivada_at is null) as personas,
       (select max(a.at) from crm_actividades a where a.cuenta_id = c.id) as ultima_actividad
from crm_cuentas c;

-- ---------- permisos: solo el gestor, con su llave; nadie borra ----------
do $$
declare t text;
begin
  foreach t in array array['equipo', 'crm_cuentas', 'crm_personas', 'crm_estados', 'crm_actividades', 'crm_pasos',
                           'crm_contratos', 'gestor_registro'] loop
    execute format('alter table %I enable row level security', t);
    execute format('revoke all on %I from public, anon, authenticated', t);
    execute format('drop policy if exists gestor on %I', t);
    execute format('create policy gestor on %I for all to anon using (gestor_ok()) with check (gestor_ok())', t);
    execute format('grant select, insert on %I to anon', t);
  end loop;
end $$;
-- Se corrigen: el equipo, las cuentas, las personas, los pasos y los contratos. Los libros (estados, actividades,
-- registro) solo crecen.
grant update on equipo, crm_cuentas, crm_personas, crm_pasos, crm_contratos to anon;
grant usage on all sequences in schema public to anon;
revoke all on crm_cuentas_hoy from public, anon, authenticated;
grant select on crm_cuentas_hoy to anon;
