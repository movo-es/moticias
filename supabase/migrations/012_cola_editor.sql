-- =====================================================================
-- MOTICIAS · 012 · Cola del editor (cambio `cola-del-editor`, decisiones de Rainer del 15 y 16-11-2026)
-- · cola_temas: temas nuevos para el editor jefe (los que el barrido no metió en la edición, avisos de batidas y
--   sensores, propuestas de los editores). Etiquetas comunes del vertical (`etiquetas-comunes`).
-- · cola_correcciones: cada vez que el editor jefe sube o baja la importancia; el agente aprende de ellas.
-- · encargos_gestor.cola_tema: «Confirmar» crea un encargo para la redacción horaria (/noticias-gestor) enlazado al tema.
-- Misma regla de la 003/004: solo el gestor, con su llave; nadie borra (la papelera es un estado). SE PUEDE APLICAR DOS VECES.
-- =====================================================================

create table if not exists cola_temas (
  id                 bigint generated always as identity primary key,
  titulo             text not null check (length(btrim(titulo)) between 8 and 300),
  resumen            text check (resumen is null or length(resumen) <= 4000),
  avisos             jsonb not null default '[]'::jsonb,      -- [{texto, fuente, url, fecha}] sobre el mismo hecho
  clave_hecho        text check (clave_hecho is null or length(clave_hecho) <= 200),  -- agrupa avisos del mismo hecho
  medio              text check (medio is null or medio in ('tierra', 'mar', 'aire', 'espacio', 'varios')),
  modos              text[] not null default '{}',
  temas              text[] not null default '{}',
  territorios        text[] not null default '{}',
  importancia        smallint check (importancia between 1 and 5),
  importancia_agente smallint check (importancia_agente between 1 and 5),
  fiabilidad         text not null default 'sin_confirmar' check (fiabilidad in ('primaria', 'secundaria', 'sin_confirmar')),
  event_date         date,
  fecha_limite       date,
  no_caduca          boolean not null default false,
  solucion           text check (solucion is null or solucion in ('MOVO', 'MUFMI', 'Movenbus')),
  seccion            text check (seccion is null or length(seccion) <= 40),
  estado             text not null default 'nuevo' check (estado in ('nuevo', 'propuesto', 'confirmado', 'en_redaccion',
                       'para_aprobar', 'publicado', 'sin_fuente', 'archivado', 'papelera')),
  estado_antes       text,                                    -- para «Recuperar» de la papelera o el archivo
  origen             text not null default 'agente' check (origen in ('agente', 'persona')),
  rutina             text check (rutina is null or length(rutina) <= 40),   -- edicion-diaria, batida, sensores, gestor…
  propuesto_por      text,                                    -- nombre de la persona (base privada), o null si es el agente
  perfil             text check (perfil is null or perfil in ('superadmin', 'editor', 'comercial', 'oficina')),
  pieza              text check (pieza is null or pieza ~ '^[a-z0-9-]{3,120}$'),
  motivo             text check (motivo is null or length(motivo) <= 1000),
  historial          jsonb not null default '[]'::jsonb,      -- [{cuando, quien, que}]
  creado_at          timestamptz not null default now(),
  actualizado_at     timestamptz not null default now()
);
create index if not exists cola_temas_estado on cola_temas (estado, creado_at desc);
create index if not exists cola_temas_hecho on cola_temas (clave_hecho) where clave_hecho is not null;

create table if not exists cola_correcciones (
  id           bigint generated always as identity primary key,
  tema         bigint references cola_temas (id),
  titulo       text not null,
  etiquetas    jsonb not null default '{}'::jsonb,           -- medio, modos, temas, territorios en el momento
  de           smallint not null check (de between 1 and 5),
  a            smallint not null check (a between 1 and 5),
  agente       smallint check (agente between 1 and 5),     -- lo que propuso el agente
  motivo       text check (motivo is null or length(motivo) <= 500),
  quien        text not null,
  creado_at    timestamptz not null default now()
);
create index if not exists cola_correcciones_fecha on cola_correcciones (creado_at desc);

alter table encargos_gestor add column if not exists cola_tema bigint references cola_temas (id);

do $$
declare t text;
begin
  foreach t in array array['cola_temas', 'cola_correcciones'] loop
    execute format('alter table %I enable row level security', t);
    execute format('revoke all on %I from public, anon, authenticated', t);
    execute format('drop policy if exists gestor on %I', t);
    execute format('create policy gestor on %I for all to anon using (privado.gestor_ok()) with check (privado.gestor_ok())', t);
    execute format('grant select, insert on %I to anon', t);
  end loop;
end $$;
grant update on cola_temas to anon;
grant usage on all sequences in schema public to anon;
