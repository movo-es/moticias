#!/usr/bin/env python3
"""MOTICIAS · Cola del editor (cambio `cola-del-editor`, decisiones de Rainer del 15 y 16-11-2026). Solo biblioteca estándar.

Qué es. Una lista rápida de temas nuevos para el editor jefe, dentro del gestor (pestaña «Cola»), usable desde el móvil.
La edición de la mañana sigue siendo automática; la cola recoge el resto: lo que el barrido encontró y no entró en la
edición, los avisos de las batidas y de los sensores, y lo que proponen los editores. Vive en la base privada
(Supabase, migración 012: `cola_temas`, `cola_correcciones`).

Reglas (decididas en la entrevista):
- Solo el editor jefe confirma y publica. «Confirmar» es un encargo a la redacción horaria (`encargos_gestor`, que atiende
  /noticias-gestor): investiga en fuente primaria, escribe con el estándar de siempre y publica con las reglas de siempre
  (rutinaria directa; crítica o con su firma, vuelve «Para aprobar»). Sin fuente primaria vuelve a la cola «Sin fuente».
  En fin de semana espera al lunes, salvo importancia 5, que lanza la batida de grandes noticias.
- Permisos: editor jefe todo; editor ve, propone, corrige etiquetas y sección, y archiva o recupera solo lo suyo;
  comercial ve (sin la solución del grupo) y propone; oficina no entra. Solo cuentan las correcciones de importancia del
  editor jefe para que el agente aprenda.
- Fiabilidad «sin confirmar» bloquea «Confirmar». «Borrar» es la papelera, recuperable para siempre: nada se borra.
- Caducidad: la fecha límite o, si no hay, 3 días laborables desde la fecha del hecho (o desde que entró). Lo editorial,
  «La voz del editor» y lo de referencia no caducan. Lo caducado pasa al archivo, nunca a la papelera.

Uso (rutinas; necesitan SUPABASE_URL, SUPABASE_ANON_KEY y MOTICIAS_BD_CLAVE, o la herramienta de Supabase):
  python3 -I src/cola.py proponer temas.json   # [{titulo, resumen, avisos:[{texto,fuente,url,fecha}], …}] → cola_temas
  python3 -I src/cola.py sql temas.json        # lo mismo, como SQL para `execute_sql` si la sesión no tiene las claves
  python3 -I src/cola.py ejemplos [N]          # las N últimas correcciones del editor jefe, para leerlas antes de proponer
  python3 -I src/cola.py aciertos [DIAS]       # en qué acierta y en qué falla el agente (informe mensual)
  python3 -I src/cola.py caducar               # pasa al archivo lo caducado (también lo hace el gestor al listar)
"""
import datetime, json, os, re, sys, unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bd as BD  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ESTADOS_COLA = ("nuevo", "propuesto", "sin_fuente")
ESTADOS_CONFIRMADOS = ("confirmado", "en_redaccion", "para_aprobar")
PESTANAS = {"cola": ESTADOS_COLA, "confirmados": ESTADOS_CONFIRMADOS, "publicados": ("publicado",),
            "archivo": ("archivado",), "papelera": ("papelera",)}
SOLUCIONES = ("MOVO", "MUFMI", "Movenbus")
SECCIONES = ("Tierra", "Mar", "Aire", "Logística", "Regulación", "Licitaciones", "Análisis")
CAMPOS_ETIQUETA = ("medio", "modos", "temas", "territorios", "fiabilidad", "event_date", "fecha_limite", "solucion", "seccion", "no_caduca")


def vertical(nombre="movilidad"):
    return json.load(open(os.path.join(ROOT, "verticals", nombre + ".json"), encoding="utf-8"))


# ---------- permisos ----------
def puede(perfil, accion, tema=None, nombre=None):
    """¿Puede este perfil hacer esta acción sobre este tema? (tabla de la entrevista, 16-11-2026)."""
    suyo = bool(tema) and tema.get("propuesto_por") and tema.get("propuesto_por") == nombre
    if perfil == "superadmin":
        return True
    if perfil == "editor":
        if accion in ("ver", "proponer", "editar", "seccion"):
            return True
        if accion in ("archivar", "papelera", "recuperar"):
            return suyo
        return False
    if perfil == "comercial":
        return accion in ("ver", "proponer")
    return False


def para_perfil(tema, perfil):
    """Lo que ve cada perfil: el comercial no ve la solución del grupo; nadie salvo el editor jefe ve la importancia del agente."""
    t = dict(tema)
    if perfil == "comercial":
        t.pop("solucion", None)
    if perfil != "superadmin":
        t.pop("importancia_agente", None)
    return t


# ---------- fechas ----------
def _pascua(y):
    a, b, c = y % 19, y // 100, y % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mes = (h + l - 7 * m + 114) // 31
    dia = ((h + l - 7 * m + 114) % 31) + 1
    return datetime.date(y, mes, dia)


def festivos(y):
    """Festivos nacionales fijos más Viernes Santo (calculado). Las comunidades no cuentan."""
    fijos = {(1, 1), (1, 6), (5, 1), (8, 15), (10, 12), (11, 1), (12, 6), (12, 8), (12, 25)}
    return {datetime.date(y, m, d) for m, d in fijos} | {_pascua(y) - datetime.timedelta(days=2)}


def laborable(d):
    return d.weekday() < 5 and d not in festivos(d.year)


def mas_laborables(d, n):
    while n > 0:
        d += datetime.timedelta(days=1)
        if laborable(d):
            n -= 1
    return d


def _fecha(s):
    try:
        return datetime.date.fromisoformat(str(s)[:10]) if s else None
    except ValueError:
        return None


def caduca(tema, dias=3):
    """Fecha de caducidad (date) o None si no caduca."""
    if tema.get("no_caduca"):
        return None
    lim = _fecha(tema.get("fecha_limite"))
    if lim:
        return lim
    base = _fecha(tema.get("event_date")) or _fecha(tema.get("creado_at")) or datetime.date.today()
    return mas_laborables(base, dias)


def hoy_madrid():
    return (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)).date()


# ---------- agrupación ----------
def plano(s):
    s = unicodedata.normalize("NFKD", str(s or "")).lower()
    return re.sub(r"[^a-z0-9 ]+", " ", "".join(c for c in s if not unicodedata.combining(c))).strip()


VACIAS = set("el la los las de del y en a por para con un una que se su sus al lo o e es son como mas tras sobre ante".split())


def clave_hecho(titulo, fecha=None):
    """Clave tosca del hecho: las seis palabras con más peso del titular, ordenadas, y el mes. Dos avisos con la misma clave
    se agrupan; el agente puede dar una clave propia (p. ej. el identificador del BOE) y entonces manda la suya."""
    pal = sorted({w for w in plano(titulo).split() if len(w) > 3 and w not in VACIAS}, key=lambda w: (-len(w), w))[:6]
    return ("%s|%s" % (" ".join(sorted(pal)), str(fecha or "")[:7]))[:200]


# ---------- proponer ----------
def normalizar(t, perfil=None, nombre=None, rutina=None):
    """Valida y completa un tema que llega del agente o de una persona."""
    from taxonomia import Taxonomia  # noqa: E402
    tx = Taxonomia()
    titulo = str(t.get("titulo") or "").strip()
    if len(titulo) < 8:
        raise ValueError("el titular de trabajo es demasiado corto")
    out = {"titulo": titulo[:300], "resumen": (str(t.get("resumen") or "").strip()[:4000] or None)}
    av = []
    for a in (t.get("avisos") or [])[:20]:
        if isinstance(a, dict) and (a.get("texto") or a.get("url")):
            url = str(a.get("url") or "")
            av.append({"texto": str(a.get("texto") or "")[:400], "fuente": str(a.get("fuente") or "")[:120],
                       "url": url[:600] if url.startswith("http") else "", "fecha": str(a.get("fecha") or "")[:10]})
    out["avisos"] = av
    out["medio"] = t.get("medio") if t.get("medio") in tx.medios and tx.medios[t["medio"]].get("activo") else None
    out["modos"] = [m for m in (t.get("modos") or []) if m in tx.modos_t][:3]
    out["temas"] = [m for m in (t.get("temas") or []) if m in tx.temas][:3]
    out["territorios"] = [m for m in (t.get("territorios") or []) if m in tx.territorios][:4]
    # Si faltan etiquetas, las propone la misma taxonomía que las piezas, a partir del titular y el resumen.
    if not (out["medio"] and out["temas"] and out["territorios"]):
        falsa = {"title": titulo, "summary": out["resumen"] or "", "tags": [], "kind": t.get("kind") or "noticia"}
        c = tx.clasificar(falsa)
        falsa.update(c)
        medio, modos = tx.medio_y_modos(falsa)
        out["medio"] = out["medio"] or medio
        out["modos"] = out["modos"] or modos
        out["temas"] = out["temas"] or c["temas"]
        out["territorios"] = out["territorios"] or c["territorios"]
    imp = t.get("importancia_agente") or t.get("importancia")
    out["importancia_agente"] = int(imp) if str(imp) in "12345" and imp else None
    out["importancia"] = out["importancia_agente"]
    fia = t.get("fiabilidad")
    if fia not in ("primaria", "secundaria", "sin_confirmar"):
        fia = "primaria" if any(x.get("oficial") for x in (t.get("avisos") or []) if isinstance(x, dict)) else "sin_confirmar"
    out["fiabilidad"] = fia
    out["event_date"] = str(_fecha(t.get("event_date")) or "") or None
    out["fecha_limite"] = str(_fecha(t.get("fecha_limite")) or "") or None
    out["no_caduca"] = bool(t.get("no_caduca")) or t.get("kind") in ("analisis", "reportaje", "opinion", "referencia")
    out["solucion"] = t.get("solucion") if t.get("solucion") in SOLUCIONES else None
    out["seccion"] = t.get("seccion") if t.get("seccion") in SECCIONES else None
    out["clave_hecho"] = str(t.get("clave_hecho") or clave_hecho(titulo, out["event_date"]))[:200]
    if perfil:
        out.update(origen="persona", estado="propuesto" if perfil != "superadmin" else "nuevo", propuesto_por=nombre, perfil=perfil, rutina="gestor")
    else:
        out.update(origen="agente", estado="nuevo", rutina=(rutina or t.get("rutina") or "agente")[:40])
    return out


def _sql_lit(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, list) and all(isinstance(x, str) for x in v):
        return ("array[%s]::text[]" % ",".join(_sql_lit(x) for x in v)) if v else "'{}'::text[]"
    if isinstance(v, (list, dict)):
        return _sql_lit(json.dumps(v, ensure_ascii=False)) + "::jsonb"
    return "'" + str(v).replace("'", "''") + "'"


def sql_insertar(filas):
    cols = sorted({k for f in filas for k in f})
    vals = ["(%s)" % ", ".join(_sql_lit(json.dumps(f.get(c) or [], ensure_ascii=False)) + "::jsonb" if c == "avisos" else _sql_lit(f.get(c))
                                for c in cols) for f in filas]
    return "insert into cola_temas (%s) values\n%s\nreturning id, titulo;" % (", ".join(cols), ",\n".join(vals))


def proponer(filas):
    """Inserta temas del agente. Si ya hay un tema abierto con la misma clave de hecho, suma los avisos a ese en vez de
    duplicarlo (así se agrupan los avisos sobre el mismo hecho)."""
    hechas = []
    for f in filas:
        previos = BD.leer("cola_temas", select="id,avisos,estado", clave_hecho="eq." + f["clave_hecho"],
                          estado="in.(%s)" % ",".join(ESTADOS_COLA + ESTADOS_CONFIRMADOS), limit="1")
        if previos:
            p = previos[0]
            urls = {a.get("url") for a in p.get("avisos") or []}
            nuevos = [a for a in f["avisos"] if a.get("url") not in urls or not a.get("url")]
            if nuevos:
                BD.actualizar("cola_temas", {"id": "eq.%s" % p["id"]}, {"avisos": (p.get("avisos") or []) + nuevos,
                                                                       "actualizado_at": datetime.datetime.now(datetime.timezone.utc).isoformat()})
            hechas.append({"id": p["id"], "agrupado": True})
        else:
            r = BD.insertar("cola_temas", f)[0]
            hechas.append({"id": r["id"], "agrupado": False})
    return hechas


# ---------- aprendizaje ----------
def ejemplos(n=20):
    """Las últimas correcciones del editor jefe, en texto, para que el agente las lea antes de proponer importancia."""
    filas = BD.leer("cola_correcciones", select="titulo,etiquetas,de,a,agente,motivo,creado_at", order="creado_at.desc", limit=str(n))
    lineas = []
    for f in filas:
        e = f.get("etiquetas") or {}
        lineas.append("- «%s» (%s · %s · %s): el agente dijo %s; el editor jefe lo dejó en %s.%s" % (
            f["titulo"], e.get("medio") or "?", "+".join(e.get("modos") or []) or "-", "+".join(e.get("territorios") or []) or "-",
            f.get("agente") or f["de"], f["a"], (" Motivo: " + f["motivo"]) if f.get("motivo") else ""))
    return "\n".join(lineas) or "Todavía no hay correcciones del editor jefe."


def aciertos(dias=30):
    desde = (datetime.date.today() - datetime.timedelta(days=dias)).isoformat()
    temas = BD.leer("cola_temas", select="importancia,importancia_agente,medio,temas", importancia_agente="not.is.null",
                    importancia="not.is.null", creado_at="gte." + desde, limit="2000")
    if not temas:
        return {"dias": dias, "temas": 0}
    exactos = sum(1 for t in temas if t["importancia"] == t["importancia_agente"])
    por_medio = {}
    for t in temas:
        m = por_medio.setdefault(t.get("medio") or "?", [0, 0, 0])
        m[0] += 1
        m[1] += t["importancia"] == t["importancia_agente"]
        m[2] += t["importancia"] - t["importancia_agente"]
    return {"dias": dias, "temas": len(temas), "aciertos_pct": round(100.0 * exactos / len(temas), 1),
            "por_medio": {k: {"temas": v[0], "aciertos_pct": round(100.0 * v[1] / v[0], 1), "sesgo": round(v[2] / v[0], 2)} for k, v in por_medio.items()},
            "lectura": "sesgo positivo: el editor jefe sube lo que el agente infravalora; negativo: lo baja"}


def caducar():
    """Pasa al archivo lo caducado (nunca a la papelera). Devuelve cuántos."""
    hoy = hoy_madrid()
    abiertos = BD.leer("cola_temas", select="id,estado,event_date,fecha_limite,no_caduca,creado_at,historial", estado="in.(nuevo,propuesto,sin_fuente)", limit="2000")
    n = 0
    for t in abiertos:
        c = caduca(t)
        if c and c < hoy:
            h = (t.get("historial") or []) + [{"cuando": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="minutes"), "quien": "sistema", "que": "caducado (%s): al archivo" % c}]
            BD.actualizar("cola_temas", {"id": "eq.%s" % t["id"]}, {"estado": "archivado", "estado_antes": t["estado"], "motivo": "caducado el %s" % c, "historial": h})
            n += 1
    return n


def main():
    a = sys.argv[1:] or ["-h"]
    if a[0] in ("-h", "--help"):
        print(__doc__)
        return
    if a[0] in ("proponer", "sql"):
        crudos = json.load(open(a[1], encoding="utf-8"))
        filas = [normalizar(t, rutina=t.get("rutina")) for t in (crudos if isinstance(crudos, list) else [crudos])]
        if a[0] == "sql":
            print(sql_insertar(filas))
            return
        print(json.dumps(proponer(filas), ensure_ascii=False))
        return
    if a[0] == "ejemplos":
        print(ejemplos(int(a[1]) if len(a) > 1 else 20))
        return
    if a[0] == "aciertos":
        print(json.dumps(aciertos(int(a[1]) if len(a) > 1 else 30), ensure_ascii=False, indent=1))
        return
    if a[0] == "caducar":
        print("archivados por caducidad:", caducar())
        return
    sys.exit("acción desconocida: %s" % a[0])


if __name__ == "__main__":
    main()
