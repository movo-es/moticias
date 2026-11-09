-- =====================================================================
-- MOTICIAS · 007 · SALA DE PRENSA SOBRE LA BASE DE PRENSA (9 nov 2026)
--
-- Cambio `sala-de-prensa-v1` unido a `prensa-y-medios` (decisión de Rainer, 9-11-2026: «lo unes tú sobre su base»).
-- Requiere la 005_prensa_medios y la 006_prensa_cargar (medios, periodistas, prensa_envios, prensa_destinatarios, prensa_coberturas).
--
-- · prensa_notas: el pedido de cada nota de un cliente (o del grupo): texto recibido, cliente (cuenta y persona del CRM),
--   plan, valoración del asesor, verificación del emisor, consentimientos, envío asociado y publicación. El texto
--   publicado vive también en data/notas-de-prensa/<id>.json (público); lo privado, aquí.
-- · prensa_coberturas gana lo que pide el informe de repercusión (docs/prensa/metodo-repercusion.md): nota, tipo de
--   impacto, estado (solo «verificado» entra en el informe), evidencia, contención, revisión humana y el medio por
--   nombre y dominio cuando no está en la base (cuenta_id deja de ser obligatoria).
-- · Mismos permisos que la 003/004/005: solo el gestor con su llave; nadie borra. SE PUEDE APLICAR DOS VECES.
-- =====================================================================

create table if not exists prensa_notas (
  id               text primary key check (id ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9-]{3,80}$'),
  cuenta_id        uuid references crm_cuentas(id),     -- organización emisora (cliente)
  persona_id       uuid references crm_personas(id),    -- quien la envía
  titulo           text not null check (length(btrim(titulo)) between 3 and 300),
  nota             jsonb not null default '{}'::jsonb,  -- {subtitulo, cuerpo, organizacion, web} tal como llegó
  plan             text not null default 'publicacion' check (plan in ('publicacion', 'difusion', 'difusion-plus', 'bono', 'patrocinado', 'publicidad')),
  objetivo         text check (objetivo is null or objetivo in ('noticia', 'lanzamiento', 'marca', 'venta')),
  asesor           jsonb not null default '{}'::jsonb,  -- {puntuacion, veredicto, tipo, ejes, fecha}
  por_que          text[] not null default '{}',        -- las tres líneas «Por qué le llega» (editables)
  verificacion     jsonb not null default '{}'::jsonb,  -- {dominio_corporativo, correo_confirmado, confirmado_at}
  consentimientos  jsonb not null default '{}'::jsonb,  -- {condiciones, comunicaciones_moticias, fecha}
  estado           text not null default 'recibida' check (estado in ('recibida', 'registrada', 'publicada', 'retirada', 'rechazada')),
  motivo           text check (motivo is null or length(motivo) <= 500),
  embargo_hasta    timestamptz,
  envio_id         bigint references prensa_envios(id),
  ghost_url        text check (ghost_url is null or length(ghost_url) <= 400),
  informe          jsonb not null default '{}'::jsonb,  -- {ultimo, enviado_at, dias}
  grupo            boolean not null default false,      -- nota de una empresa del grupo editor
  recibida_at      timestamptz not null default now(),
  publicada_at     timestamptz,
  actualizado      timestamptz not null default now()
);

alter table prensa_coberturas alter column cuenta_id drop not null;
alter table prensa_coberturas add column if not exists nota_id text references prensa_notas(id);
alter table prensa_coberturas add column if not exists tipo_impacto text check (tipo_impacto is null or tipo_impacto in ('reproduccion', 'adaptacion', 'mencion'));
alter table prensa_coberturas add column if not exists estado text not null default 'verificado' check (estado in ('verificado', 'revisar', 'descartado', 'rechazado'));
alter table prensa_coberturas add column if not exists evidencia text[] not null default '{}';
alter table prensa_coberturas add column if not exists contencion numeric(4,3) check (contencion is null or contencion between 0 and 1);
alter table prensa_coberturas add column if not exists medio_texto text check (medio_texto is null or length(medio_texto) <= 200);
alter table prensa_coberturas add column if not exists dominio text check (dominio is null or length(dominio) <= 200);
alter table prensa_coberturas add column if not exists tono text check (tono is null or tono in ('positivo', 'neutro', 'negativo'));
alter table prensa_coberturas add column if not exists revisado_por text;
alter table prensa_coberturas add column if not exists revisado_at timestamptz;
create unique index if not exists prensa_coberturas_nota_url on prensa_coberturas (nota_id, url);  -- los null de nota_id (coberturas de la 005) no chocan entre sí
create index if not exists prensa_notas_estado on prensa_notas (estado, recibida_at desc);

-- ---------- permisos: solo el gestor, con su llave; nadie borra ----------
alter table prensa_notas enable row level security;
revoke all on prensa_notas from public, anon, authenticated;
drop policy if exists gestor on prensa_notas;
create policy gestor on prensa_notas for all to anon using (privado.gestor_ok()) with check (privado.gestor_ok());
grant select, insert, update on prensa_notas to anon;
