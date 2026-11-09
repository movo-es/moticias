-- =====================================================================
-- MOTICIAS · 004 · LA LLAVE DEL GESTOR, FUERA DE LA API (9 nov 2026)
--
-- El asesor de seguridad de Supabase avisó de que `public.gestor_ok()` se podía llamar como /rest/v1/rpc/gestor_ok:
-- solo contesta sí o no a una llave de 256 bits, pero no tiene por qué estar a la vista. Se muda a un esquema que
-- PostgREST no publica (`privado`) y las políticas la llaman desde ahí. Además, las dos funciones de disparador fijan
-- su search_path. Aplicada en el proyecto «moticias» el 9-11-2026. SE PUEDE APLICAR DOS VECES.
-- =====================================================================
create schema if not exists privado;
revoke all on schema privado from public;
grant usage on schema privado to anon, authenticated;
create or replace function privado.gestor_ok() returns boolean
language sql stable security definer set search_path = public, extensions as $$
  select exists (
    select 1 from public.gestor_llave
    where huella = encode(extensions.digest(coalesce(
      nullif(current_setting('request.headers', true), '')::json ->> 'x-moticias-clave', ''), 'sha256'), 'hex')
  );
$$;
revoke all on function privado.gestor_ok() from public;
grant execute on function privado.gestor_ok() to anon, authenticated;
do $$
declare t text;
begin
  foreach t in array array['equipo', 'crm_cuentas', 'crm_personas', 'crm_estados', 'crm_actividades', 'crm_pasos',
                           'crm_contratos', 'gestor_registro'] loop
    execute format('drop policy if exists gestor on %I', t);
    execute format('create policy gestor on %I for all to anon using (privado.gestor_ok()) with check (privado.gestor_ok())', t);
  end loop;
end $$;
drop function if exists public.gestor_ok();
alter function public.crm_no_contactar_para_siempre() set search_path = public;
alter function public.crm_solo_anadir() set search_path = public;
