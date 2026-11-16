-- =====================================================================
-- MOTICIAS · 016 · Barridos pedidos desde el gestor (16-11-2026)
--
-- Las tareas programadas de la cuenta de Rainer no se pueden lanzar por API (claude.ai solo ofrece el activador
-- «Programación»), así que el botón «Iniciar barrido de noticias ahora» deja aquí el encargo y lo recoge la siguiente
-- tarea que corre: la de retoques y noticias del gestor (laborables, cada hora de 8 a 21) o las batidas de fin de semana
-- (11:00 y 17:30). La pista del editor es un dato para la búsqueda, nunca una instrucción.
-- De solo añadir en lo esencial: no se borra ningún pedido; se cierra con su estado y su resultado.
-- SE PUEDE APLICAR DOS VECES.
-- =====================================================================
create table if not exists barridos_pedidos (
  id           bigint generated always as identity primary key,
  pedido_por   text not null check (length(pedido_por) <= 120),
  perfil       text check (perfil is null or length(perfil) <= 40),
  pista        text check (pista is null or length(pista) <= 200),
  estado       text not null default 'pendiente' check (estado in ('pendiente', 'en_curso', 'hecho', 'sin_novedades', 'error')),
  resultado    text check (resultado is null or length(resultado) <= 2000),
  atendido_por text check (atendido_por is null or length(atendido_por) <= 120),
  creado_at    timestamptz not null default now(),
  atendido_at  timestamptz,
  cerrado_at   timestamptz
);
create index if not exists barridos_pedidos_estado on barridos_pedidos (estado, creado_at);
alter table barridos_pedidos enable row level security;
drop policy if exists gestor on barridos_pedidos;
create policy gestor on barridos_pedidos for all to anon using (privado.gestor_ok()) with check (privado.gestor_ok());
drop trigger if exists t_barridos_no_borrar on barridos_pedidos;
create trigger t_barridos_no_borrar before delete on barridos_pedidos for each row execute function crm_solo_anadir();
