-- =====================================================================
-- MOTICIAS · 010 · Copias de seguridad en el Mac (cambio OpenSpec copia-de-seguridad-mac, «sí» de Rainer del 15-11-2026)
--
-- · copias_registro: una fila por copia o por prueba de restauración que hace el Mac. Solo fecha, duración, tamaños,
--   huellas SHA-256 y recuentos de filas: NINGÚN dato. De solo añadir. La lee el gestor (con su llave).
-- · privado.copias_llave: la huella sha256 del token del Mac (el token vive solo en el llavero del Mac). Fuera de la API.
-- · public.copia_anotar(token, datos): la única puerta para escribir en copias_registro; comprueba la huella del token.
--   La llama el gestor (POST /api/gestor?a=copia) con lo que le manda el Mac.
-- · copia_lectura: usuario de Postgres de SOLO LECTURA para el pg_dump del Mac. Se crea sin poder entrar (NOLOGIN) y
--   sin contraseña: la contraseña la genera el instalador en el Mac, la guarda en su llavero y Rainer la activa pegando
--   en el editor SQL la línea que el instalador le deja en el portapapeles. Nunca pasa por el repositorio ni por el chat.
-- SE PUEDE APLICAR DOS VECES.
-- =====================================================================

create table if not exists copias_registro (
  id          bigint generated always as identity primary key,
  clase       text not null check (clase in ('copia', 'prueba')),
  ok          boolean not null,
  inicio      timestamptz not null,
  fin         timestamptz not null default now(),
  equipo      text check (equipo is null or length(equipo) <= 80),            -- nombre del Mac (no de la persona)
  partes      jsonb not null default '{}'::jsonb check (pg_column_size(partes) < 20000),  -- {repo:{bytes,sha256,commit}, base:{bytes,sha256,filas:{tabla:n}}, ghost:{bytes,sha256,miembros}}
  error       text check (error is null or length(error) <= 600),
  creado_at   timestamptz not null default now()
);
create index if not exists copias_registro_fin on copias_registro (clase, fin desc);
alter table copias_registro enable row level security;
drop policy if exists gestor on copias_registro;
create policy gestor on copias_registro for select to anon using (privado.gestor_ok());
drop trigger if exists t_copias_solo_anadir on copias_registro;
create trigger t_copias_solo_anadir before update or delete on copias_registro for each row execute function crm_solo_anadir();

create table if not exists privado.copias_llave (
  huella     text primary key check (huella ~ '^[0-9a-f]{64}$'),
  equipo     text,
  creada_at  timestamptz not null default now()
);
revoke all on privado.copias_llave from public, anon, authenticated;

create or replace function public.copia_anotar(p_token text, p_datos jsonb) returns bigint
language plpgsql security definer set search_path = public, extensions as $$
declare
  nuevo bigint;
begin
  if p_token is null or not exists (select 1 from privado.copias_llave
                                    where huella = encode(extensions.digest(p_token, 'sha256'), 'hex')) then
    raise exception 'token de copia no válido';
  end if;
  insert into copias_registro (clase, ok, inicio, equipo, partes, error)
  values (p_datos ->> 'clase', coalesce((p_datos ->> 'ok')::boolean, false), (p_datos ->> 'inicio')::timestamptz,
          left(p_datos ->> 'equipo', 80), coalesce(p_datos -> 'partes', '{}'::jsonb), left(p_datos ->> 'error', 600))
  returning id into nuevo;
  return nuevo;
end $$;
revoke all on function public.copia_anotar(text, jsonb) from public;
grant execute on function public.copia_anotar(text, jsonb) to anon;

-- Usuario de solo lectura para el pg_dump del Mac (sin login hasta que Rainer pegue su contraseña desde el Mac).
do $$
begin
  if not exists (select 1 from pg_roles where rolname = 'copia_lectura') then
    create role copia_lectura nologin bypassrls;
  end if;
end $$;
grant usage on schema public to copia_lectura;
grant select on all tables in schema public to copia_lectura;
grant select on all sequences in schema public to copia_lectura;
alter default privileges in schema public grant select on tables to copia_lectura;
alter default privileges in schema public grant select on sequences to copia_lectura;
