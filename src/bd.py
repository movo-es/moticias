"""MOTICIAS · Base de datos privada del gestor (Supabase «moticias», migración 003). Solo biblioteca estándar.

El gestor habla con PostgREST con la clave pública del proyecto y la cabecera `x-moticias-clave`; la base guarda solo la
huella de esa clave y todas sus políticas la piden (`gestor_ok()`). Variables de entorno (en Vercel, nunca aquí):
  SUPABASE_URL        https://<ref>.supabase.co
  SUPABASE_ANON_KEY   clave pública (anon) del proyecto
  MOTICIAS_BD_CLAVE   la llave del gestor (su huella sha256 está en la tabla gestor_llave)
"""
import json, os, urllib.error, urllib.parse, urllib.request


def configurada():
    return all(os.environ.get(k) for k in ("SUPABASE_URL", "SUPABASE_ANON_KEY", "MOTICIAS_BD_CLAVE"))


class ErrorBD(Exception):
    pass


def _cab(extra=None):
    k = os.environ.get("SUPABASE_ANON_KEY", "")
    h = {"apikey": k, "Authorization": "Bearer " + k, "x-moticias-clave": os.environ.get("MOTICIAS_BD_CLAVE", ""),
         "Content-Type": "application/json", "Accept": "application/json"}
    h.update(extra or {})
    return h


def peticion(metodo, tabla, params=None, cuerpo=None, prefer=None):
    """Devuelve la lista de filas (o []). Lanza ErrorBD con el mensaje de PostgREST si algo falla."""
    if not configurada():
        raise ErrorBD("la base de datos del gestor no está configurada (SUPABASE_URL, SUPABASE_ANON_KEY, MOTICIAS_BD_CLAVE)")
    url = "%s/rest/v1/%s" % (os.environ["SUPABASE_URL"].rstrip("/"), tabla)
    if params:
        url += "?" + urllib.parse.urlencode(params, safe="(),.:*")
    extra = {"Prefer": prefer} if prefer else {}
    req = urllib.request.Request(url, method=metodo, headers=_cab(extra),
                                 data=json.dumps(cuerpo).encode("utf-8") if cuerpo is not None else None)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            raw = r.read()
            return json.loads(raw) if raw else []
    except urllib.error.HTTPError as e:
        try:
            d = json.loads(e.read() or b"{}")
        except ValueError:
            d = {}
        raise ErrorBD(d.get("message") or d.get("hint") or "error de la base (%s)" % e.code)
    except urllib.error.URLError as e:
        raise ErrorBD("la base no contesta: %s" % e.reason)


def leer(tabla, **params):
    return peticion("GET", tabla, params)


def insertar(tabla, filas):
    return peticion("POST", tabla, cuerpo=filas, prefer="return=representation")


def actualizar(tabla, filtro, cambios):
    return peticion("PATCH", tabla, filtro, cambios, prefer="return=representation")


def upsert(tabla, filas, conflicto="id"):
    return peticion("POST", tabla, {"on_conflict": conflicto}, filas, prefer="resolution=merge-duplicates,return=representation")


def registrar(quien, accion, objeto=None, detalle=None):
    """Apunta en gestor_registro. Nunca hace fallar la acción que registra."""
    if not configurada():
        return
    try:
        insertar("gestor_registro", {"quien": quien or "?", "accion": accion[:60], "objeto": (objeto or "")[:200] or None, "detalle": detalle or {}})
    except ErrorBD:
        pass
