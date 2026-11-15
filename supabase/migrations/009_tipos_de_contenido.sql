-- =====================================================================
-- MOTICIAS · 009 · Tipos de contenido (cambio OpenSpec tipos-de-contenido, aprobado por Rainer el 15-11-2026)
--
-- Las cuatro cajas de servicios del grupo de data/ads/ cambian de identificador (casa-… → grupo-…) y de tipo (→ grupo).
-- Esta migración traslada su historia del seguimiento a los identificadores nuevos, para que el editor jefe vea una sola
-- serie antes y después del cambio, y amplía la lista de tipos admitidos donde la hay.
--
-- · pub_diario: si el identificador nuevo ya tiene fila para el mismo día, hueco y página, se le suman las cifras de la
--   antigua y la antigua se queda a cero (no se borra); si no, la fila cambia de identificador.
-- · pub_comprobaciones: es de solo añadir; se levanta su protección solo durante el traslado del identificador y se vuelve a
--   poner en la misma transacción. No se borra ninguna fila.
-- · crm_contratos.anuncio_id: mismo traslado.
-- · campaigns (001, si existe): el tipo antiguo de las cajas del grupo pasa a grupo y la lista de tipos admitidos queda en
--   patrocinio, banner, contenido, edicion-a-medida, grupo y publicidad.
-- SE PUEDE APLICAR DOS VECES: la segunda vez no encuentra nada que trasladar.
-- =====================================================================

do $$
declare
  par record;
begin
  for par in select * from (values
      ('casa-anunciate', 'grupo-anunciate'),
      ('casa-ediciones-a-medida', 'grupo-ediciones-a-medida'),
      ('casa-movo-licitaciones', 'grupo-movo-licitaciones'),
      ('casa-movo-pmst', 'grupo-movo-pmst')) as t(viejo, nuevo)
  loop
    -- pub_diario: primero se suman las filas que chocarían con una del identificador nuevo…
    update pub_diario n
       set impresiones = n.impresiones + o.impresiones, clics = n.clics + o.clics
      from pub_diario o
     where o.anuncio = par.viejo and n.anuncio = par.nuevo
       and o.dia = n.dia and o.hueco = n.hueco and o.pagina = n.pagina
       and (o.impresiones > 0 or o.clics > 0);
    update pub_diario o
       set impresiones = 0, clics = 0
     where o.anuncio = par.viejo
       and exists (select 1 from pub_diario n where n.anuncio = par.nuevo and n.dia = o.dia and n.hueco = o.hueco and n.pagina = o.pagina);
    -- … y el resto cambia de identificador.
    update pub_diario o
       set anuncio = par.nuevo
     where o.anuncio = par.viejo
       and not exists (select 1 from pub_diario n where n.anuncio = par.nuevo and n.dia = o.dia and n.hueco = o.hueco and n.pagina = o.pagina);

    if to_regclass('public.crm_contratos') is not null then
      execute 'update crm_contratos set anuncio_id = $1 where anuncio_id = $2' using par.nuevo, par.viejo;
    end if;
  end loop;
end $$;

-- pub_comprobaciones (solo añadir): traslado del identificador con la protección levantada un instante.
alter table pub_comprobaciones disable trigger t_comprobaciones_solo_anadir;
update pub_comprobaciones set anuncio = 'grupo-anunciate' where anuncio = 'casa-anunciate';
update pub_comprobaciones set anuncio = 'grupo-ediciones-a-medida' where anuncio = 'casa-ediciones-a-medida';
update pub_comprobaciones set anuncio = 'grupo-movo-licitaciones' where anuncio = 'casa-movo-licitaciones';
update pub_comprobaciones set anuncio = 'grupo-movo-pmst' where anuncio = 'casa-movo-pmst';
alter table pub_comprobaciones enable trigger t_comprobaciones_solo_anadir;

-- campaigns (001): tipos admitidos.
do $$
begin
  if to_regclass('public.campaigns') is not null then
    alter table campaigns drop constraint if exists campaigns_type_check;
    update campaigns set type = 'grupo' where type not in ('patrocinio', 'banner', 'contenido', 'edicion-a-medida', 'grupo', 'publicidad');
    alter table campaigns add constraint campaigns_type_check
      check (type in ('patrocinio', 'banner', 'contenido', 'edicion-a-medida', 'grupo', 'publicidad'));
  end if;
end $$;
