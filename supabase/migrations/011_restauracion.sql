-- =====================================================================
-- MOTICIAS · 011 · Restauración desde el gestor (cambio OpenSpec restaurar-copia, «sí» de Rainer del 15-11-2026)
--
-- · Esquema `copia` (fuera de la API: PostgREST no lo publica): cada noche, copia.instantanea() guarda una copia de cada
--   tabla de `public` como copia.<tabla>__AAAAMMDD y retira las de más de 14 días (decisión 2). Los datos no salen de
--   Supabase. No se copian gestor_llave, repo_buzon ni copias_registro.
-- · public.copia_fechas(), public.copia_diferencias(tabla, fecha) y public.copia_recuperar(tabla, fecha, clave, campos):
--   las llama el gestor con su llave (privado.gestor_ok()). Comparan una tabla de hoy con la del día elegido y recuperan
--   una fila que falta o los campos elegidos de una fila cambiada. Nunca borran una fila de hoy.
-- · Reglas que se mantienen: «No contactar» no se quita nunca (además del disparador t_no_contactar, aquí se omite
--   cualquier campo no_contactar* que hoy tenga valor); las tablas de solo añadir rechazan los cambios por su disparador.
-- · Qué tablas puede tocar cada perfil lo decide el gestor (verticals → restauracion); aquí, la lista máxima: nunca
--   equipo, gestor_llave, repo_buzon ni copias_registro.
-- · pg_cron: trabajo «copia-interna-diaria» a las 02:40 UTC (03:40 en Madrid en invierno).
-- SE PUEDE APLICAR DOS VECES.
-- =====================================================================
create extension if not exists pg_cron with schema pg_catalog;
create schema if not exists copia;
revoke all on schema copia from public, anon, authenticated;

create or replace function copia.instantanea() returns integer
language plpgsql security definer set search_path = public as $$
declare
  t text;
  f text := to_char((now() at time zone 'Europe/Madrid')::date, 'YYYYMMDD');
  n integer := 0;
  r record;
begin
  for t in select c.relname from pg_class c join pg_namespace s on s.oid = c.relnamespace
           where s.nspname = 'public' and c.relkind = 'r' and c.relname not in ('gestor_llave', 'repo_buzon', 'copias_registro')
  loop
    execute format('drop table if exists copia.%I', t || '__' || f);   -- repetir el mismo día sustituye la copia de ese día
    execute format('create table copia.%I as table public.%I', t || '__' || f, t);
    n := n + 1;
  end loop;
  for r in select tablename from pg_tables where schemaname = 'copia' and tablename ~ '__[0-9]{8}$'
           and to_date(right(tablename, 8), 'YYYYMMDD') < (now() at time zone 'Europe/Madrid')::date - 14
  loop
    execute format('drop table copia.%I', r.tablename);  -- conservación de 14 días (decisión 2 de Rainer)
  end loop;
  return n;
end $$;
revoke all on function copia.instantanea() from public, anon, authenticated;

create or replace function copia._tabla_valida(p_tabla text) returns boolean
language sql stable as $$
  select p_tabla ~ '^[a-z_]+$' and p_tabla not in ('equipo', 'gestor_llave', 'repo_buzon', 'copias_registro')
     and exists (select 1 from pg_tables where schemaname = 'public' and tablename = p_tabla);
$$;

create or replace function copia._clave(p_tabla text) returns text[]
language sql stable as $$
  select array_agg(a.attname::text order by array_position(i.indkey, a.attnum))
  from pg_index i join pg_attribute a on a.attrelid = i.indrelid and a.attnum = any(i.indkey)
  where i.indrelid = ('public.' || quote_ident(p_tabla))::regclass and i.indisprimary;
$$;

create or replace function public.copia_fechas() returns setof date
language sql stable security definer set search_path = public as $$
  select distinct to_date(right(tablename, 8), 'YYYYMMDD') d from pg_tables
  where schemaname = 'copia' and tablename ~ '__[0-9]{8}$' and privado.gestor_ok() order by 1 desc;
$$;

create or replace function public.copia_diferencias(p_tabla text, p_fecha date, p_limite integer default 200) returns jsonb
language plpgsql stable security definer set search_path = public as $$
declare
  snap text := p_tabla || '__' || to_char(p_fecha, 'YYYYMMDD');
  pk text[];
  res jsonb;
begin
  if not privado.gestor_ok() then raise exception 'sin permiso'; end if;
  if not copia._tabla_valida(p_tabla) then raise exception 'tabla no admitida: %', p_tabla; end if;
  if not exists (select 1 from pg_tables where schemaname = 'copia' and tablename = snap) then
    raise exception 'no hay copia de % del %', p_tabla, p_fecha;
  end if;
  pk := copia._clave(p_tabla);
  execute format($q$
    with sk as (select j, (select jsonb_object_agg(k, j -> k) from unnest($1) k) clave from (select to_jsonb(x) j from copia.%I x) s),
         ck as (select j, (select jsonb_object_agg(k, j -> k) from unnest($1) k) clave from (select to_jsonb(y) j from public.%I y) c),
         faltan as (select sk.* from sk where not exists (select 1 from ck where ck.clave = sk.clave)),
         cambiadas as (select sk.clave, (select jsonb_object_agg(k, jsonb_build_object('antes', sk.j -> k, 'ahora', ck.j -> k))
                                         from jsonb_object_keys(sk.j) k where sk.j -> k is distinct from ck.j -> k) campos
                       from sk join ck on ck.clave = sk.clave where sk.j <> ck.j)
    select jsonb_build_object(
      'clave', to_jsonb($1),
      'total_faltan', (select count(*) from faltan), 'total_cambiadas', (select count(*) from cambiadas),
      'faltan', coalesce((select jsonb_agg(jsonb_build_object('clave', clave, 'fila', j)) from (select * from faltan limit $2) f), '[]'::jsonb),
      'cambiadas', coalesce((select jsonb_agg(jsonb_build_object('clave', clave, 'campos', campos)) from (select * from cambiadas limit $2) c), '[]'::jsonb))
  $q$, snap, p_tabla) into res using pk, p_limite;
  return res;
end $$;

create or replace function public.copia_recuperar(p_tabla text, p_fecha date, p_clave jsonb, p_campos text[] default null) returns jsonb
language plpgsql security definer set search_path = public as $$
declare
  snap text := p_tabla || '__' || to_char(p_fecha, 'YYYYMMDD');
  pk text[];
  antes jsonb;
  ahora jsonb;
  donde text;
  sets text[] := '{}';
  omitidos text[] := '{}';
  nombres text[] := '{}';
  k text;
begin
  if not privado.gestor_ok() then raise exception 'sin permiso'; end if;
  if not copia._tabla_valida(p_tabla) then raise exception 'tabla no admitida: %', p_tabla; end if;
  pk := copia._clave(p_tabla);
  select string_agg(format('(x.j ->> %L) is not distinct from (%L::jsonb ->> %L)', c, p_clave::text, c), ' and ') into donde from unnest(pk) c;
  execute format('select x.j from (select to_jsonb(s) j from copia.%I s) x where %s', snap, donde) into antes;
  if antes is null then raise exception 'esa fila no está en la copia del %', p_fecha; end if;
  execute format('select x.j from (select to_jsonb(s) j from public.%I s) x where %s', p_tabla, donde) into ahora;
  if ahora is null then  -- la fila falta hoy: se vuelve a insertar tal como estaba
    execute format('insert into public.%I overriding system value select * from jsonb_populate_record(null::public.%I, $1)', p_tabla, p_tabla) using antes;
    return jsonb_build_object('accion', 'insertada', 'clave', p_clave);
  end if;
  for k in select jsonb_object_keys(antes) loop
    continue when k = any(pk);
    continue when p_campos is not null and not (k = any(p_campos));
    continue when (antes -> k) is not distinct from (ahora -> k);
    if k like 'no_contactar%' and (ahora -> k) is not null and (ahora -> k) <> 'null'::jsonb and (ahora -> k) <> 'false'::jsonb then
      omitidos := omitidos || k;  -- «No contactar» es para siempre: no se quita
      continue;
    end if;
    sets := sets || format('%I = r.%I', k, k);
    nombres := nombres || k;
  end loop;
  if array_length(sets, 1) is null then
    return jsonb_build_object('accion', 'nada', 'omitidos', to_jsonb(omitidos));
  end if;
  execute format('update public.%I t set %s from jsonb_populate_record(null::public.%I, $1) r where %s', p_tabla, array_to_string(sets, ', '), p_tabla,
                 (select string_agg(format('t.%I = r.%I', c, c), ' and ') from unnest(pk) c)) using antes;
  return jsonb_build_object('accion', 'actualizada', 'campos', to_jsonb(nombres), 'omitidos', to_jsonb(omitidos));
end $$;
revoke all on function public.copia_fechas() from public;
revoke all on function public.copia_diferencias(text, date, integer) from public;
revoke all on function public.copia_recuperar(text, date, jsonb, text[]) from public;
grant execute on function public.copia_fechas() to anon;
grant execute on function public.copia_diferencias(text, date, integer) to anon;
grant execute on function public.copia_recuperar(text, date, jsonb, text[]) to anon;

do $$
begin
  perform cron.unschedule('copia-interna-diaria') where exists (select 1 from cron.job where jobname = 'copia-interna-diaria');
  perform cron.schedule('copia-interna-diaria', '40 2 * * *', 'select copia.instantanea()');
end $$;
select copia.instantanea();  -- la primera, ya
