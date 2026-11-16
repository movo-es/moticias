-- =====================================================================
-- MOTICIAS · 014 · Panel SEO y asistentes de IA (cambio `panel-seo-llm`, 16-11-2026)
-- · seo_llm: cada respuesta de la batería fija de preguntas del sector a cada asistente, con lo que cita y qué marcas nombra
--   (y si las asocia con lo suyo: MOVO con PMST y consultoría, Movenbus con el autobús, MUFMI con el transporte a la demanda).
-- · seo_cambios: cada cambio de «Hazlo con IA» (título, descripción, relacionadas, marcado o texto), con el valor de antes
--   para deshacerlo. Nadie borra: deshacer es otro estado.
-- SE PUEDE APLICAR DOS VECES.
-- =====================================================================
create table if not exists seo_llm (
  id            bigint generated always as identity primary key,
  ronda         text not null,                 -- AAAA-MM-DD de la batería
  modelo        text not null,
  pregunta_n    smallint not null,
  pregunta      text not null,
  respuesta     text,
  citas         jsonb not null default '[]'::jsonb,
  cita_moticias boolean not null default false,
  marcas        jsonb not null default '{}'::jsonb,
  error         text,
  creado_at     timestamptz not null default now()
);
create index if not exists seo_llm_ronda on seo_llm (ronda desc, modelo);

create table if not exists seo_cambios (
  id          bigint generated always as identity primary key,
  pieza       text not null check (pieza ~ '^[a-z0-9-]{3,120}$'),
  tipo        text not null check (tipo in ('seo_title', 'seo_description', 'relacionadas', 'marcado', 'texto')),
  antes       jsonb,
  despues     jsonb,
  estado      text not null default 'aplicado' check (estado in ('propuesta', 'aplicado', 'deshecho', 'descartado')),
  quien       text not null,
  nota        text,
  creado_at   timestamptz not null default now(),
  cambiado_at timestamptz
);
create index if not exists seo_cambios_pieza on seo_cambios (pieza, creado_at desc);

do $$
declare t text;
begin
  foreach t in array array['seo_llm', 'seo_cambios'] loop
    execute format('alter table %I enable row level security', t);
    execute format('revoke all on %I from public, anon, authenticated', t);
    execute format('drop policy if exists gestor on %I', t);
    execute format('create policy gestor on %I for all to anon using (privado.gestor_ok()) with check (privado.gestor_ok())', t);
    execute format('grant select, insert on %I to anon', t);
  end loop;
end $$;
grant update on seo_cambios to anon;
grant usage on all sequences in schema public to anon;
