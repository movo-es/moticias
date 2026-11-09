-- =====================================================================
-- MOTICIAS · 005 · SEGUIMIENTO DE LA PUBLICIDAD, COMPROBADOR Y NOTICIAS DESDE EL GESTOR (9 nov 2026)
--
-- Rainer, 9-11-2026 (tarde): «Debe haber un panel de seguimiento de cada una de las publicidades y patrocinios: fecha
-- publicación y retirada, en qué contextos insertados, en qué posiciones, número de visualizaciones y número de clics.
-- Debe haber un agente comprobador que en horarios diurnos al azar haga clic en cada uno de los enlaces promocionados […]
-- con constatación en el panel.» Y: «El panel del editor y editor jefe debe tener posibilidad de pegar un texto o un enlace
-- […] investiga y crea noticia con publicación inmediata».
--
-- · pub_diario: una fila por día, caja, hueco y página, con impresiones y clics (lectores reales; los robots y el
--   comprobador no cuentan). Lo suma pub_contar(), que corre con los permisos de quien llama (el gestor, con su llave).
-- · pub_comprobaciones: cada visita del comprobador a un enlace promocionado, con su resultado. De solo añadir.
-- · encargos_gestor: lo que el editor o el editor jefe pegan en el gestor para que la redacción lo investigue y publique.
--   Aquí y no en el repositorio porque puede llevar texto que no es público.
-- Todo con la misma regla de la 003/004: solo el gestor, con su llave; nadie borra. SE PUEDE APLICAR DOS VECES.
-- =====================================================================

create table if not exists pub_diario (
  dia          date not null,
  anuncio      text not null check (anuncio ~ '^[a-z0-9:-]{3,90}$'),
  hueco        text not null check (length(hueco) between 2 and 40),
  pagina       text not null check (length(pagina) between 1 and 200),
  impresiones  integer not null default 0 check (impresiones >= 0),
  clics        integer not null default 0 check (clics >= 0),
  primary key (dia, anuncio, hueco, pagina)
);
create index if not exists pub_diario_anuncio on pub_diario (anuncio, dia desc);

create or replace function pub_contar(p_anuncio text, p_hueco text, p_pagina text, p_tipo text) returns void
language sql security invoker set search_path = public as $$
  insert into pub_diario (dia, anuncio, hueco, pagina, impresiones, clics)
  values ((now() at time zone 'Europe/Madrid')::date, p_anuncio, p_hueco, p_pagina,
          case when p_tipo = 'i' then 1 else 0 end, case when p_tipo = 'c' then 1 else 0 end)
  on conflict (dia, anuncio, hueco, pagina) do update
    set impresiones = pub_diario.impresiones + excluded.impresiones, clics = pub_diario.clics + excluded.clics;
$$;
revoke all on function pub_contar(text, text, text, text) from public;
grant execute on function pub_contar(text, text, text, text) to anon;

create table if not exists pub_comprobaciones (
  id         bigint generated always as identity primary key,
  anuncio    text not null check (anuncio ~ '^[a-z0-9:-]{3,90}$'),
  url        text not null check (length(url) <= 600),
  estado     integer,
  url_final  text check (url_final is null or length(url_final) <= 600),
  ms         integer,
  ok         boolean not null,
  error      text check (error is null or length(error) <= 300),
  origen     text not null default 'agente' check (origen in ('agente', 'manual')),
  at         timestamptz not null default now()
);
create index if not exists pub_comprobaciones_anuncio on pub_comprobaciones (anuncio, at desc);
drop trigger if exists t_comprobaciones_solo_anadir on pub_comprobaciones;
create trigger t_comprobaciones_solo_anadir before update or delete on pub_comprobaciones for each row execute function crm_solo_anadir();

create table if not exists encargos_gestor (
  id           bigint generated always as identity primary key,
  texto        text not null check (length(btrim(texto)) between 10 and 20000),
  enlace       text check (enlace is null or (enlace ~ '^https?://' and length(enlace) <= 600)),
  dominio      text check (dominio is null or dominio ~ '^[a-z0-9.-]+\.[a-z]{2,}$'),
  clase_fuente text check (clase_fuente is null or clase_fuente in ('notas_de_prensa', 'informacion', 'no_confianza')),
  pedido_por   text not null,
  perfil       text not null check (perfil in ('superadmin', 'editor', 'comercial', 'oficina')),
  publicacion  text not null check (publicacion in ('inmediata', 'revision')),
  estado       text not null default 'pendiente' check (estado in ('pendiente', 'en_curso', 'publicada', 'pendiente_aprobacion', 'sin_fuentes', 'descartado')),
  pieza        text check (pieza is null or pieza ~ '^[a-z0-9-]{3,120}$'),
  resultado    text check (resultado is null or length(resultado) <= 2000),
  creado_at    timestamptz not null default now(),
  cerrado_at   timestamptz
);
create index if not exists encargos_gestor_pendientes on encargos_gestor (creado_at) where estado in ('pendiente', 'en_curso');

do $$
declare t text;
begin
  foreach t in array array['pub_diario', 'pub_comprobaciones', 'encargos_gestor'] loop
    execute format('alter table %I enable row level security', t);
    execute format('revoke all on %I from public, anon, authenticated', t);
    execute format('drop policy if exists gestor on %I', t);
    execute format('create policy gestor on %I for all to anon using (privado.gestor_ok()) with check (privado.gestor_ok())', t);
    execute format('grant select, insert on %I to anon', t);
  end loop;
end $$;
grant update on pub_diario, encargos_gestor to anon;
grant usage on all sequences in schema public to anon;
