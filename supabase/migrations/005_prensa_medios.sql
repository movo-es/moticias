-- =====================================================================
-- MOTICIAS · 005 · PRENSA: MEDIOS, PERIODISTAS, ENVÍOS Y COBERTURAS (9 nov 2026)
--
-- Rainer, 9-11-2026: «Lo importante es tener una base de datos de destinatarios muy buena, que reacciona y actualizada»
-- para el Broadcast de novedades (notas de prensa), noticias (contenido editorial con noticia real) y comunicados
-- (p. ej. de asociaciones), para clientes o para nosotros; invitaciones a suscribirse y mensajes del editor o de la
-- redacción; actualización cada miércoles a las 15:30. Cambio OpenSpec `prensa-y-medios`.
--
-- · Se apoya en el CRM de la 003: un medio es una `crm_cuentas` de tipo `medio`; un periodista es una `crm_personas`
--   de esa cuenta. Aquí van solo las fichas ampliadas (1:1), los envíos, sus destinatarios y las coberturas.
-- · Colaboración, importancia y probabilidad de publicación: las calcula `prensa_recalcular()` salvo que alguien las
--   haya fijado a mano (`*_manual = true`). La colaboración empieza VACÍA y solo toma valor tras el primer contacto
--   saliente o entrante (decisión de Rainer).
-- · Solo datos profesionales publicados por el propio medio o por el periodista (art. 19 LOPDGDD); cada dato lleva su
--   fuente en `fuentes`. «No contactar» (crm_personas) manda sobre todo.
-- · Mismos permisos que la 003/004: solo el gestor con su llave; nadie borra. SE PUEDE APLICAR DOS VECES.
-- =====================================================================

-- ---------- ficha de medio ----------
create table if not exists medios (
  cuenta_id            uuid primary key references crm_cuentas(id),
  tipo_medio           text not null default 'otro' check (tipo_medio in (
                         'generalista', 'economico', 'b2b_sector', 'b2b_otro_sector', 'b2g', 'agencia', 'newsletter',
                         'boletin_asociacion', 'radio_tv', 'regional', 'turismo', 'tecnologia', 'institucional', 'otro')),
  formatos             text[] not null default '{}',      -- digital, impreso, newsletter, radio, tv, podcast, agencia
  alcance              text check (alcance is null or alcance in ('internacional', 'nacional', 'autonomico', 'provincial', 'local')),
  ambitos              text[] not null default '{}',      -- movilidad, viajeros, autobus, ferrocarril, aereo, maritimo, logistica, turismo, economia, administracion, sostenibilidad, tecnologia, infraestructuras
  periodicidad         text check (periodicidad is null or length(periodicidad) <= 60),
  grupo                text check (grupo is null or length(grupo) <= 120),  -- grupo editorial o editora
  correo_redaccion     text check (correo_redaccion is null or correo_redaccion ~ '^[^@\s]+@[^@\s]+\.[^@\s]+$'),
  correo_notas         text check (correo_notas is null or correo_notas ~ '^[^@\s]+@[^@\s]+\.[^@\s]+$'),
  telefono_corporativo text check (telefono_corporativo is null or length(regexp_replace(telefono_corporativo, '\D', '', 'g')) between 9 and 15),
  direccion            text check (direccion is null or length(direccion) <= 200),
  cp                   text check (cp is null or cp ~ '^[0-9A-Z -]{4,10}$'),
  ciudad               text check (ciudad is null or length(ciudad) <= 120),
  region               text check (region is null or length(region) <= 120),   -- comunidad autónoma, estado o provincia
  pais                 text not null default 'España',
  redes                jsonb not null default '[]'::jsonb,  -- [{red, url, usuario, seguidores, ultimo, at}]
  audiencia            jsonb not null default '{}'::jsonb,  -- {usuarios_mes, suscriptores_newsletter, tirada, fuente, at}
  referencias          text check (referencias is null or length(referencias) <= 1500),  -- calidad y cantidad: OJD/PGD, premios, quién lo cita
  comentario_ia        text check (comentario_ia is null or length(comentario_ia) <= 1500),
  importancia          smallint check (importancia between 1 and 5),
  importancia_manual   boolean not null default false,
  colaboracion         text check (colaboracion is null or colaboracion in ('colaborador', 'neutral', 'poco_colaborador')),
  colaboracion_manual  boolean not null default false,
  prob_previa          numeric(3,2) check (prob_previa between 0 and 1),      -- estimación inicial (encaje temático)
  prob_publicacion     numeric(3,2) check (prob_publicacion between 0 and 1), -- previa ajustada con el historial
  prob_manual          boolean not null default false,
  acepta_notas         boolean,           -- publica notas de prensa de terceros
  fuentes              text[] not null default '{}',  -- de dónde sale cada dato
  verificado_at        date,
  revisar_at           date,
  actualizado          timestamptz not null default now()
);
create index if not exists medios_tipo on medios (tipo_medio);
create index if not exists medios_ambitos on medios using gin (ambitos);

-- ---------- ficha de periodista ----------
create table if not exists periodistas (
  persona_id           uuid primary key references crm_personas(id),
  rol                  text check (rol is null or rol in ('director', 'redactor_jefe', 'jefe_seccion', 'redactor', 'colaborador',
                                                         'freelance', 'corresponsal', 'editor_newsletter', 'comunicacion', 'otro')),
  temas                text[] not null default '{}',
  telefono_corporativo text check (telefono_corporativo is null or length(regexp_replace(telefono_corporativo, '\D', '', 'g')) between 9 and 15),
  otros_medios         text[] not null default '{}',
  articulo_url         text check (articulo_url is null or length(articulo_url) <= 400),
  articulo_titulo      text check (articulo_titulo is null or length(articulo_titulo) <= 300),
  articulo_fecha       date,
  redes                jsonb not null default '[]'::jsonb,
  comentario_ia        text check (comentario_ia is null or length(comentario_ia) <= 1200),
  importancia          smallint check (importancia between 1 and 5),
  importancia_manual   boolean not null default false,
  colaboracion         text check (colaboracion is null or colaboracion in ('colaborador', 'neutral', 'poco_colaborador')),
  colaboracion_manual  boolean not null default false,
  prob_publicacion     numeric(3,2) check (prob_publicacion between 0 and 1),
  prob_manual          boolean not null default false,
  suscriptor_moticias  boolean not null default false,
  suscriptor_at        timestamptz,
  fuentes              text[] not null default '{}',
  verificado_at        date,
  actualizado          timestamptz not null default now()
);

-- ---------- envíos (broadcast) ----------
create table if not exists prensa_envios (
  id            bigint generated always as identity primary key,
  tipo          text not null check (tipo in ('nota_de_prensa', 'noticia', 'comunicado', 'invitacion_suscripcion',
                                              'mensaje_editor', 'mensaje_redaccion')),
  por_cuenta_de uuid references crm_cuentas(id),   -- cliente para el que se difunde (null = MOTICIAS)
  asunto        text not null check (length(btrim(asunto)) between 3 and 200),
  cuerpo        text check (cuerpo is null or length(cuerpo) <= 20000),
  pieza_url     text check (pieza_url is null or length(pieza_url) <= 400),
  filtro        jsonb not null default '{}'::jsonb, -- criterios con los que se eligieron los destinatarios
  estado        text not null default 'borrador' check (estado in ('borrador', 'aprobado', 'enviado', 'anulado')),
  creado_por    text,
  creado_at     timestamptz not null default now(),
  aprobado_por  text,
  aprobado_at   timestamptz,
  enviado_at    timestamptz,
  brevo_ref     text
);

create table if not exists prensa_destinatarios (
  id          bigint generated always as identity primary key,
  envio_id    bigint not null references prensa_envios(id),
  persona_id  uuid references crm_personas(id),
  cuenta_id   uuid references crm_cuentas(id),
  correo      text not null check (correo ~ '^[^@\s]+@[^@\s]+\.[^@\s]+$'),
  estado      text not null default 'pendiente' check (estado in ('pendiente', 'enviado', 'abierto', 'clic', 'respondido',
                                                                  'rebotado', 'baja', 'error')),
  detalle     text check (detalle is null or length(detalle) <= 300),
  at          timestamptz not null default now()
);
create index if not exists prensa_dest_envio on prensa_destinatarios (envio_id);
create index if not exists prensa_dest_persona on prensa_destinatarios (persona_id);
create unique index if not exists prensa_dest_unico on prensa_destinatarios (envio_id, lower(correo));

-- ---------- coberturas (artículos publicados a raíz de un envío nuestro) ----------
create table if not exists prensa_coberturas (
  id           bigint generated always as identity primary key,
  envio_id     bigint references prensa_envios(id),
  cuenta_id    uuid not null references crm_cuentas(id),
  persona_id   uuid references crm_personas(id),
  url          text not null check (length(url) <= 500),
  titulo       text check (titulo is null or length(titulo) <= 300),
  fecha        date,
  alcance      text check (alcance is null or alcance in ('integra', 'parcial', 'mencion', 'cita')),
  detectada    text not null default 'manual' check (detectada in ('manual', 'agente')),
  at           timestamptz not null default now()
);
create unique index if not exists prensa_cob_url on prensa_coberturas (url);
create index if not exists prensa_cob_cuenta on prensa_coberturas (cuenta_id);

-- ---------- cálculo: colaboración, probabilidad e importancia ----------
-- Contacto = actividad del CRM de tipo correo, llamada, reunión, LinkedIn, WhatsApp o nota de prensa, o un destinatario
-- de un envío ya enviado. Sin contacto, la colaboración se queda vacía.
create or replace function prensa_recalcular() returns jsonb
language plpgsql set search_path = public as $$
declare n_m int; n_p int;
begin
  with c as (
    select m.cuenta_id,
           (select count(*) from crm_actividades a where a.cuenta_id = m.cuenta_id
              and a.tipo in ('correo_saliente', 'correo_entrante', 'llamada', 'reunion', 'linkedin', 'whatsapp', 'nota_de_prensa'))
         + (select count(*) from prensa_destinatarios d where d.cuenta_id = m.cuenta_id and d.estado <> 'pendiente') as contactos,
           (select count(*) from crm_actividades a where a.cuenta_id = m.cuenta_id and a.tipo in ('correo_entrante', 'llamada', 'reunion'))
         + (select count(*) from prensa_destinatarios d where d.cuenta_id = m.cuenta_id and d.estado = 'respondido') as respuestas,
           (select count(distinct d.envio_id) from prensa_destinatarios d join prensa_envios e on e.id = d.envio_id
              where d.cuenta_id = m.cuenta_id and e.tipo in ('nota_de_prensa', 'noticia', 'comunicado')
                and d.estado not in ('pendiente', 'rebotado', 'error')) as envios,
           (select count(*) from prensa_coberturas k where k.cuenta_id = m.cuenta_id) as coberturas
    from medios m
  )
  update medios m set
    colaboracion = case when m.colaboracion_manual then m.colaboracion
                        when c.contactos = 0 then null
                        when c.coberturas >= 1 or c.respuestas >= 2 then 'colaborador'
                        when c.envios >= 3 and c.coberturas = 0 and c.respuestas = 0 then 'poco_colaborador'
                        else 'neutral' end,
    prob_publicacion = case when m.prob_manual then m.prob_publicacion
                            when m.prob_previa is null then null
                            else round(((c.coberturas + 2 * m.prob_previa) / (c.envios + 2))::numeric, 2) end,
    actualizado = now()
  from c where c.cuenta_id = m.cuenta_id;
  get diagnostics n_m = row_count;

  with c as (
    select p.persona_id, x.cuenta_id,
           (select count(*) from crm_actividades a where a.persona_id = p.persona_id
              and a.tipo in ('correo_saliente', 'correo_entrante', 'llamada', 'reunion', 'linkedin', 'whatsapp', 'nota_de_prensa'))
         + (select count(*) from prensa_destinatarios d where d.persona_id = p.persona_id and d.estado <> 'pendiente') as contactos,
           (select count(*) from crm_actividades a where a.persona_id = p.persona_id and a.tipo in ('correo_entrante', 'llamada', 'reunion'))
         + (select count(*) from prensa_destinatarios d where d.persona_id = p.persona_id and d.estado = 'respondido') as respuestas,
           (select count(distinct d.envio_id) from prensa_destinatarios d join prensa_envios e on e.id = d.envio_id
              where d.persona_id = p.persona_id and e.tipo in ('nota_de_prensa', 'noticia', 'comunicado')
                and d.estado not in ('pendiente', 'rebotado', 'error')) as envios,
           (select count(*) from prensa_coberturas k where k.persona_id = p.persona_id) as coberturas
    from periodistas p join crm_personas x on x.id = p.persona_id
  )
  update periodistas p set
    colaboracion = case when p.colaboracion_manual then p.colaboracion
                        when c.contactos = 0 then null
                        when c.coberturas >= 1 or c.respuestas >= 2 then 'colaborador'
                        when c.envios >= 3 and c.coberturas = 0 and c.respuestas = 0 then 'poco_colaborador'
                        else 'neutral' end,
    prob_publicacion = case when p.prob_manual then p.prob_publicacion
                            else (select m.prob_publicacion from medios m where m.cuenta_id = c.cuenta_id) end,
    importancia = case when p.importancia_manual or p.importancia is not null then p.importancia
                       else (select m.importancia from medios m where m.cuenta_id = c.cuenta_id) end,
    actualizado = now()
  from c where c.persona_id = p.persona_id;
  get diagnostics n_p = row_count;
  return jsonb_build_object('medios', n_m, 'periodistas', n_p, 'at', now());
end $$;

-- ---------- vistas de trabajo ----------
create or replace view medios_hoy with (security_invoker = true) as
select c.id, c.nombre, c.web, c.dominio, c.sector, c.notas, c.etiquetas, c.archivada_at,
       m.tipo_medio, m.formatos, m.alcance, m.ambitos, m.periodicidad, m.grupo, m.correo_redaccion, m.correo_notas,
       m.telefono_corporativo, m.direccion, m.cp, m.ciudad, m.region, m.pais, m.redes, m.audiencia, m.referencias,
       m.comentario_ia, m.importancia, m.importancia_manual, m.colaboracion, m.colaboracion_manual, m.prob_previa,
       m.prob_publicacion, m.prob_manual, m.acepta_notas, m.fuentes, m.verificado_at,
       (select e.estado from crm_estados e where e.cuenta_id = c.id order by e.id desc limit 1) as estado,
       (select count(*) from crm_personas x where x.cuenta_id = c.id and x.archivada_at is null) as personas,
       (select count(*) from crm_personas x join periodistas p on p.persona_id = x.id
          where x.cuenta_id = c.id and p.suscriptor_moticias) as suscriptores,
       (select count(*) from prensa_coberturas k where k.cuenta_id = c.id) as coberturas,
       (select max(a.at) from crm_actividades a where a.cuenta_id = c.id) as ultima_actividad
from crm_cuentas c join medios m on m.cuenta_id = c.id
where c.tipo = 'medio';

create or replace view periodistas_hoy with (security_invoker = true) as
select x.id, x.cuenta_id, c.nombre as medio, x.nombre, x.cargo, x.correo, x.telefono, x.linkedin, x.no_contactar_at,
       x.permiso_correo_at, x.archivada_at, x.ghost_member_id,
       p.rol, p.temas, p.telefono_corporativo, p.otros_medios, p.articulo_url, p.articulo_titulo, p.articulo_fecha, p.redes,
       p.comentario_ia, p.importancia, p.importancia_manual, p.colaboracion, p.colaboracion_manual, p.prob_publicacion,
       p.prob_manual, p.suscriptor_moticias, p.suscriptor_at, p.fuentes, p.verificado_at,
       (select count(*) from prensa_coberturas k where k.persona_id = x.id) as coberturas
from crm_personas x join periodistas p on p.persona_id = x.id left join crm_cuentas c on c.id = x.cuenta_id;

-- ---------- permisos: solo el gestor, con su llave; nadie borra ----------
do $$
declare t text;
begin
  foreach t in array array['medios', 'periodistas', 'prensa_envios', 'prensa_destinatarios', 'prensa_coberturas'] loop
    execute format('alter table %I enable row level security', t);
    execute format('revoke all on %I from public, anon, authenticated', t);
    execute format('drop policy if exists gestor on %I', t);
    execute format('create policy gestor on %I for all to anon using (privado.gestor_ok()) with check (privado.gestor_ok())', t);
    execute format('grant select, insert, update on %I to anon', t);
  end loop;
end $$;
grant usage on all sequences in schema public to anon;
revoke all on medios_hoy, periodistas_hoy from public, anon, authenticated;
grant select on medios_hoy, periodistas_hoy to anon;
revoke all on function prensa_recalcular() from public, anon, authenticated;
-- El recálculo lo lanza la tarea de los miércoles (conector de Supabase) o el gestor por RPC con su llave
-- (/rest/v1/rpc/prensa_recalcular_gestor: sin la llave solo contesta «sin llave»):
create or replace function public.prensa_recalcular_gestor() returns jsonb
language plpgsql security definer set search_path = public as $$
begin
  if not privado.gestor_ok() then raise exception 'sin llave'; end if;
  return public.prensa_recalcular();
end $$;
revoke all on function public.prensa_recalcular_gestor() from public;
grant execute on function public.prensa_recalcular_gestor() to anon;
