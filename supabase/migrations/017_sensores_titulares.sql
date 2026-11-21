-- 017 · Titulares de los medios monitorizados, recogidos por el servidor sin IA (decisión de Rainer, 21-11-2026).
-- El cron `sensores` de Vercel los guarda cada hora, de 06:00 a 23:00 (Madrid); la edición diaria los lee en vez de abrir
-- cada medio. Solo titular, enlace, fecha y entradilla públicos; nada de texto de los artículos. Se puede aplicar dos veces.
create table if not exists sensores_titulares (
  id            bigint generated always as identity primary key,
  medio         text not null check (length(medio) <= 60),
  titulo        text not null check (length(titulo) between 8 and 400),
  url           text not null unique check (length(url) <= 600),
  publicado_at  timestamptz,                                   -- la que da el medio; null si no la da (nunca deducida)
  entradilla    text check (entradilla is null or length(entradilla) <= 400),
  grande        boolean not null default false,                -- casa con una regla de «gran noticia» del vertical
  avisado       boolean not null default false,                -- ya fue a la cola del editor
  visto_at      timestamptz not null default now()             -- cuándo lo vio el servidor por primera vez
);
create index if not exists sensores_titulares_visto on sensores_titulares (visto_at desc);
create index if not exists sensores_titulares_medio on sensores_titulares (medio, visto_at desc);
create table if not exists sensores_medios (
  medio        text primary key check (length(medio) <= 60),
  ultimo_ok    timestamptz,
  ultimo_n     integer,
  ultimo_error text check (ultimo_error is null or length(ultimo_error) <= 400),
  error_at     timestamptz,
  pasada_at    timestamptz not null default now()
);
alter table sensores_titulares enable row level security;
alter table sensores_medios enable row level security;
drop policy if exists gestor on sensores_titulares;
create policy gestor on sensores_titulares for all to anon using (privado.gestor_ok()) with check (privado.gestor_ok());
drop policy if exists gestor on sensores_medios;
create policy gestor on sensores_medios for all to anon using (privado.gestor_ok()) with check (privado.gestor_ok());
