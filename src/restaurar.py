"""MOTICIAS · Restauración desde el gestor (cambio OpenSpec restaurar-copia, «sí» de Rainer del 15-11-2026). Solo biblioteca estándar.

Lógica sin red (la usa api/gestor.py, que pone GitHub, Ghost, la base y el correo):
  - qué documentos se pueden restaurar y quién (`puede_contenido`), con las reglas de verticals → restauracion;
  - las diferencias campo a campo entre una versión y la actual (`diferencias`);
  - el documento restaurado (`restaurado`): el contenido de la versión elegida, conservando lo que no se restaura (estado,
    revisiones, cajas, correcciones) y completando tipo de contenido y ejes si la versión antigua no los tenía;
  - qué tablas de la base privada puede recuperar cada perfil (`tablas_permitidas`).
Nunca se borra nada: restaurar escribe una versión nueva y se puede deshacer restaurando la anterior.
"""
import copy, datetime, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tipos as T  # noqa: E402

RUTA_OK = re.compile(r"^data/[a-z-]+/[A-Za-z0-9._-]+\.json$")


def cfg(v):
    return v.get("restauracion") or {}


def coleccion(ruta):
    return ruta.split("/")[1] if ruta.count("/") >= 2 else ""


def ruta_valida(ruta, v):
    return bool(RUTA_OK.match(ruta or "")) and ".." not in ruta and any(ruta.startswith(p) for p in cfg(v).get("contenido", {}))


def es_del_director(doc, v):
    return bool(doc) and (doc.get("author") or "") in T.firmas_director(v)


def puede_contenido(perfil, ruta, actual, antigua, v):
    """(True, "") o (False, motivo)."""
    if not ruta_valida(ruta, v):
        return False, "ese documento no se restaura desde el gestor"
    if perfil == "superadmin":
        return True, ""
    if any(ruta.startswith(p) for p in cfg(v).get("solo_superadmin_contenido", [])):
        return False, "los productos solo los restaura el editor jefe"
    if es_del_director(actual, v) or es_del_director(antigua, v):
        return False, "las piezas que firma el director solo las restaura él"
    if ruta.startswith("data/articles/"):
        if (actual or {}).get("status") != "publicado":
            return False, "la pieza no está publicada hoy: la restaura el editor jefe"
        if (antigua or {}).get("status") not in (None, "publicado"):
            return False, "esa versión no llegó a publicarse: solo el editor jefe la puede recuperar"
    return True, ""


def _corto(x, n=280):
    if isinstance(x, str):
        return x if len(x) <= n else x[: n - 1] + "…"
    s = json.dumps(x, ensure_ascii=False)
    return s if len(s) <= n else s[: n - 1] + "…"


def diferencias(antigua, actual):
    """Lista de {campo, antes (versión elegida), ahora (hoy)}, resumida para leerla en el móvil."""
    out = []
    for k in sorted(set(antigua or {}) | set(actual or {})):
        a, b = (antigua or {}).get(k), (actual or {}).get(k)
        if a == b:
            continue
        if k == "body_md":
            pa, pb = len(str(a or "").split()), len(str(b or "").split())
            out.append({"campo": k, "antes": "texto de %d palabras" % pa, "ahora": "texto de %d palabras" % pb, "largo": True})
            continue
        out.append({"campo": k, "antes": _corto(a), "ahora": _corto(b)})
    return out


def restaurado(antigua, actual, ruta, perfil, quien, sha, fecha_version, motivo, v):
    """El documento que se escribe al restaurar."""
    c = cfg(v)
    nuevo = copy.deepcopy(antigua)
    ahora = datetime.datetime.now().astimezone().isoformat(timespec="minutes")
    if ruta.startswith("data/articles/"):
        for k in c.get("conservar_en_pieza", []):
            if k in (actual or {}):
                nuevo[k] = copy.deepcopy(actual[k])
            else:
                nuevo.pop(k, None)
        for k in c.get("completar_si_faltan", []):
            if not nuevo.get(k) and (actual or {}).get(k):
                nuevo[k] = copy.deepcopy(actual[k])
        if not nuevo.get("tipo_contenido"):
            nuevo["tipo_contenido"] = T.deducir(nuevo, "articles")
        nuevo["revised_at"] = ahora
        nuevo.setdefault("revisiones", []).append({"en": ahora, "por": quien, "accion": "restaurar",
                                                   "version": (sha or "")[:7], "de": fecha_version, "motivo": (motivo or "")[:300]})
    else:
        if perfil != "superadmin" and "status" in (actual or {}):
            nuevo["status"] = actual["status"]  # el editor no activa ni pausa nada al restaurar
        if "updated_at" in nuevo or "updated_at" in (actual or {}):
            nuevo["updated_at"] = ahora
        if ruta.startswith("data/ads/"):
            nuevo["tipo_contenido"] = "patrocinado"
    return nuevo


def tablas_permitidas(perfil, v):
    c = cfg(v)
    t = list(c.get("tablas_editor", []))
    if perfil == "superadmin":
        t += c.get("tablas_superadmin_ademas", [])
    return t if perfil in ("superadmin", "editor") else []


def titulo(doc, ruta):
    d = doc or {}
    return d.get("title") or d.get("headline") or d.get("name") or d.get("titulo") or os.path.basename(ruta)[:-5]
