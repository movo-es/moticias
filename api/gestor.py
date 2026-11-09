"""MOTICIAS · Gestor (función de Vercel, Python, solo biblioteca estándar): redacción del editor jefe, contenido
patrocinado, publicidad, CRM y equipo.

Sirve la API de app.moticias.com/gestor/ (la página está en app/public/gestor/index.html) y dos lecturas que pide
www.moticias.com con el script del sitio (app/public/sitio/m.js): `yo` (¿es el editor jefe?, con CORS y credenciales) y
`publicidad` (las cajas activas, pública). Lee el contenido que viene con el despliegue (data/, verticals/, src/; Vercel
redespliega en cada push) y, para escribir, usa GitHub como fuente de verdad: lee el fichero fresco, lo cambia y lo guarda
con un commit. Después actualiza el post en Ghost. El equipo y el CRM viven en la base privada (src/bd.py).

Variables de entorno (en Vercel, nunca en el repositorio):
  GESTOR_CLAVE_SUPERADMIN   contraseña común del superadministrador (acceso de emergencia)
  GESTOR_CLAVE_OFICINA      contraseña común del perfil oficina (opcional)
  GITHUB_TOKEN              token de GitHub con permiso de escritura en contenidos de movo-es/moticias
  GHOST_URL, GHOST_ADMIN_KEY  para publicar al momento
  SUPABASE_URL, SUPABASE_ANON_KEY, MOTICIAS_BD_CLAVE  base privada del equipo y del CRM (src/bd.py)
  AI_GATEWAY_API_KEY        opcional: sin ella la IA usa el token OIDC de Vercel; MODELO_IA (por defecto anthropic/claude-opus-5.5)

Retoques del director (data/retoques/, src/retoques.py): encargos con investigación que atiende la rutina /retoques.

Permisos (src/equipo.py): solo el superadministrador (editor jefe) publica —edita, retira y reenfoca piezas, publica cajas,
activa publicidad, cambia productos y equipo—; los demás proponen y trabajan en el CRM. Todo se comprueba aquí, en el
servidor. Reglas: openspec/changes/editor-jefe-y-crm/ y openspec/changes/patrocinios-en-linea/.
"""
import base64, datetime, glob, hashlib, hmac, http.cookies, json, os, re, secrets, sys, time, unicodedata, urllib.error, urllib.parse, urllib.request
from http.server import BaseHTTPRequestHandler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import menciones as M  # noqa: E402
import ghost_publish as G  # noqa: E402
import equipo as EQ  # noqa: E402
import retoques as RT  # noqa: E402  (retoques del director: data/retoques/README.md)
import bd as BD  # noqa: E402
import redaccion as R  # noqa: E402
import firma as F  # noqa: E402
import seguimiento as S  # noqa: E402

REPO = os.environ.get("GITHUB_REPO", "movo-es/moticias")
EQUIPO_REPO = os.environ.get("EQUIPO_REPO", "movo-es/moticias-equipo")  # privado: datos personales del equipo
EQUIPO_FICHERO = "equipo.json"
BRANCH = os.environ.get("GITHUB_BRANCH", "main")
COOKIE = "gestor"
MARCA = "moticias_jefe"  # galleta visible en todo moticias.com: solo dice «hay un editor jefe»; la sesión de verdad es COOKIE
DIAS_SESION = 90
VERTICAL = "movilidad"
ORIGEN_SITIO = os.environ.get("ORIGEN_SITIO", "https://www.moticias.com")

# Campos que el superadministrador puede cambiar en un producto y en un anuncio (lista cerrada).
CAMPOS_PRODUCTO = {"modo", "umbral", "exclusividad", "posicion", "max_por_semana", "status", "url", "one_liner", "contexto", "textos", "excluir"}
CAMPOS_ANUNCIO = {"status", "start", "end", "headline", "text", "cta", "url", "weight", "name", "advertiser", "type", "nivel", "slots",
                  "sections", "image", "crm_cuenta_id", "utm_campaign", "notes"}


# ---------- sesión ----------
def _claves():
    return {"superadmin": os.environ.get("GESTOR_CLAVE_SUPERADMIN") or "", "oficina": os.environ.get("GESTOR_CLAVE_OFICINA") or ""}


def _secreto():
    c = _claves()
    # La firma depende de las contraseñas: cambiar una contraseña cierra todas las sesiones abiertas.
    return hashlib.sha256(("moticias-gestor|" + c["superadmin"] + "|" + c["oficina"]).encode()).digest()


def _firma(msg):
    return hmac.new(_secreto(), msg.encode(), hashlib.sha256).hexdigest()


def firmar(sujeto, dias=DIAS_SESION):
    """sujeto: «superadmin» u «oficina» (acceso con la contraseña común) o «p-<id>-<versión>» (persona del equipo)."""
    msg = "%s.%d" % (sujeto, int(time.time()) + dias * 86400)
    return msg + "." + _firma(msg)


def sesion_de(valor):
    """Devuelve {perfil, nombre, id, permisos} o None. Una persona suspendida, o cuya versión cambió (perfil cambiado,
    enlace nuevo), pierde la sesión en el acto."""
    try:
        sujeto, exp, sig = (valor or "").split(".")
    except ValueError:
        return None
    if not hmac.compare_digest(sig, _firma("%s.%s" % (sujeto, exp))) or int(exp) <= time.time():
        return None
    if sujeto in ("superadmin", "oficina"):
        return {"perfil": sujeto, "nombre": "Acceso común (%s)" % sujeto, "id": None, "permisos": EQ.PERFILES[sujeto]["permisos"]}
    if sujeto.startswith("p-"):
        try:
            _, pid, ver = sujeto.split("-")
        except ValueError:
            return None
        datos, _ = equipo()
        per = EQ.buscar(datos, pid=pid)
        if per and per.get("estado") == "activa" and str(per.get("version") or 0) == ver and per.get("perfil") in EQ.PERFILES:
            return {"perfil": per["perfil"], "nombre": per.get("nombre"), "id": pid, "permisos": EQ.PERFILES[per["perfil"]]["permisos"]}
    return None


def cookie_sesion(sujeto):
    return "%s=%s; Path=/; Max-Age=%d; HttpOnly; Secure; SameSite=Lax" % (COOKIE, firmar(sujeto), DIAS_SESION * 86400)


def cookie_marca(encendida, host):
    """Galleta para todo moticias.com que hace que el script del sitio pregunte si quien mira es el editor jefe. No da
    ningún permiso: si alguien la pone a mano, el gestor le contesta que no es nadie. Sin ella, el sitio no pregunta."""
    dom = "; Domain=moticias.com" if (host or "").endswith("moticias.com") else ""
    if encendida:
        return "%s=1; Path=/%s; Max-Age=%d; Secure; SameSite=Lax" % (MARCA, dom, DIAS_SESION * 86400)
    return "%s=; Path=/%s; Max-Age=0; Secure; SameSite=Lax" % (MARCA, dom)


# ---------- datos ----------
def vertical():
    return json.load(open(os.path.join(ROOT, "verticals", VERTICAL + ".json"), encoding="utf-8"))


def productos():
    return M.cargar_productos(os.path.join(ROOT, "data"))


def gh(method, path, body=None, repo=None):
    tok = os.environ.get("GITHUB_TOKEN")
    if not tok:
        return 0, {"message": "falta GITHUB_TOKEN"}
    req = urllib.request.Request(("https://api.github.com/repos/%s/%s" % (repo or REPO, path)).rstrip("/"), method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": "Bearer " + tok, "Accept": "application/vnd.github+json", "Content-Type": "application/json",
                                          "User-Agent": "moticias-gestor", "X-GitHub-Api-Version": "2022-11-28"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")
    except urllib.error.URLError as e:
        return 0, {"message": str(e)}


def leer(ruta, repo=None):
    """Devuelve (objeto, sha). Primero GitHub (fresco); si no hay token, el fichero del despliegue (sha None)."""
    st, r = gh("GET", "contents/%s" % urllib.parse.quote(ruta) + ("" if repo else "?ref=%s" % BRANCH), repo=repo)
    if st == 200:
        return json.loads(base64.b64decode(r["content"]).decode("utf-8")), r["sha"]
    if repo:
        return None, None
    p = os.path.join(ROOT, ruta)
    if os.path.exists(p):
        return json.load(open(p, encoding="utf-8")), None
    return None, None


def escribir(ruta, obj, sha, mensaje, repo=None):
    txt = json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    body = {"message": mensaje + "\n\nGestor de patrocinios (app.moticias.com/gestor/)", "content": base64.b64encode(txt.encode("utf-8")).decode()}
    if not repo:
        body["branch"] = BRANCH
    if sha:
        body["sha"] = sha
    st, r = gh("PUT", "contents/%s" % urllib.parse.quote(ruta), body, repo=repo)
    if st in (200, 201):
        return True, (r.get("commit") or {}).get("sha", "")[:7]
    if st == 409:
        return False, "el fichero cambió mientras tanto; vuelve a abrir la pieza"
    return False, r.get("message") or "error de GitHub (%s)" % st


def republicar(a, v):
    url, key = os.environ.get("GHOST_URL"), os.environ.get("GHOST_ADMIN_KEY")
    if not url or not key or ":" not in key:
        return False, "sin clave de Ghost en el gestor: la pieza se actualizará en la próxima publicación"
    try:
        res, err = G.republicar(a, v, url.rstrip("/"), key)
    except Exception as e:  # noqa: BLE001  (un fallo de Ghost no debe perder el cambio ya guardado)
        return False, "Ghost: %s" % e
    if err:
        return False, err if isinstance(err, str) else "Ghost: %s" % json.dumps(err, ensure_ascii=False)[:200]
    return True, res.get("url") or "actualizada en Ghost"


def resumen_pieza(a, prods):
    return {"id": a["id"], "title": a.get("title"), "date": a.get("date"), "section": a.get("section"), "kind": a.get("kind"),
            "status": a.get("status"), "author": a.get("author"), "menciones": a.get("menciones") or [],
            "candidatos": [c for c in M.candidatos(a, prods) if c["puntuacion"] is not None][:4]}


def piezas(dias):
    prods = productos()
    lim = (datetime.date.today() - datetime.timedelta(days=dias)).isoformat()
    out = []
    for p in glob.glob(os.path.join(ROOT, "data", "articles", "*.json")):
        a = json.load(open(p, encoding="utf-8"))
        if (a.get("date") or "") < lim and not any(m.get("estado") == "propuesta" for m in a.get("menciones") or []):
            continue
        out.append(resumen_pieza(a, prods))
    out.sort(key=lambda r: (r["date"] or "", r["title"] or ""), reverse=True)
    return out


def detalle(pid):
    a, _ = leer("data/articles/%s.json" % pid)
    if not a:
        return None
    v, prods = vertical(), productos()
    r = resumen_pieza(a, prods)
    r["candidatos"] = M.candidatos(a, prods)
    r["summary"] = a.get("summary")
    r["vista"] = M.insertar_en_medio(G.md_to_html(a.get("body_md", "")), M.cajas_html(a, v, G.inline))
    r["url"] = "https://%s/%s/" % (v.get("domain", "www.moticias.com"), a["id"])
    r["retoques"] = retoques_de(pid)
    return r


# ---------- retoques del director ----------
def retoques_de(pid=None):
    """Retoques (frescos de GitHub si hay token; si no, los del despliegue), los más recientes primero."""
    out = []
    st, lista = gh("GET", "contents/data/retoques?ref=%s" % BRANCH)
    if st == 200 and isinstance(lista, list):
        for f in lista:
            if not f.get("name", "").endswith(".json"):
                continue
            if pid and ("-%s-" % pid[:40].rstrip("-")) not in f["name"]:
                continue
            r, _ = leer("data/retoques/" + f["name"])
            if r and (not pid or r.get("pieza") == pid):
                out.append(r)
    else:
        out = [r for r in RT.cargar_todos() if not pid or r.get("pieza") == pid]
    out.sort(key=lambda r: r.get("pedido_en") or "", reverse=True)
    return out


def accion_retoque(ses, d):
    acc, pid = d.get("accion") or "crear", d.get("id")
    if acc == "crear":
        try:
            r = RT.construir(str(d.get("pieza") or ""), str(d.get("instruccion") or ""), ses["perfil"])
        except ValueError as e:
            return 400, {"error": str(e)}
        ok, det = escribir("data/retoques/%s.json" % r["id"], r, None, "Retoque pedido: %s" % r["pieza"])
        if not ok:
            return 502, {"error": det}
        return 200, {"ok": True, "commit": det, "retoque": r, "aviso": "La redacción lo atiende en menos de una hora y te avisa al publicarlo."}
    if acc == "cancelar":
        ruta = "data/retoques/%s.json" % re.sub(r"[^a-z0-9-]", "", str(pid or ""))
        r, sha = leer(ruta)
        if not r:
            return 404, {"error": "retoque no encontrado"}
        if r.get("estado") != "pendiente":
            return 400, {"error": "solo se cancela un retoque pendiente"}
        r["estado"] = "cancelado"
        r["resultado"] = {"en": RT.ahora(), "resumen": "cancelado desde el gestor", "fuentes": [], "cambios": []}
        ok, det = escribir(ruta, r, sha, "Retoque cancelado: %s" % r["pieza"])
        return (200, {"ok": True, "commit": det, "retoque": r}) if ok else (502, {"error": det})
    return 400, {"error": "acción desconocida"}


def accion_mencion(rol, d, publica=True):
    """`publica`: solo el editor jefe. Los demás perfiles proponen: añadir una caja la deja «pendiente» y solo pueden
    retocar el texto de una caja pendiente. Nada de lo que hacen se ve en la web hasta que él publica."""
    pid, prod_id, acc = d.get("id"), d.get("producto"), d.get("accion")
    if acc not in ("publicar", "retirar", "proponer", "editar", "anadir", "posicion"):
        return 400, {"error": "acción desconocida"}
    if not publica and acc not in ("anadir", "editar"):
        return 403, {"error": "solo el editor jefe publica, retira o mueve cajas; tú puedes proponerlas"}
    ruta = "data/articles/%s.json" % pid
    a, sha = leer(ruta)
    if not a:
        return 404, {"error": "pieza no encontrada"}
    if sha is None:
        return 503, {"error": "el gestor no puede escribir: falta GITHUB_TOKEN en Vercel"}
    v = vertical()
    ms = a.setdefault("menciones", [])
    ahora = datetime.datetime.now().astimezone().isoformat(timespec="minutes")
    m = next((x for x in ms if x.get("producto") == prod_id), None)
    if acc == "anadir" and d.get("posicion") not in (None, *M.POSICIONES):
        return 400, {"error": "posición no válida"}
    if acc == "anadir":
        if a.get("kind") == "analisis":
            return 400, {"error": "los análisis del director no llevan contenido patrocinado"}
        prod = next((p for p in productos() if p.get("id") == prod_id), None)
        if not prod or not prod.get("url"):
            return 400, {"error": "producto sin url o inexistente"}
        if m and m.get("estado") != "retirada":
            return 400, {"error": "esa pieza ya tiene ese producto"}
        nuevo = "publicada" if publica else "propuesta"
        if m:  # estaba retirada: se reactiva (nunca se borra; queda en el historial)
            m["estado"] = nuevo
        else:
            pts, motivos = M.puntuar(a, prod)
            m = M.nueva_mencion(a, prod, pts or 0, ["%s a mano por %s" % ("añadida" if publica else "propuesta", rol)] + (motivos if isinstance(motivos, list) else [motivos]), nuevo, origen="manual")
            ms.append(m)
        if d.get("posicion") in M.POSICIONES:
            m["posicion"] = d["posicion"]
    else:
        if not m:
            return 404, {"error": "esa pieza no tiene mención de ese producto"}
        if acc == "publicar":
            m["estado"] = "publicada"
        elif acc == "retirar":
            m["estado"] = "retirada"
        elif acc == "proponer":
            m["estado"] = "propuesta"
        elif acc == "editar":
            if not publica and m.get("estado") != "propuesta":
                return 403, {"error": "solo el editor jefe cambia una caja que ya está en la web o retirada"}
            for k in ("texto", "cta"):
                if isinstance(d.get(k), str) and d[k].strip():
                    m[k] = d[k].strip()[:600]
            if d.get("posicion") in M.POSICIONES and publica:
                m["posicion"] = d["posicion"]
        elif acc == "posicion":
            if d.get("posicion") not in M.POSICIONES:
                return 400, {"error": "posición no válida"}
            m["posicion"] = d["posicion"]
    m.setdefault("historial", []).append({"en": ahora, "por": rol, "accion": acc})
    pub = [x for x in ms if x.get("estado") == "publicada"]
    maxp = int((v.get("productos") or {}).get("max_por_pieza") or 2)
    if acc in ("publicar", "anadir") and (len(pub) > maxp or (len(pub) > 1 and any(x.get("exclusividad") == "exclusiva" for x in pub))):
        return 400, {"error": "no cabe: la pieza ya tiene %d caja(s) y una de ellas es exclusiva o se supera el máximo (%d). Retira otra antes." % (len(pub) - 1, maxp)}
    # Cada cambio se sube a la web en el acto (también en productos propios: la pieza se actualiza en Ghost y su fecha de
    # modificación y el sitemap se refrescan); si Ghost responde bien, la mención queda marcada «en la web».
    m.pop("en_web", None)
    if not publica:  # una propuesta no cambia nada de lo que se ve: no se sube a Ghost
        ok, det = escribir(ruta, a, sha, "Patrocinio: %s propone %s en %s" % (rol, prod_id, pid))
        if not ok:
            return 502, {"error": det}
        BD.registrar(rol, "proponer_caja", pid, {"producto": prod_id, "accion": acc})
        r = resumen_pieza(a, productos())
        r["vista"] = M.insertar_en_medio(G.md_to_html(a.get("body_md", "")), M.cajas_html(a, v, G.inline))
        r["candidatos"] = M.candidatos(a, productos())
        return 200, {"ok": True, "commit": det, "ghost": {"ok": True, "detalle": "propuesta: la publica el editor jefe"}, "pieza": r}
    rep_ok, rep = republicar(a, v)
    if rep_ok:
        G.marcar_en_web(a)
    ok, det = escribir(ruta, a, sha, "Patrocinio: %s %s en %s" % (acc, prod_id, pid))
    if not ok:
        return 502, {"error": det}
    r = resumen_pieza(a, productos())
    r["vista"] = M.insertar_en_medio(G.md_to_html(a.get("body_md", "")), M.cajas_html(a, v, G.inline))
    r["candidatos"] = M.candidatos(a, productos())
    return 200, {"ok": True, "commit": det, "ghost": {"ok": rep_ok, "detalle": rep}, "pieza": r}


def pendiente_web(p):
    return any(m.get("estado") == "publicada" and not m.get("en_web") for m in p.get("menciones") or [])


def republicar_y_marcar(pid):
    ruta = "data/articles/%s.json" % pid
    a, sha = leer(ruta)
    if not a:
        return {"ok": False, "detalle": "pieza no encontrada"}
    ok, det = republicar(a, vertical())
    if ok and G.marcar_en_web(a) and sha:
        escribir(ruta, a, sha, "Patrocinio: %s en la web" % pid)
    return {"ok": ok, "detalle": det}


def accion_producto(d):
    pid = d.get("id")
    ruta = "data/productos/%s.json" % pid
    p, sha = leer(ruta)
    if not p:
        return 404, {"error": "producto no encontrado"}
    if sha is None:
        return 503, {"error": "falta GITHUB_TOKEN en Vercel"}
    cambios = {k: val for k, val in (d.get("cambios") or {}).items() if k in CAMPOS_PRODUCTO}
    if "modo" in cambios and cambios["modo"] not in M.MODOS:
        return 400, {"error": "modo no válido"}
    if "posicion" in cambios and cambios["posicion"] not in M.POSICIONES:
        return 400, {"error": "posición no válida"}
    if "exclusividad" in cambios and cambios["exclusividad"] not in ("exclusiva", "compartida"):
        return 400, {"error": "exclusividad no válida"}
    for k in ("umbral", "max_por_semana"):
        if k in cambios:
            try:
                cambios[k] = max(0, min(200, int(cambios[k])))
            except (TypeError, ValueError):
                return 400, {"error": "%s debe ser un número" % k}
    if "textos" in cambios:
        cambios["textos"] = {**(p.get("textos") or {}), **{k: str(x)[:600] for k, x in (cambios["textos"] or {}).items() if k in ("corto", "cta")}}
    if cambios.get("modo") in ("automatico", "revision", "manual") and p.get("status") != "activo" and "status" not in cambios:
        cambios["status"] = "activo"
    p.update(cambios)
    p["updated_at"] = datetime.datetime.now().astimezone().isoformat(timespec="minutes")
    ok, det = escribir(ruta, p, sha, "Producto %s: %s" % (pid, ", ".join(sorted(cambios)) or "sin cambios"))
    return (200, {"ok": True, "commit": det, "producto": p}) if ok else (502, {"error": det})


def anuncios():
    out = []
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "ads", "*.json"))):
        a = json.load(open(f, encoding="utf-8"))
        out.append({k: a.get(k) for k in ("id", "name", "advertiser", "type", "label", "status", "start", "end", "slots", "sections", "headline",
                                          "text", "cta", "url", "weight", "nivel", "image", "crm_cuenta_id", "utm_campaign", "updated_at", "propuesto_por")})
    return out


def _slug(t, n=48):
    t = unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")[:n].strip("-") or "anuncio"


def _hoy():
    return datetime.date.today().isoformat()


def publicidad_publica():
    """Cajas activas hoy, por hueco, para el script del sitio. Solo creatividad pública: ni importes ni contactos."""
    v = vertical()
    pub = v.get("publicidad") or {}
    huecos = set((pub.get("huecos") or {}).keys())
    tipos = pub.get("tipos") or {}
    hoy, out = _hoy(), {}
    for a in anuncios():
        if a.get("status") != "activo" or not a.get("url") or not str(a.get("url")).startswith("https://"):
            continue
        if (a.get("start") and a["start"] > hoy) or (a.get("end") and a["end"] < hoy):
            continue
        caja = {"id": a["id"], "tipo": a.get("type") or "publicidad", "etiqueta": a.get("label") or tipos.get(a.get("type"), "Publicidad"),
                "anunciante": a.get("advertiser") or "", "titular": a.get("headline") or "", "texto": a.get("text") or "", "cta": a.get("cta") or "",
                "url": a["url"], "nivel": a.get("nivel") or "estandar", "peso": int(a.get("weight") or 1), "imagen": a.get("image") or None,
                "secciones": a.get("sections") or [], "campana": a.get("utm_campaign") or a["id"]}
        for h in a.get("slots") or []:
            if h in huecos:
                out.setdefault(h, []).append(caja)
    orden = {"premium": 0, "estandar": 1, "basico": 2}
    for h in out:  # lo pagado delante de la autopromoción; después por nivel y peso
        out[h].sort(key=lambda c: (c["tipo"] == "autopromocion", orden.get(c["nivel"], 3), -c["peso"]))
    return {"huecos": out, "generado": datetime.datetime.now().astimezone().isoformat(timespec="minutes")}


def accion_anuncio(ses, d):
    """Crear o cambiar una caja de publicidad o patrocinio. Solo el editor jefe la activa o toca una que está en la web;
    los demás la crean o la retocan como «propuesta»."""
    jefe = "publicidad" in ses["permisos"]
    v = vertical()
    pub = v.get("publicidad") or {}
    cambios = {k: val for k, val in (d.get("cambios") or {}).items() if k in CAMPOS_ANUNCIO}
    if "status" in cambios and cambios["status"] not in (pub.get("estados") or ["propuesta", "activo", "pausado", "terminado"]):
        return 400, {"error": "estado no válido"}
    if "nivel" in cambios and cambios["nivel"] not in (pub.get("niveles") or {}):
        return 400, {"error": "nivel no válido"}
    if "type" in cambios and cambios["type"] not in (pub.get("tipos") or {}):
        return 400, {"error": "tipo no válido"}
    if "slots" in cambios:
        if not isinstance(cambios["slots"], list) or not set(cambios["slots"]) <= set((pub.get("huecos") or {}).keys()):
            return 400, {"error": "hueco no válido"}
    if cambios.get("url") and not str(cambios["url"]).startswith("https://"):
        return 400, {"error": "el enlace tiene que empezar por https://"}
    for k in ("start", "end"):
        if cambios.get(k) and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(cambios[k])):
            return 400, {"error": "fecha no válida (%s)" % k}
    for k, n in (("headline", 140), ("text", 400), ("cta", 60), ("name", 120), ("advertiser", 120), ("notes", 1000), ("utm_campaign", 60)):
        if k in cambios:
            cambios[k] = str(cambios[k] or "").strip()[:n]
    if "weight" in cambios:
        try:
            cambios["weight"] = max(1, min(10, int(cambios["weight"])))
        except (TypeError, ValueError):
            return 400, {"error": "el peso es un número del 1 al 10"}
    if not jefe:
        if cambios.get("status") not in (None, "propuesta"):
            return 403, {"error": "solo el editor jefe activa, pausa o termina publicidad; tú la dejas propuesta"}
        cambios["status"] = "propuesta"
    nuevo = d.get("accion") == "crear"
    if nuevo:
        if not cambios.get("name") or not cambios.get("headline"):
            return 400, {"error": "faltan el nombre interno y el titular"}
        aid = "%s-%s" % (_slug(cambios.get("advertiser") or cambios["name"], 40), secrets.token_hex(2))
        a, sha = {"id": aid, "created_at": datetime.datetime.now().astimezone().isoformat(timespec="minutes"), "utm": True,
                  "label": (pub.get("tipos") or {}).get(cambios.get("type") or "publicidad", "Publicidad"), "status": "propuesta",
                  "type": "publicidad", "nivel": "estandar", "slots": [], "sections": [], "weight": 1}, None
        if not jefe:
            a["propuesto_por"] = ses["nombre"]
    else:
        a, sha = leer("data/ads/%s.json" % d.get("id"))
        if not a:
            return 404, {"error": "anuncio no encontrado"}
        if sha is None:
            return 503, {"error": "falta GITHUB_TOKEN en Vercel"}
        if not jefe and a.get("status") != "propuesta":
            return 403, {"error": "esta caja ya la ha aprobado el editor jefe: solo él la cambia"}
    if "type" in cambios:
        a["label"] = (pub.get("tipos") or {}).get(cambios["type"], a.get("label"))
    if cambios.get("status") and cambios["status"] != a.get("status"):  # fechas de publicación y retirada para el seguimiento
        a.setdefault("historial", []).append({"en": datetime.datetime.now().astimezone().isoformat(timespec="minutes"), "estado": cambios["status"],
                                              "por": ses["perfil"]})
    a.update(cambios)
    if a.get("status") == "activo" and (not a.get("url") or not a.get("slots") or not a.get("headline")):
        return 400, {"error": "para activarla necesita titular, enlace https:// y al menos un hueco"}
    a["updated_at"] = datetime.datetime.now().astimezone().isoformat(timespec="minutes")
    for k in ("amount_eur", "contact", "invoice_ref"):  # lo comercial va al CRM (privado), no al repositorio público
        a.pop(k, None)
    ok, det = escribir("data/ads/%s.json" % a["id"], a, sha, "Publicidad %s: %s" % (a["id"], "alta" if nuevo else ", ".join(sorted(cambios))))
    if not ok:
        return 502, {"error": det}
    BD.registrar(ses["nombre"], "publicidad_" + ("crear" if nuevo else "cambiar"), a["id"], {"cambios": sorted(cambios)})
    return 200, {"ok": True, "commit": det, "anuncio": a,
                 "nota": "En la web en un par de minutos (lo que tarda Vercel en desplegar)." if a.get("status") == "activo" else "Guardada como %s." % a.get("status")}


# ---------- equipo (base privada; si no está configurada, repositorio privado) ----------
_CACHE = {"t": 0, "datos": None, "sha": None}


def equipo(fresco=False):
    """(datos, sha) del equipo con 60 s de caché por instancia. Con la base configurada, sha es «bd»."""
    if fresco or not _CACHE["datos"] or time.time() - _CACHE["t"] > 60:
        if BD.configurada():
            try:
                filas = BD.leer("equipo", select="datos", order="actualizado.asc")
                _CACHE.update(t=time.time(), datos={"personas": [f["datos"] for f in filas]}, sha="bd")
            except BD.ErrorBD:
                _CACHE.update(t=time.time(), datos=EQ.vacio(), sha=None)
        else:
            datos, sha = leer(EQUIPO_FICHERO, repo=EQUIPO_REPO)
            _CACHE.update(t=time.time(), datos=datos or EQ.vacio(), sha=sha)
    return _CACHE["datos"], _CACHE["sha"]


def guardar_equipo(datos, sha, mensaje, pid=None):
    datos["actualizado"] = EQ.ahora()
    _CACHE.update(t=0, datos=None)
    if sha == "bd" or (sha is None and BD.configurada()):
        filas = [{"id": p["id"], "email": EQ.normal(p["email"]), "datos": p, "actualizado": datetime.datetime.now().astimezone().isoformat()}
                 for p in datos.get("personas", []) if not pid or p["id"] == pid]
        try:
            BD.upsert("equipo", filas)
            return True, "bd"
        except BD.ErrorBD as e:
            return False, str(e)
    return escribir(EQUIPO_FICHERO, datos, sha, mensaje, repo=EQUIPO_REPO)


def accion_equipo(ses, d, base):
    datos, sha = equipo(fresco=True)
    acc = d.get("accion")
    try:
        if acc == "invitar":
            p, token = EQ.invitar(datos, d.get("nombre"), d.get("email"), d.get("perfil"), ses["nombre"])
        else:
            p, token = EQ.cambiar(datos, d.get("id"), acc, ses["nombre"], d.get("perfil"))
            if p.get("id") == ses.get("id") and acc in ("suspender", "perfil") and d.get("perfil") != "superadmin":
                return 400, {"error": "no puedes quitarte a ti mismo el perfil de superadministrador ni suspenderte"}
    except ValueError as e:
        return 400, {"error": str(e)}
    ok, det = guardar_equipo(datos, sha, "Equipo: %s %s" % (acc, p["id"]), pid=p["id"])
    BD.registrar(ses["nombre"], "equipo_" + acc, p["id"], {"perfil": p.get("perfil")})
    if not ok:
        return 502, {"error": det}
    r = {"ok": True, "persona": EQ.publica(p)}
    if token:
        r["enlace"] = base + "/gestor/?invitacion=" + urllib.parse.quote(token)
    return 200, r


def suscriptores():
    """Resumen de los suscriptores de Ghost (Members): totales por tipo y las últimas altas. Se gestionan en Ghost."""
    url, key = os.environ.get("GHOST_URL"), os.environ.get("GHOST_ADMIN_KEY")
    if not url or not key or ":" not in key:
        return {"error": "sin clave de Ghost"}
    base, tok = G.admin_base(url.rstrip("/")), G.ghost_token(key)
    out = {"ghost_members": base + "/ghost/#/members", "ghost_staff": base + "/ghost/#/settings/staff"}
    for k, f in (("total", ""), ("gratuitos", "&filter=status:free"), ("pago", "&filter=status:paid"), ("cortesia", "&filter=status:comped")):
        st, r = G.api("GET", base + "/ghost/api/admin/members/?limit=1&fields=id" + f, tok)
        out[k] = ((r.get("meta") or {}).get("pagination") or {}).get("total") if st == 200 else None
    st, r = G.api("GET", base + "/ghost/api/admin/members/?limit=8&order=created_at%20desc&fields=name,email,status,created_at", tok)
    out["ultimos"] = [{"nombre": m.get("name") or "", "email": m.get("email"), "estado": m.get("status"), "alta": (m.get("created_at") or "")[:10]}
                      for m in (r.get("members") or [])] if st == 200 else []
    return out


# ---------- redacción del editor jefe ----------
def _ruta_pieza(pid):
    if not re.fullmatch(r"[a-z0-9-]{3,120}", pid or ""):
        return None
    return "data/articles/%s.json" % pid


def _url_pieza(a, v):
    return "https://%s/%s/" % (v.get("domain", "www.moticias.com"), a["id"])


def ficha_redaccion(pid):
    ruta = _ruta_pieza(pid)
    a, _ = leer(ruta) if ruta else (None, None)
    if not a:
        return None
    v = vertical()
    c = F.config(v)
    arts = F.cargar(ROOT)
    arts[a["id"]] = a
    dec = F.decidir(a, arts, c)
    imp, mot = F.importante(a, c)
    return {"id": a["id"], "campos": {k: a.get(k) or "" for k in R.CAMPOS}, "nombres": R.NOMBRES, "status": a.get("status") or "publicado",
            "kind": a.get("kind"), "date": a.get("date"), "author": a.get("author"), "section": a.get("section"), "url": _url_pieza(a, v),
            "revised_at": a.get("revised_at"), "revisiones": (a.get("revisiones") or [])[-8:], "correcciones": a.get("correcciones") or [],
            "fuentes": [{"medio": x.get("outlet"), "titulo": x.get("title"), "url": x.get("url")} for x in a.get("sources") or []],
            "enfoques": {k: t.split(":")[0] for k, t in R.ENFOQUES.items()},
            "firma": {"actual": "director" if F.es_del_director(a, c) else "redaccion", "director": c["director"], "redaccion": c["redaccion"],
                      "importante": imp, "motivo": mot, "propuesta": dec["firma"], "cupo": dec["cupo"]}}


def _aplicar_firma(a, quiere, v):
    """Firma pedida por el editor jefe para esta pieza. El tope del 10 % no se salta ni a mano."""
    c = F.config(v)
    if quiere == "director":
        q = F.cupo(F.cargar(ROOT), a.get("date") or _hoy(), c, excluir=a["id"])
        if not F.es_del_director(a, c) and q["libres_max"] <= 0:
            raise ValueError("tu firma ya está en el %s %% de las piezas de los últimos %s días (tope %s %%): firma la redacción" % (q["pct"], c["ventana_dias"], c["max_pct"]))
        a["firma_director"] = True
        a["author"], a["author_role"] = c["director"], c["director_role"]
        if a.get("author_note"):
            a["author_note"] = (v.get("editor") or {}).get("interests_note") or a["author_note"]
    elif quiere == "redaccion":
        a["firma_director"] = False
        a["author"], a["author_role"] = c["redaccion"], c["redaccion_role"]
        if a.get("author_note"):
            a["author_note"] = (v.get("editorial") or {}).get("interests_note_redaccion") or F.NOTA_REDACCION


def _subir(a, v, estado=None):
    url, key = os.environ.get("GHOST_URL"), os.environ.get("GHOST_ADMIN_KEY")
    if not url or not key or ":" not in key:
        return False, "sin clave de Ghost en el gestor: se verá en la próxima publicación"
    try:
        res, err = (G.publicar_con_estado(a, v, url.rstrip("/"), key, estado) if estado else G.republicar(a, v, url.rstrip("/"), key))
    except Exception as e:  # noqa: BLE001
        return False, "Ghost: %s" % e
    if err:
        return False, err if isinstance(err, str) else "Ghost: %s" % json.dumps(err, ensure_ascii=False)[:200]
    return True, res.get("url") or "actualizada en Ghost"


def accion_redaccion(ses, d, cabeceras):
    acc, pid = d.get("accion"), d.get("id")
    ruta = _ruta_pieza(pid)
    if not ruta:
        return 400, {"error": "pieza no válida"}
    a, sha = leer(ruta)
    if not a:
        return 404, {"error": "pieza no encontrada"}
    v, quien = vertical(), ses["nombre"]
    if acc == "enfoque":
        try:
            r = R.otro_enfoque(a, d.get("enfoque") or "", d.get("instruccion") or "", cabeceras)
        except (RuntimeError, ValueError) as e:
            return 502, {"error": str(e)}
        BD.registrar(quien, "ia_enfoque", pid, {"enfoque": d.get("enfoque"), "modelo": r["modelo"], "cifras_nuevas": r["cifras_nuevas"]})
        return 200, dict(r, original={k: a.get(k) or "" for k in R.CAMPOS})
    if sha is None:
        return 503, {"error": "el gestor no puede escribir: falta GITHUB_TOKEN en Vercel"}
    estado = None
    try:
        if acc == "editar":
            cambios = R.limpiar(d.get("cambios") or {})
            nuevas = R.cifras_nuevas(a, dict({k: a.get(k) or "" for k in R.CAMPOS}, **cambios))
            if nuevas and not d.get("confirmo_cifras"):
                return 409, {"error": "hay cifras o fechas que no están en la pieza ni en sus fuentes", "cifras": nuevas}
            hechos = R.aplicar_edicion(a, cambios, quien, origen=d.get("origen") or "manual", correccion=d.get("correccion"))
            if d.get("firma") in ("director", "redaccion"):
                antes = a.get("author")
                _aplicar_firma(a, d["firma"], v)
                if a.get("author") != antes:
                    hechos.append("firma")
            if not hechos:
                return 400, {"error": "no hay cambios"}
            mensaje = "Redacción: %s edita %s (%s)" % (quien, pid, ", ".join(hechos))
        elif acc == "retirar":
            R.retirar(a, quien, d.get("motivo"))
            estado, mensaje = "draft", "Redacción: %s retira %s" % (quien, pid)
        elif acc == "restaurar":
            R.restaurar(a, quien)
            estado = "draft" if a.get("status") in ("pendiente", "borrador") else "published"
            mensaje = "Redacción: %s restaura %s" % (quien, pid)
        elif acc == "publicar":  # el visto bueno del director a una pieza pendiente
            if a.get("status") not in ("pendiente", "borrador"):
                return 400, {"error": "la pieza no está pendiente"}
            a["status"] = "publicado"
            a.setdefault("revisiones", []).append({"en": R.ahora(), "por": quien, "accion": "aprobar y publicar"})
            estado, mensaje = "published", "Redacción: %s aprueba y publica %s" % (quien, pid)
        else:
            return 400, {"error": "acción desconocida"}
    except ValueError as e:
        return 400, {"error": str(e)}
    ok, det = escribir(ruta, a, sha, mensaje)
    if not ok:
        return 502, {"error": det}
    g_ok, g = _subir(a, v, estado)
    BD.registrar(quien, "redaccion_" + acc, pid, {"commit": det, "ghost": g_ok})
    return 200, {"ok": True, "commit": det, "ghost": {"ok": g_ok, "detalle": g}, "pieza": ficha_redaccion(pid)}


def informe_firma():
    v = vertical()
    c = F.config(v)
    arts = F.cargar(ROOT)
    q = F.cupo(arts, _hoy(), c)
    suyas = sorted([{"id": a["id"], "title": a.get("title"), "date": a.get("date"), "status": a.get("status")} for a in arts.values()
                    if F.es_del_director(a, c) and q["desde"] <= (a.get("date") or "") <= q["hasta"]], key=lambda x: x["date"], reverse=True)
    return {"cupo": q, "piezas": suyas, "regla": ((v.get("editorial") or {}).get("firma_director") or {}).get("regla")}


# ---------- CRM (base privada; módulo de MOVO) ----------
CAMPOS_CUENTA = ("tipo", "subtipo", "nombre", "razon_social", "cif", "sector", "comunidad", "provincia", "municipio", "web", "dominio",
                 "origen", "senal", "responsable", "etiquetas", "notas")
CAMPOS_PERSONA = ("cuenta_id", "nombre", "cargo", "perfil", "correo", "telefono", "linkedin", "ghost_member_id", "verificado", "notas")
CAMPOS_CONTRATO = ("anuncio_id", "concepto", "nivel", "importe_cent", "desde", "hasta", "estado", "notas")


def crm_cfg():
    return vertical().get("crm") or {}


def _dominio(web):
    h = urllib.parse.urlparse(web if "://" in (web or "") else "https://" + (web or "")).hostname or ""
    return h[4:] if h.startswith("www.") else (h or None)


def _limpio(d, campos):
    out = {}
    for k in campos:
        if k in d:
            x = d[k]
            if isinstance(x, str):
                x = x.strip() or None
            out[k] = x
    return out


def crm_cuentas(q):
    p = {"select": "id,tipo,subtipo,nombre,web,comunidad,provincia,estado,estado_at,paso_que,paso_fecha,personas,ultima_actividad,responsable,etiquetas",
         "producto": "eq.moticias", "archivada_at": "is.null", "order": "paso_fecha.asc.nullslast,nombre.asc", "limit": "300"}
    if q.get("tipo"):
        p["tipo"] = "eq." + q["tipo"]
    if q.get("estado"):
        p["estado"] = "eq." + q["estado"]
    if q.get("q"):
        t = re.sub(r"[^\w .@-]", "", q["q"])[:60]
        p["or"] = "(nombre.ilike.*%s*,dominio.ilike.*%s*,razon_social.ilike.*%s*)" % (t, t, t)
    return BD.leer("crm_cuentas_hoy", **p)


def crm_resumen():
    filas = BD.leer("crm_cuentas_hoy", select="tipo,estado,paso_fecha", producto="eq.moticias", archivada_at="is.null", limit="5000")
    hoy, por = _hoy(), {}
    for f in filas:
        t = por.setdefault(f["tipo"], {"total": 0, "estados": {}})
        t["total"] += 1
        t["estados"][f.get("estado") or "—"] = t["estados"].get(f.get("estado") or "—", 0) + 1
    pasos = BD.leer("crm_pasos", select="id,cuenta_id,que,fecha,responsable,crm_cuentas(nombre,tipo)", hecho_at="is.null",
                    fecha="lte." + (datetime.date.today() + datetime.timedelta(days=7)).isoformat(), order="fecha.asc", limit="100")
    return {"tipos": por, "pasos": pasos, "hoy": hoy}


def crm_ficha(cid, permisos):
    if not re.fullmatch(r"[0-9a-f-]{36}", cid or ""):
        return None
    c = BD.leer("crm_cuentas_hoy", select="*", id="eq." + cid)
    if not c:
        return None
    r = {"cuenta": c[0],
         "personas": BD.leer("crm_personas", select="*", cuenta_id="eq." + cid, archivada_at="is.null", order="creada_at.asc"),
         "estados": BD.leer("crm_estados", select="*", cuenta_id="eq." + cid, order="id.desc", limit="30"),
         "actividades": BD.leer("crm_actividades", select="*", cuenta_id="eq." + cid, order="at.desc", limit="60"),
         "pasos": BD.leer("crm_pasos", select="*", cuenta_id="eq." + cid, order="hecho_at.desc.nullsfirst,fecha.asc", limit="40")}
    if "contratos" in permisos:
        r["contratos"] = BD.leer("crm_contratos", select="*", cuenta_id="eq." + cid, order="creado_at.desc")
    return r


def _estado_actual(cid):
    e = BD.leer("crm_estados", select="estado", cuenta_id="eq." + cid, order="id.desc", limit="1")
    return e[0]["estado"] if e else None


def _paso_abierto(cid):
    return bool(BD.leer("crm_pasos", select="id", cuenta_id="eq." + cid, hecho_at="is.null", limit="1"))


def accion_crm(ses, d):
    cfg, quien, acc = crm_cfg(), ses["nombre"], d.get("accion")
    tipos = cfg.get("tipos") or {}
    activos = set(cfg.get("activos") or [])
    try:
        if acc == "cuenta_nueva":
            c = _limpio(d, CAMPOS_CUENTA)
            if c.get("tipo") not in tipos:
                return 400, {"error": "tipo de cuenta no válido"}
            if not c.get("nombre"):
                return 400, {"error": "falta el nombre"}
            c["dominio"] = c.get("dominio") or _dominio(c.get("web"))
            c.update(producto="moticias", creada_por=quien, origen=c.get("origen") or "manual")
            fila = BD.insertar("crm_cuentas", c)[0]
            est = d.get("estado") or tipos[c["tipo"]]["estados"][0]
            paso = d.get("paso") or {}
            if est in activos and not (paso.get("que") and paso.get("fecha")):
                return 400, {"error": "una cuenta en marcha lleva un siguiente paso con fecha"}
            BD.insertar("crm_estados", {"cuenta_id": fila["id"], "estado": est, "quien": quien, "motivo": "alta"})
            if paso.get("que") and paso.get("fecha"):
                BD.insertar("crm_pasos", {"cuenta_id": fila["id"], "que": paso["que"][:200], "fecha": paso["fecha"], "responsable": paso.get("responsable") or quien, "creado_por": quien})
            if d.get("persona"):
                pe = _limpio(d["persona"], CAMPOS_PERSONA)
                if pe.get("nombre") or pe.get("correo") or pe.get("telefono"):
                    BD.insertar("crm_personas", dict(pe, cuenta_id=fila["id"], creada_por=quien))
            BD.registrar(quien, "crm_cuenta_nueva", fila["id"], {"tipo": c["tipo"]})
            return 200, {"ok": True, "id": fila["id"]}
        cid = d.get("cuenta_id") or d.get("id")
        if acc == "cuenta_editar":
            cambios = _limpio(d.get("cambios") or {}, CAMPOS_CUENTA)
            if "tipo" in cambios and cambios["tipo"] not in tipos:
                return 400, {"error": "tipo de cuenta no válido"}
            if "web" in cambios and "dominio" not in cambios:
                cambios["dominio"] = _dominio(cambios["web"])
            BD.actualizar("crm_cuentas", {"id": "eq." + cid}, cambios)
        elif acc == "cuenta_archivar":
            BD.actualizar("crm_cuentas", {"id": "eq." + cid}, {"archivada_at": datetime.datetime.now().astimezone().isoformat()})
            BD.insertar("crm_actividades", {"cuenta_id": cid, "tipo": "nota", "notas": "Archivada: %s" % (d.get("motivo") or "sin motivo")[:300], "quien": quien})
        elif acc == "persona":
            pe = _limpio(d, CAMPOS_PERSONA)
            if d.get("no_contactar"):
                pe["no_contactar_at"] = datetime.datetime.now().astimezone().isoformat()
                pe["no_contactar_motivo"] = (d.get("no_contactar_motivo") or "pedido por la persona")[:300]
            if d.get("permiso_correo_como"):
                pe["permiso_correo_at"] = datetime.datetime.now().astimezone().isoformat()
                pe["permiso_correo_como"] = d["permiso_correo_como"][:200]
            if d.get("persona_id"):
                pe.pop("cuenta_id", None)
                BD.actualizar("crm_personas", {"id": "eq." + d["persona_id"]}, pe)
            else:
                if not (pe.get("nombre") or pe.get("correo") or pe.get("telefono")):
                    return 400, {"error": "falta el nombre, el correo o el teléfono"}
                BD.insertar("crm_personas", dict(pe, creada_por=quien))
        elif acc == "estado":
            cuenta = BD.leer("crm_cuentas", select="tipo", id="eq." + cid)
            if not cuenta:
                return 404, {"error": "cuenta no encontrada"}
            est = d.get("estado")
            if est not in tipos.get(cuenta[0]["tipo"], {}).get("estados", []):
                return 400, {"error": "ese estado no existe para este tipo de cuenta"}
            if _estado_actual(cid) == "no_contactar":
                return 400, {"error": "«No contactar» es para siempre"}
            paso = d.get("paso") or {}
            if est in activos and not _paso_abierto(cid) and not (paso.get("que") and paso.get("fecha")):
                return 400, {"error": "una cuenta en marcha lleva un siguiente paso con fecha"}
            if est == "nutrir" and not d.get("nutrir_hasta"):
                return 400, {"error": "di hasta cuándo se nutre"}
            BD.insertar("crm_estados", {"cuenta_id": cid, "estado": est, "motivo": (d.get("motivo") or "")[:300] or None,
                                        "nutrir_hasta": d.get("nutrir_hasta") or None, "quien": quien})
            if paso.get("que") and paso.get("fecha"):
                BD.insertar("crm_pasos", {"cuenta_id": cid, "que": paso["que"][:200], "fecha": paso["fecha"], "responsable": paso.get("responsable") or quien, "creado_por": quien})
        elif acc == "actividad":
            if d.get("tipo") not in (cfg.get("actividades") or {}):
                return 400, {"error": "tipo de actividad no válido"}
            BD.insertar("crm_actividades", {"cuenta_id": cid, "persona_id": d.get("persona_id") or None, "tipo": d["tipo"],
                                            "notas": (d.get("notas") or "")[:2000] or None, "quien": quien})
            paso = d.get("paso") or {}
            if paso.get("que") and paso.get("fecha"):
                BD.insertar("crm_pasos", {"cuenta_id": cid, "que": paso["que"][:200], "fecha": paso["fecha"], "responsable": paso.get("responsable") or quien, "creado_por": quien})
        elif acc == "paso":
            if not d.get("que") or not d.get("fecha"):
                return 400, {"error": "el paso necesita qué y fecha"}
            BD.insertar("crm_pasos", {"cuenta_id": cid, "que": d["que"][:200], "fecha": d["fecha"], "responsable": d.get("responsable") or quien, "creado_por": quien})
        elif acc == "paso_hecho":
            BD.actualizar("crm_pasos", {"id": "eq.%d" % int(d.get("paso_id"))}, {"hecho_at": datetime.datetime.now().astimezone().isoformat(), "hecho_por": quien})
        elif acc == "contrato":
            if "contratos" not in ses["permisos"]:
                return 403, {"error": "tu perfil no ve los contratos"}
            co = _limpio(d, CAMPOS_CONTRATO)
            if co.get("importe_cent") is not None:
                co["importe_cent"] = int(round(float(str(co["importe_cent"]).replace(",", ".")) * 100)) if d.get("en_euros") else int(co["importe_cent"])
            if d.get("contrato_id"):
                BD.actualizar("crm_contratos", {"id": "eq.%d" % int(d["contrato_id"])}, co)
            else:
                if not co.get("concepto"):
                    return 400, {"error": "falta el concepto"}
                BD.insertar("crm_contratos", dict(co, cuenta_id=cid, creado_por=quien))
        elif acc == "importar_fuentes":
            if "redaccion" not in ses["permisos"]:
                return 403, {"error": "solo el editor jefe importa las fuentes"}
            fuentes = json.load(open(os.path.join(ROOT, "portal", "data", "sources.json"), encoding="utf-8"))
            ya = {f.get("dominio") for f in BD.leer("crm_cuentas", select="dominio", producto="eq.moticias", tipo="eq.fuente", limit="5000")}
            nuevas, vistos = [], set()
            for f in fuentes:
                dom = _dominio(f.get("url"))
                if not dom or dom in ya or dom in vistos:
                    continue
                vistos.add(dom)
                nuevas.append({"producto": "moticias", "tipo": "fuente", "subtipo": (f.get("type") or "")[:60] or None, "nombre": (f.get("name") or dom)[:200],
                               "web": f.get("url"), "dominio": dom, "origen": "repositorio", "creada_por": quien,
                               "notas": ("Publica: %s · Cadencia: %s" % (f.get("publishes") or "—", f.get("cadence") or "—"))[:4000]})
            filas = BD.insertar("crm_cuentas", nuevas) if nuevas else []
            if filas:
                BD.insertar("crm_estados", [{"cuenta_id": x["id"], "estado": "activa", "quien": quien, "motivo": "importada del repositorio"} for x in filas])
            BD.registrar(quien, "crm_importar_fuentes", None, {"nuevas": len(filas)})
            return 200, {"ok": True, "nuevas": len(filas)}
        else:
            return 400, {"error": "acción desconocida"}
    except BD.ErrorBD as e:
        return 502, {"error": str(e)}
    except (TypeError, ValueError) as e:
        return 400, {"error": "dato no válido: %s" % e}
    BD.registrar(quien, "crm_" + acc, cid)
    return 200, {"ok": True}


# ---------- suscriptores (miembros de Ghost) ----------
def _ghost():
    url, key = os.environ.get("GHOST_URL"), os.environ.get("GHOST_ADMIN_KEY")
    if not url or not key or ":" not in key:
        return None, None
    return G.admin_base(url.rstrip("/")), G.ghost_token(key)


def miembros(q, ver_correos):
    base, tok = _ghost()
    if not base:
        return {"error": "sin clave de Ghost"}
    pref = (crm_cfg().get("suscriptores") or {}).get("prefijo_categoria", "cat:")
    filtros = []
    if q.get("estado") in ("free", "paid", "comped"):
        filtros.append("status:" + q["estado"])
    if q.get("cat"):
        filtros.append("label:" + _slug(pref + q["cat"], 190))
    par = {"limit": "50", "page": str(max(1, int(q.get("pagina") or 1))), "order": "created_at desc", "include": "labels,newsletters"}
    if filtros:
        par["filter"] = "+".join(filtros)
    if q.get("q"):
        par["search"] = q["q"][:80]
    st, r = G.api("GET", base + "/ghost/api/admin/members/?" + urllib.parse.urlencode(par), tok)
    if st != 200:
        return {"error": "Ghost respondió %s" % st}
    out = []
    for m in r.get("members") or []:
        e = m.get("email") or ""
        out.append({"id": m["id"], "nombre": m.get("name") or "", "email": e if ver_correos else ((e[:2] + "…@" + e.split("@")[-1]) if "@" in e else ""),
                    "estado": m.get("status"), "alta": (m.get("created_at") or "")[:10], "boletines": len(m.get("newsletters") or []),
                    "categorias": [l["name"][len(pref):] for l in m.get("labels") or [] if l.get("name", "").startswith(pref)],
                    "etiquetas": [l["name"] for l in m.get("labels") or [] if not l.get("name", "").startswith(pref)]})
    st, lb = G.api("GET", base + "/ghost/api/admin/labels/?limit=all&include=count.members", tok)
    cats = {l["name"][len(pref):]: (l.get("count") or {}).get("members", 0) for l in (lb.get("labels") or []) if l.get("name", "").startswith(pref)} if st == 200 else {}
    pag = (r.get("meta") or {}).get("pagination") or {}
    return {"miembros": out, "total": pag.get("total"), "paginas": pag.get("pages"), "pagina": pag.get("page"),
            "categorias": [{"nombre": c, "n": cats.get(c, 0)} for c in (crm_cfg().get("suscriptores") or {}).get("categorias", [])],
            "ghost": base + "/ghost/#/members"}


def accion_miembro(ses, d):
    base, tok = _ghost()
    if not base:
        return 503, {"error": "sin clave de Ghost"}
    mid = d.get("id") or ""
    if not re.fullmatch(r"[0-9a-f]{24}", mid):
        return 400, {"error": "miembro no válido"}
    st, r = G.api("GET", base + "/ghost/api/admin/members/%s/?include=labels" % mid, tok)
    if st != 200 or not r.get("members"):
        return 404, {"error": "miembro no encontrado"}
    m = r["members"][0]
    cfg = crm_cfg().get("suscriptores") or {}
    pref = cfg.get("prefijo_categoria", "cat:")
    if d.get("accion") == "categorias":
        validas = set(cfg.get("categorias") or [])
        pedidas = [c for c in d.get("categorias") or [] if c in validas]
        labels = [{"name": l["name"]} for l in m.get("labels") or [] if not l["name"].startswith(pref)] + [{"name": pref + c} for c in pedidas]
        st, r = G.api("PUT", base + "/ghost/api/admin/members/%s/" % mid, tok, {"members": [{"labels": labels}]})
        if st != 200:
            return 502, {"error": "Ghost respondió %s" % st}
        BD.registrar(ses["nombre"], "suscriptor_categorias", mid, {"categorias": pedidas})
        return 200, {"ok": True, "categorias": pedidas}
    if d.get("accion") == "enlazar":
        cid = d.get("cuenta_id")
        try:
            ya = BD.leer("crm_personas", select="id", ghost_member_id="eq." + mid)
            datos = {"cuenta_id": cid, "nombre": (m.get("name") or "").strip() or None, "correo": m.get("email"), "ghost_member_id": mid, "perfil": "otro"}
            if ya:
                BD.actualizar("crm_personas", {"id": "eq." + ya[0]["id"]}, {"cuenta_id": cid})
            else:
                BD.insertar("crm_personas", dict(datos, creada_por=ses["nombre"]))
        except BD.ErrorBD as e:
            return 502, {"error": str(e)}
        BD.registrar(ses["nombre"], "suscriptor_enlazar", mid, {"cuenta": cid})
        return 200, {"ok": True}
    return 400, {"error": "acción desconocida"}


# ---------- noticias desde el gestor y dominios de confianza ----------
CLASES_FUENTE = {"notas_de_prensa": "Notas de prensa (fuente de comunicados)", "informacion": "Información (fuente de confianza)",
                 "no_confianza": "No de confianza (siempre revisión del editor jefe)"}
DOMINIOS = "data/fuentes/dominios.json"


def accion_encargo(ses, d):
    """Texto o enlace pegado en el gestor → encargo para la redacción (rutina horaria). Opción 1: investiga y publica hoy.
    Opción 2: además registra el dominio de la fuente con su clase. Solo el editor jefe publica directo; lo del editor y lo
    que venga de un dominio no de confianza queda pendiente de su aprobación."""
    texto, enlace = str(d.get("texto") or "").strip(), str(d.get("enlace") or "").strip()
    if not enlace:
        m = re.search(r"https?://[^\s<>\"']+", texto)
        enlace = m.group(0).rstrip(".,);") if m else ""
    if len(texto) < 10 and not enlace:
        return 400, {"error": "pega un texto o un enlace"}
    if len(texto) < 10:
        texto = "Enlace: " + enlace
    dom = _dominio(enlace) if enlace else None
    clase = d.get("clase_fuente") if d.get("opcion") == 2 else None
    if d.get("opcion") == 2:
        if clase not in CLASES_FUENTE:
            return 400, {"error": "elige la clase de la fuente"}
        if not dom:
            return 400, {"error": "para registrar la fuente hace falta un enlace"}
    jefe = "redaccion" in ses["permisos"]
    no_conf = clase == "no_confianza" or _clase_dominio(dom) == "no_confianza"
    pub = "inmediata" if jefe and not no_conf else "revision"
    try:
        fila = BD.insertar("encargos_gestor", {"texto": texto[:20000], "enlace": enlace[:600] or None, "dominio": dom, "clase_fuente": clase,
                                               "pedido_por": ses["nombre"], "perfil": ses["perfil"], "publicacion": pub})[0]
    except BD.ErrorBD as e:
        return 502, {"error": str(e)}
    nota = None
    if clase:
        ok, nota = registrar_dominio(dom, clase, ses, jefe)
        if not ok:
            nota = "el encargo está guardado, pero no pude registrar la fuente: %s" % nota
    BD.registrar(ses["nombre"], "encargo_noticia", str(fila["id"]), {"dominio": dom, "clase": clase, "publicacion": pub})
    return 200, {"ok": True, "id": fila["id"], "publicacion": pub, "fuente": nota,
                 "aviso": ("La redacción la investiga y la publica en la próxima hora (laborables de 8 a 21)." if pub == "inmediata"
                           else "La redacción la investiga y la deja escrita para que el editor jefe la apruebe.")}


def _dominios():
    d, sha = leer(DOMINIOS)
    return (d or {"dominios": []}), sha


def _clase_dominio(dom):
    if not dom:
        return None
    d, _ = _dominios()
    x = next((x for x in d["dominios"] if x["dominio"] == dom), None)
    if not x:
        return None
    return x["clase"] if x.get("confirmado") else "no_confianza"


def registrar_dominio(dom, clase, ses, jefe):
    d, sha = _dominios()
    x = next((x for x in d["dominios"] if x["dominio"] == dom), None)
    ahora = datetime.datetime.now().astimezone().isoformat(timespec="minutes")
    if x and not jefe and x.get("confirmado"):
        return True, "la fuente %s ya está registrada como «%s»; solo el editor jefe la cambia" % (dom, CLASES_FUENTE[x["clase"]])
    if not x:
        x = {"dominio": dom, "alta": ahora}
        d["dominios"].append(x)
    # Lo que no clasifica el editor jefe cuenta como «no de confianza» hasta que él lo confirme.
    x.update(clase=clase, por=ses["perfil"], actualizado=ahora, confirmado=bool(jefe) or clase == "no_confianza")
    d["dominios"].sort(key=lambda y: y["dominio"])
    ok, det = escribir(DOMINIOS, d, sha, "Fuentes: %s → %s (%s)" % (dom, clase, ses["perfil"]))
    if ok and BD.configurada():  # y su ficha de fuente en el CRM, si no existe
        try:
            if not BD.leer("crm_cuentas", select="id", producto="eq.moticias", tipo="eq.fuente", dominio="eq." + dom):
                c = BD.insertar("crm_cuentas", {"producto": "moticias", "tipo": "fuente", "nombre": dom, "web": "https://" + dom, "dominio": dom,
                                                "subtipo": clase, "origen": "gestor", "creada_por": ses["nombre"]})[0]
                BD.insertar("crm_estados", {"cuenta_id": c["id"], "estado": "activa" if clase != "no_confianza" else "en_seguimiento", "quien": ses["nombre"],
                                            "motivo": CLASES_FUENTE[clase]})
        except BD.ErrorBD:
            pass
    return ok, ("fuente %s registrada como «%s»%s" % (dom, CLASES_FUENTE[clase], "" if x["confirmado"] else "; queda sin confirmar hasta que la vea el editor jefe")) if ok else det


def accion_dominio(ses, d):
    if "redaccion" not in ses["permisos"]:
        return 403, {"error": "solo el editor jefe confirma o cambia las fuentes"}
    dom, clase = str(d.get("dominio") or ""), d.get("clase")
    if clase not in CLASES_FUENTE:
        return 400, {"error": "clase no válida"}
    ok, det = registrar_dominio(dom, clase, ses, True)
    return (200, {"ok": True, "detalle": det}) if ok else (502, {"error": det})


# ---------- HTTP ----------
class handler(BaseHTTPRequestHandler):
    def _enviar(self, st, obj, cookie=None, cors=None, cache="no-store"):
        b = b"" if st == 204 else json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(st)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", cache)
        self.send_header("X-Robots-Tag", "noindex")
        for c in ([cookie] if isinstance(cookie, str) else (cookie or [])):
            self.send_header("Set-Cookie", c)
        if cors == "*":
            self.send_header("Access-Control-Allow-Origin", "*")
        elif cors:
            self.send_header("Access-Control-Allow-Origin", cors)
            self.send_header("Access-Control-Allow-Credentials", "true")
            self.send_header("Vary", "Origin")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def _galletas(self):
        return http.cookies.SimpleCookie(self.headers.get("Cookie") or "")

    def _ses(self):
        c = self._galletas()
        return sesion_de(c[COOKIE].value) if COOKIE in c else None

    def _host(self):
        return self.headers.get("X-Forwarded-Host") or self.headers.get("Host") or "app.moticias.com"

    def _base(self):
        return "https://" + self._host()

    def _q(self):
        return {k: v[0] for k, v in urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).items()}

    def _cab(self):
        return {k.lower(): v for k, v in self.headers.items()}

    def _galletas_entrada(self, perfil, sujeto):
        """Al entrar: la sesión y, si es el editor jefe, la marca para que moticias.com le enseñe sus herramientas."""
        return [cookie_sesion(sujeto), cookie_marca(perfil == "superadmin", self._host())]

    def do_GET(self):
        q, ses = self._q(), self._ses()
        a = q.get("a", "yo")
        if a == "comprobar":  # el cron de Vercel (cabecera Authorization: Bearer CRON_SECRET)
            sec = os.environ.get("CRON_SECRET")
            if not sec or not hmac.compare_digest(self.headers.get("Authorization") or "", "Bearer " + sec):
                return self._enviar(401, {"error": "no autorizado"})
            r = S.comprobar(origen="agente", azar=True)
            return self._enviar(200, {"comprobados": len(r), "fallos": [x["anuncio"] for x in r if not x["ok"]]})
        if a == "publicidad":  # pública: la pide el script de moticias.com
            return self._enviar(200, publicidad_publica(), cors="*", cache="public, max-age=120, s-maxage=300, stale-while-revalidate=3600")
        if a == "yo":
            origen = self.headers.get("Origin")
            if origen == ORIGEN_SITIO:  # desde moticias.com: solo «¿es el editor jefe?»; nada más sale de aquí
                jefe = bool(ses and "redaccion" in ses["permisos"])
                return self._enviar(200, {"jefe": jefe, "gestor": self._base() + "/gestor/"}, cors=origen,
                                    cookie=None if jefe else cookie_marca(False, self._host()))
            cab = self._cab()
            r = {"rol": ses and ses["perfil"], "nombre": ses and ses["nombre"], "permisos": ses and ses["permisos"],
                 "configurado": bool(_claves()["superadmin"]), "escritura": bool(os.environ.get("GITHUB_TOKEN")),
                 "ghost": bool(os.environ.get("GHOST_ADMIN_KEY")), "oficina": bool(_claves()["oficina"]), "bd": BD.configurada(),
                 "ia": bool(os.environ.get("AI_GATEWAY_API_KEY") or cab.get("x-vercel-oidc-token") or os.environ.get("VERCEL_OIDC_TOKEN"))}
            marca = MARCA in self._galletas()
            cookie = None
            if ses and ses["perfil"] == "superadmin" and not marca:
                cookie = cookie_marca(True, self._host())
            elif marca and not (ses and ses["perfil"] == "superadmin"):
                cookie = cookie_marca(False, self._host())
            return self._enviar(200, r, cookie=cookie)
        if not ses:
            return self._enviar(401, {"error": "sin sesión"})
        per = ses["permisos"]
        try:
            if a == "equipo":
                if "equipo" not in per:
                    return self._enviar(403, {"error": "solo el superadministrador ve el equipo"})
                datos, sha = equipo(fresco=True)
                return self._enviar(200, {"personas": [EQ.publica(p) for p in datos.get("personas", [])], "perfiles": EQ.PERFILES,
                                          "almacen": "base privada" if sha == "bd" else EQUIPO_REPO,
                                          "accesible": sha is not None or gh("GET", "", repo=EQUIPO_REPO)[0] == 200})
            if a == "suscriptores":
                r = suscriptores()
                if "equipo" not in per:  # solo el superadministrador ve los correos completos
                    for m in r.get("ultimos", []):
                        e = m.get("email") or ""
                        m["email"] = (e[:2] + "…@" + e.split("@")[-1]) if "@" in e else ""
                return self._enviar(200, r)
            if a == "miembros":
                if "suscriptores" not in per:
                    return self._enviar(403, {"error": "tu perfil no ve los suscriptores"})
                return self._enviar(200, miembros(q, "equipo" in per))
            if a == "piezas":
                return self._enviar(200, {"piezas": piezas(int(q.get("dias") or 14))})
            if a == "pieza":
                r = detalle(q.get("id", ""))
                return self._enviar(200 if r else 404, r or {"error": "pieza no encontrada"})
            if a == "redaccion":
                if "redaccion" not in per:
                    return self._enviar(403, {"error": "solo el editor jefe edita las piezas"})
                r = ficha_redaccion(q.get("id", ""))
                return self._enviar(200 if r else 404, r or {"error": "pieza no encontrada"})
            if a == "firma":
                return self._enviar(200, informe_firma())
            if a == "seguimiento":
                if "publicidad" not in per and "contratos" not in per:
                    return self._enviar(403, {"error": "tu perfil no ve el seguimiento de la publicidad"})
                return self._enviar(200, S.panel(int(q.get("dias") or 30)))
            if a == "encargos":
                if "proponer" not in per and "redaccion" not in per:
                    return self._enviar(403, {"error": "tu perfil no encarga noticias"})
                filas = BD.leer("encargos_gestor", select="id,texto,enlace,dominio,clase_fuente,pedido_por,perfil,publicacion,estado,pieza,resultado,creado_at,cerrado_at",
                                order="creado_at.desc", limit="30") if BD.configurada() else []
                for f in filas:
                    f["texto"] = (f.get("texto") or "")[:280]
                return self._enviar(200, {"encargos": filas, "dominios": _dominios()[0]["dominios"], "clases": CLASES_FUENTE})
            if a == "retoques":
                return self._enviar(200, {"retoques": retoques_de(q.get("pieza") or None)})
            if a == "productos":
                return self._enviar(200, {"productos": productos(), "modos": list(M.MODOS)})
            if a == "anuncios":
                return self._enviar(200, {"anuncios": anuncios(), "publicidad": vertical().get("publicidad") or {}})
            if a in ("crm_resumen", "crm_cuentas", "crm_cuenta"):
                if "crm" not in per:
                    return self._enviar(403, {"error": "tu perfil no entra en el CRM"})
                if not BD.configurada():
                    return self._enviar(503, {"error": "la base privada del CRM aún no está conectada"})
                if a == "crm_resumen":
                    return self._enviar(200, dict(crm_resumen(), cfg=crm_cfg()))
                if a == "crm_cuentas":
                    return self._enviar(200, {"cuentas": crm_cuentas(q)})
                r = crm_ficha(q.get("id"), per)
                return self._enviar(200 if r else 404, r or {"error": "cuenta no encontrada"})
        except BD.ErrorBD as e:
            return self._enviar(502, {"error": str(e)})
        return self._enviar(404, {"error": "acción desconocida"})

    def do_POST(self):
        q, ses = self._q(), self._ses()
        a = q.get("a")
        try:
            n = int(self.headers.get("Content-Length") or 0)
            d = json.loads(self.rfile.read(min(n, 400000)) or b"{}") if n else {}
        except (ValueError, json.JSONDecodeError):
            return self._enviar(400, {"error": "JSON no válido"})
        if a == "evento":  # pública: visualizaciones y clics que manda el script de moticias.com (sendBeacon, texto plano)
            S.evento(d, self.headers.get("User-Agent"))
            return self._enviar(204, {}, cors="*")
        if a == "entrar":
            clave, email = str(d.get("clave") or ""), str(d.get("email") or "").strip()
            if email:  # cuenta personal del equipo
                datos, sha = equipo(fresco=True)
                p = EQ.buscar(datos, email=email)
                if p and p.get("estado") == "activa" and EQ.comprobar(p, clave):
                    p["ultimo_acceso"] = EQ.ahora()
                    guardar_equipo(datos, sha, "Equipo: acceso %s" % p["id"], pid=p["id"])
                    BD.registrar(p.get("nombre") or p["id"], "entrar", p["id"])
                    return self._enviar(200, {"rol": p["perfil"], "nombre": p.get("nombre")},
                                        self._galletas_entrada(p["perfil"], "p-%s-%s" % (p["id"], p.get("version") or 0)))
            else:  # contraseña común (acceso de emergencia del superadministrador y perfil oficina antiguo)
                for r, c in _claves().items():
                    if c and hmac.compare_digest(clave.encode(), c.encode()):
                        BD.registrar("acceso común (%s)" % r, "entrar")
                        return self._enviar(200, {"rol": r}, self._galletas_entrada(r, r))
            time.sleep(1.2)
            return self._enviar(401, {"error": "correo o contraseña incorrectos"})
        if a == "aceptar":
            datos, sha = equipo(fresco=True)
            try:
                p = EQ.aceptar(datos, str(d.get("invitacion") or ""), str(d.get("clave") or ""))
            except ValueError as e:
                time.sleep(0.8)
                return self._enviar(400, {"error": str(e)})
            p["ultimo_acceso"] = EQ.ahora()
            ok, det = guardar_equipo(datos, sha, "Equipo: alta %s" % p["id"], pid=p["id"])
            if not ok:
                return self._enviar(502, {"error": det})
            return self._enviar(200, {"rol": p["perfil"], "nombre": p.get("nombre")},
                                self._galletas_entrada(p["perfil"], "p-%s-%s" % (p["id"], p.get("version") or 0)))
        if a == "salir":
            return self._enviar(200, {"rol": None}, ["%s=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Lax" % COOKIE, cookie_marca(False, self._host())])
        if not ses:
            return self._enviar(401, {"error": "sin sesión"})
        if self.headers.get("X-Gestor") != "1":  # protección CSRF: solo la página del gestor envía esta cabecera
            return self._enviar(403, {"error": "petición no válida"})
        per = ses["permisos"]
        if a == "retoque":  # encargo a la redacción con investigación: solo el editor jefe
            if "redaccion" not in per:
                return self._enviar(403, {"error": "solo el editor jefe pide retoques"})
            return self._enviar(*accion_retoque(ses, d))
        if a == "mencion":
            if "piezas" not in per and "proponer" not in per:
                return self._enviar(403, {"error": "tu perfil no toca las cajas de las piezas"})
            return self._enviar(*accion_mencion(ses["nombre"], d, publica="piezas" in per))
        if a in ("republicar", "republicar_pendientes") and "piezas" not in per:
            return self._enviar(403, {"error": "solo el editor jefe sube cambios a la web"})
        if a == "republicar":
            return self._enviar(200, republicar_y_marcar(d.get("id")))
        if a == "republicar_pendientes":
            ids = [p["id"] for p in piezas(60) if pendiente_web(p)]
            res = [dict(republicar_y_marcar(i), id=i) for i in ids[:15]]
            return self._enviar(200, {"ok": all(r["ok"] for r in res), "piezas": res, "quedan": max(0, len(ids) - 15)})
        if a == "redaccion":
            if "redaccion" not in per:
                return self._enviar(403, {"error": "solo el editor jefe edita, retira o reenfoca piezas"})
            return self._enviar(*accion_redaccion(ses, d, self._cab()))
        if a == "producto":
            if "productos" not in per:
                return self._enviar(403, {"error": "solo el editor jefe cambia los productos"})
            return self._enviar(*accion_producto(d))
        if a == "anuncio":
            if "publicidad" not in per and "proponer" not in per:
                return self._enviar(403, {"error": "tu perfil no toca la publicidad"})
            return self._enviar(*accion_anuncio(ses, d))
        if a == "equipo":
            if "equipo" not in per:
                return self._enviar(403, {"error": "solo el superadministrador gestiona el equipo"})
            return self._enviar(*accion_equipo(ses, d, self._base()))
        if a == "crm":
            if "crm" not in per:
                return self._enviar(403, {"error": "tu perfil no entra en el CRM"})
            if not BD.configurada():
                return self._enviar(503, {"error": "la base privada del CRM aún no está conectada"})
            return self._enviar(*accion_crm(ses, d))
        if a == "comprobar":
            if "publicidad" not in per:
                return self._enviar(403, {"error": "solo el editor jefe lanza el comprobador"})
            if not BD.configurada():
                return self._enviar(503, {"error": "la base privada no está conectada"})
            r = S.comprobar(origen="manual", azar=False, solo=d.get("anuncio"))
            return self._enviar(200, {"resultados": r})
        if a == "encargo":
            if "proponer" not in per and "redaccion" not in per:
                return self._enviar(403, {"error": "tu perfil no encarga noticias"})
            if ses["perfil"] not in ("superadmin", "editor"):
                return self._enviar(403, {"error": "encargan noticias el editor y el editor jefe"})
            if not BD.configurada():
                return self._enviar(503, {"error": "la base privada no está conectada"})
            return self._enviar(*accion_encargo(ses, d))
        if a == "dominio":
            return self._enviar(*accion_dominio(ses, d))
        if a == "miembro":
            if "crm" not in per:
                return self._enviar(403, {"error": "tu perfil no cambia los suscriptores"})
            return self._enviar(*accion_miembro(ses, d))
        return self._enviar(404, {"error": "acción desconocida"})
