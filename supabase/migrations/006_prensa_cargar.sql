-- =====================================================================
-- MOTICIAS · 006 · CARGA DE LA BASE DE PRENSA DESDE JSON (9 nov 2026)
--
-- `select prensa_cargar('{"medios": [...]}'::jsonb)` crea o completa cada medio por su dominio, sin pisar lo que alguien
-- fijó a mano; añade periodistas por correo o por (medio, nombre) y coberturas por URL. Mismo formato que
-- `src/prensa.py validar` (cada medio lleva `dominio`, que pone `src/prensa.py json`). Solo la usa el conector de
-- Supabase (rol de servicio): no se publica a anon. Se aplicó el 9-11-2026 con la 005. SE PUEDE APLICAR DOS VECES.
-- =====================================================================
create or replace function prensa_cargar(dato jsonb) returns jsonb
language plpgsql set search_path = public as $$
declare
  m jsonb; p jsonb; k jsonb; cid uuid; pid uuid; dom text; v_correo text; v_nom text;
  n_med int := 0; n_nuevos int := 0; n_per int := 0; n_cob int := 0;
  arr text[];
begin
  for m in select * from jsonb_array_elements(dato->'medios') loop
    dom := lower(m->>'dominio');
    continue when dom is null;
    select c.id into cid from crm_cuentas c where c.tipo = 'medio' and c.dominio = dom and archivada_at is null limit 1;
    if cid is null then
      insert into crm_cuentas (producto, tipo, nombre, web, dominio, sector, origen, creada_por)
      values ('moticias', 'medio', m->>'nombre', m->>'web', dom, m->>'sector', 'agente', 'medios-actualizar') returning id into cid;
      insert into crm_estados (cuenta_id, estado, quien, motivo) values (cid, 'sin_contacto', 'medios-actualizar', 'alta');
      n_nuevos := n_nuevos + 1;
    end if;
    insert into medios (cuenta_id, tipo_medio, formatos, alcance, ambitos, periodicidad, grupo, correo_redaccion, correo_notas,
                        telefono_corporativo, direccion, cp, ciudad, region, pais, redes, audiencia, referencias, comentario_ia,
                        importancia, prob_previa, acepta_notas, fuentes, verificado_at, revisar_at)
    values (cid, coalesce(m->>'tipo_medio', 'otro'),
            coalesce(array(select jsonb_array_elements_text(m->'formatos')), '{}'), m->>'alcance',
            coalesce(array(select jsonb_array_elements_text(m->'ambitos')), '{}'), m->>'periodicidad', m->>'grupo',
            m->>'correo_redaccion', m->>'correo_notas', m->>'telefono_corporativo', m->>'direccion', m->>'cp', m->>'ciudad',
            m->>'region', coalesce(m->>'pais', 'España'), coalesce(m->'redes', '[]'), coalesce(m->'audiencia', '{}'),
            m->>'referencias', m->>'comentario_ia', (m->>'importancia')::smallint, (m->>'prob_previa')::numeric,
            (m->>'acepta_notas')::boolean, coalesce(array(select jsonb_array_elements_text(m->'fuentes')), '{}'),
            (m->>'verificado_at')::date, (m->>'revisar_at')::date)
    on conflict (cuenta_id) do update set
      tipo_medio = coalesce(m->>'tipo_medio', medios.tipo_medio),
      formatos = case when jsonb_array_length(coalesce(m->'formatos', '[]')) > 0 then excluded.formatos else medios.formatos end,
      alcance = coalesce(excluded.alcance, medios.alcance),
      ambitos = case when jsonb_array_length(coalesce(m->'ambitos', '[]')) > 0 then excluded.ambitos else medios.ambitos end,
      periodicidad = coalesce(excluded.periodicidad, medios.periodicidad), grupo = coalesce(excluded.grupo, medios.grupo),
      correo_redaccion = coalesce(excluded.correo_redaccion, medios.correo_redaccion),
      correo_notas = coalesce(excluded.correo_notas, medios.correo_notas),
      telefono_corporativo = coalesce(excluded.telefono_corporativo, medios.telefono_corporativo),
      direccion = coalesce(excluded.direccion, medios.direccion), cp = coalesce(excluded.cp, medios.cp),
      ciudad = coalesce(excluded.ciudad, medios.ciudad), region = coalesce(excluded.region, medios.region),
      pais = coalesce(m->>'pais', medios.pais),
      redes = case when jsonb_array_length(coalesce(m->'redes', '[]')) > 0 then excluded.redes else medios.redes end,
      audiencia = medios.audiencia || coalesce(m->'audiencia', '{}'),
      referencias = coalesce(excluded.referencias, medios.referencias),
      comentario_ia = coalesce(excluded.comentario_ia, medios.comentario_ia),
      importancia = case when medios.importancia_manual then medios.importancia else coalesce(excluded.importancia, medios.importancia) end,
      prob_previa = coalesce(excluded.prob_previa, medios.prob_previa),
      acepta_notas = coalesce(excluded.acepta_notas, medios.acepta_notas),
      fuentes = array(select distinct unnest(medios.fuentes || excluded.fuentes)),
      verificado_at = coalesce(excluded.verificado_at, medios.verificado_at),
      revisar_at = coalesce(excluded.revisar_at, medios.revisar_at), actualizado = now();
    n_med := n_med + 1;

    for p in select * from jsonb_array_elements(coalesce(m->'periodistas', '[]')) loop
      v_correo := nullif(lower(btrim(p->>'correo')), ''); v_nom := nullif(btrim(p->>'nombre'), ''); pid := null;
      continue when v_correo is null and v_nom is null;
      if v_correo is not null then select x.id into pid from crm_personas x where lower(x.correo) = v_correo limit 1; end if;
      if pid is null and v_nom is not null then
        select x.id into pid from crm_personas x where x.cuenta_id = cid and lower(x.nombre) = lower(v_nom) limit 1;
      end if;
      if pid is null then
        insert into crm_personas (cuenta_id, nombre, cargo, perfil, correo, telefono, linkedin, verificado, creada_por)
        values (cid, v_nom, left(p->>'cargo', 160), 'periodista', v_correo, p->>'telefono', p->>'linkedin',
                jsonb_array_length(coalesce(p->'fuentes', '[]')) > 0, 'medios-actualizar') returning id into pid;
      else
        update crm_personas x set cargo = coalesce(left(p->>'cargo', 160), x.cargo), correo = coalesce(x.correo, v_correo),
               telefono = coalesce(x.telefono, p->>'telefono'), linkedin = coalesce(x.linkedin, p->>'linkedin') where x.id = pid;
      end if;
      insert into periodistas (persona_id, rol, temas, telefono_corporativo, otros_medios, articulo_url, articulo_titulo,
                               articulo_fecha, redes, comentario_ia, importancia, fuentes, verificado_at)
      values (pid, p->>'rol', coalesce(array(select jsonb_array_elements_text(p->'temas')), '{}'), p->>'telefono_corporativo',
              coalesce(array(select jsonb_array_elements_text(p->'otros_medios')), '{}'), p->>'articulo_url', p->>'articulo_titulo',
              (p->>'articulo_fecha')::date, coalesce(p->'redes', '[]'), p->>'comentario_ia', (p->>'importancia')::smallint,
              coalesce(array(select jsonb_array_elements_text(p->'fuentes')), '{}'), (p->>'verificado_at')::date)
      on conflict (persona_id) do update set
        rol = coalesce(excluded.rol, periodistas.rol),
        temas = case when cardinality(excluded.temas) > 0 then excluded.temas else periodistas.temas end,
        telefono_corporativo = coalesce(excluded.telefono_corporativo, periodistas.telefono_corporativo),
        articulo_url = coalesce(excluded.articulo_url, periodistas.articulo_url),
        articulo_titulo = coalesce(excluded.articulo_titulo, periodistas.articulo_titulo),
        articulo_fecha = coalesce(excluded.articulo_fecha, periodistas.articulo_fecha),
        redes = case when jsonb_array_length(excluded.redes) > 0 then excluded.redes else periodistas.redes end,
        comentario_ia = coalesce(excluded.comentario_ia, periodistas.comentario_ia),
        importancia = case when periodistas.importancia_manual then periodistas.importancia else coalesce(excluded.importancia, periodistas.importancia) end,
        fuentes = array(select distinct unnest(periodistas.fuentes || excluded.fuentes)),
        verificado_at = coalesce(excluded.verificado_at, periodistas.verificado_at), actualizado = now();
      n_per := n_per + 1;
    end loop;

    for k in select * from jsonb_array_elements(coalesce(m->'coberturas', '[]')) loop
      insert into prensa_coberturas (cuenta_id, url, titulo, fecha, alcance, detectada, envio_id)
      values (cid, k->>'url', k->>'titulo', (k->>'fecha')::date, k->>'alcance', 'agente', (k->>'envio_id')::bigint)
      on conflict (url) do nothing;
      if found then n_cob := n_cob + 1; end if;
    end loop;
  end loop;
  perform prensa_recalcular();
  return jsonb_build_object('medios', n_med, 'nuevos', n_nuevos, 'periodistas', n_per, 'coberturas', n_cob);
end $$;
revoke all on function prensa_cargar(jsonb) from public, anon, authenticated;
