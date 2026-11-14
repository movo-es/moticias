-- =====================================================================
-- MOTICIAS · 008 · Buzón del repositorio (14-11-2026)
-- Las tareas programadas de Claude no siempre pueden hacer `push` a movo-es/moticias (desde el 12-11-2026 sus sesiones
-- arrancan sin el repositorio autorizado). En vez de dejar parches que alguien aplica a mano, dejan aquí los ficheros
-- que cambian, con el conector de Supabase; el cron `aplicar_buzon` del gestor (Vercel, con su GITHUB_TOKEN) los sube
-- a `main` en un solo commit por lote, y `ghost_al_dia` los publica en moticias.com.
-- · Un lote puede llegar en varias partes (`parte` de `partes`): no se aplica hasta que están todas.
-- · Cada fichero lleva `base`, el blob que la tarea vio en `main` (null si es nuevo). Si `main` ha cambiado ese fichero
--   desde entonces, el lote queda en `error` y no se pisa nada.
-- · Solo contenido: data/, docs/ediciones.md, docs/fuentes.md, docs/asesor/ y portal/img/. El código no entra por aquí.
-- · Nadie borra: sin `grant delete`; los lotes cambian de estado (pendiente → aplicado | error).
-- SE PUEDE APLICAR DOS VECES.
-- =====================================================================

create table if not exists repo_buzon (
  id           uuid primary key default gen_random_uuid(),
  creado_at    timestamptz not null default now(),
  lote         text not null check (lote ~ '^[0-9]{8}-[0-9]{4}-[a-z0-9-]{2,60}$'),
  parte        int  not null default 1 check (parte >= 1),
  partes       int  not null default 1 check (partes >= 1 and partes <= 50),
  origen       text not null,
  mensaje      text not null,
  autor        text not null default 'G. Jordan',
  autor_correo text not null default 'redaccion@moticias.com',
  ficheros     jsonb not null check (jsonb_typeof(ficheros) = 'array'),
  estado       text not null default 'pendiente' check (estado in ('pendiente', 'aplicado', 'error')),
  aplicado_at  timestamptz,
  sha          text,
  error        text,
  unique (lote, parte)
);
create index if not exists repo_buzon_pendientes on repo_buzon (estado, creado_at);

alter table repo_buzon enable row level security;
revoke all on repo_buzon from public, anon, authenticated;
drop policy if exists gestor on repo_buzon;
create policy gestor on repo_buzon for all to anon using (privado.gestor_ok()) with check (privado.gestor_ok());  -- 004: la función vive en `privado`
grant select, insert, update on repo_buzon to anon;
