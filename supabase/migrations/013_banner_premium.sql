-- =====================================================================
-- MOTICIAS · 013 · Banner premium (cambio `banner-premium`, decisiones de Rainer del 15 y 16-11-2026)
-- · pub_eventos: medición ampliada de cada caja de publicidad: vistas reales, clics, clics en el botón (CTA), formularios
--   abiertos y enviados, con procedencia, dispositivo y sección. Cuenta por día (sin datos personales).
-- · pub_formularios: lo que envía un lector con «Pide más información», ligado a la campaña; se reenvía al anunciante.
--   Datos personales: solo en esta base privada, nunca en el repositorio. Se conservan 12 meses (lo borra nadie a mano:
--   la purga es un trabajo programado que marca y vacía los campos personales, sin borrar la fila).
-- Misma regla de la 003/004/005: solo el gestor, con su llave; el sitio solo puede sumar por funciones. SE PUEDE APLICAR DOS VECES.
-- =====================================================================

create table if not exists pub_eventos (
  dia          date not null,
  anuncio      text not null check (anuncio ~ '^[a-z0-9:-]{3,90}$'),
  hueco        text not null check (length(hueco) between 2 and 40),
  seccion      text not null default 'portada' check (length(seccion) between 1 and 60),
  dispositivo  text not null default 'escritorio' check (dispositivo in ('movil', 'tableta', 'escritorio')),
  procedencia  text not null default 'directo' check (length(procedencia) between 1 and 80),
  tipo         text not null check (tipo in ('vista', 'clic', 'cta', 'form_abierto', 'form_enviado')),
  n            integer not null default 0 check (n >= 0),
  primary key (dia, anuncio, hueco, seccion, dispositivo, procedencia, tipo)
);
create index if not exists pub_eventos_anuncio on pub_eventos (anuncio, dia desc);

create or replace function pub_evento(p_anuncio text, p_hueco text, p_seccion text, p_dispositivo text, p_procedencia text, p_tipo text) returns void
language sql security invoker set search_path = public as $$
  insert into pub_eventos (dia, anuncio, hueco, seccion, dispositivo, procedencia, tipo, n)
  values ((now() at time zone 'Europe/Madrid')::date, p_anuncio, p_hueco, p_seccion, p_dispositivo, p_procedencia, p_tipo, 1)
  on conflict (dia, anuncio, hueco, seccion, dispositivo, procedencia, tipo) do update set n = pub_eventos.n + 1;
$$;
revoke all on function pub_evento(text, text, text, text, text, text) from public;
grant execute on function pub_evento(text, text, text, text, text, text) to anon;

create table if not exists pub_formularios (
  id              bigint generated always as identity primary key,
  anuncio         text not null check (anuncio ~ '^[a-z0-9:-]{3,90}$'),
  campana         text,
  anunciante      text,
  nombre          text check (nombre is null or length(nombre) <= 120),
  empresa         text check (empresa is null or length(empresa) <= 160),
  email           text check (email is null or length(email) <= 200),
  telefono        text check (telefono is null or length(telefono) <= 40),
  direccion       text check (direccion is null or length(direccion) <= 200),
  cp              text check (cp is null or length(cp) <= 12),
  ciudad          text check (ciudad is null or length(ciudad) <= 100),
  pais            text check (pais is null or length(pais) <= 80),
  consentimiento  boolean not null,
  texto_legal     text not null,                    -- versión del texto que vio (fecha del documento)
  pagina          text,
  dispositivo     text,
  procedencia     text,
  entregado       boolean not null default false,   -- se mandó al anunciante
  entregado_at    timestamptz,
  error_entrega   text,
  purgado_at      timestamptz,                      -- pasados 12 meses se vacían los datos personales (la fila queda)
  creado_at       timestamptz not null default now()
);
create index if not exists pub_formularios_anuncio on pub_formularios (anuncio, creado_at desc);

do $$
declare t text;
begin
  foreach t in array array['pub_eventos', 'pub_formularios'] loop
    execute format('alter table %I enable row level security', t);
    execute format('revoke all on %I from public, anon, authenticated', t);
    execute format('drop policy if exists gestor on %I', t);
    execute format('create policy gestor on %I for all to anon using (privado.gestor_ok()) with check (privado.gestor_ok())', t);
    execute format('grant select, insert on %I to anon', t);
  end loop;
end $$;
grant update on pub_eventos, pub_formularios to anon;
grant usage on all sequences in schema public to anon;

-- Purga a los 12 meses (aplicada el 16-11-2026 con pg_cron): vacía los datos personales del formulario y deja la fila (cifras).
select cron.schedule('formularios-purga-12-meses', '20 3 * * *', $$update public.pub_formularios set nombre = null, empresa = null, email = null, telefono = null, direccion = null, cp = null, ciudad = null, purgado_at = now() where purgado_at is null and creado_at < now() - interval '12 months'$$);
