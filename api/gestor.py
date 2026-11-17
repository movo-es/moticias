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
  BREVO_API_KEY, PRENSA_REMITENTE, PRENSA_RESPONDER_A  envíos de prensa (src/prensa.py)
  CRON_SECRET               lo manda Vercel en sus crons (comprobar, prensa_cron y ghost_al_dia: moticias.com al día)
  AI_GATEWAY_API_KEY        opcional: sin ella la IA usa el token OIDC de Vercel; MODELO_IA (por defecto anthropic/claude-opus-5.5)
  RUTINA_BARRIDO_TOKEN      token del disparador de API de la tarea «MOTICIAS · batida de fin de semana (mañana)»
                            (claude.ai/code/routines → la tarea → Edit → Trigger → API); sin él, el botón de barrido avisa
  RUTINA_BARRIDO_ID         opcional: id de esa tarea (por defecto verticals/<v>.json → rutinas.barrido)

Retoques del editor jefe (data/retoques/, src/retoques.py): encargos con investigación que atiende la rutina /retoques.

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
import cola as CO  # noqa: E402  (cola del editor: cambio cola-del-editor)
import seo as SEO  # noqa: E402  (panel SEO y asistentes de IA: cambio panel-seo-llm)
import taxonomia as TX  # noqa: E402
import retoques as RT  # noqa: E402  (retoques del editor jefe: data/retoques/README.md)
import bd as BD  # noqa: E402
import redaccion as R  # noqa: E402
import firma as F  # noqa: E402
import seguimiento as S  # noqa: E402
import prensa as PR  # noqa: E402  (prensa: medios, periodistas, envíos y coberturas; openspec/changes/prensa-y-medios/)
import tipos as T  # noqa: E402
import agenda_gestor as AG  # noqa: E402  (agenda de eventos: openspec agenda-de-eventos)
import entradilla as EN  # noqa: E402  (entradilla de las tarjetas: frases completas que caben; openspec entradilla-y-linkedin)
import compartir as CP  # noqa: E402  (botón «Compartir en LinkedIn» de cada pieza)
import restaurar as RS  # noqa: E402  (restauración desde el gestor; openspec restaurar-copia)  (tipos de contenido: marca y rel en un solo sitio; openspec tipos-de-contenido)

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
                  "sections", "image", "crm_cuenta_id", "utm_campaign", "notes",
                  # banner premium (16-11-2026): formato de la rejilla, imagen o caja de texto, imagen para móvil, texto alternativo,
                  # fondo de la paleta y botón (Ir a la web · Pide más información)
                  "formato", "modo", "imagen_movil", "alt", "fondo", "cta_tipo"}


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
    r["entradilla"] = EN.de(a)  # lo que se ve en las tarjetas y lo que se comparte (nunca cortada a media palabra)
    r["linkedin"] = CP.linkedin(a, v)  # texto y enlace del botón «Compartir en LinkedIn»; None si la pieza no está publicada
    r["vista"] = M.insertar_en_medio(G.md_to_html(a.get("body_md", "")), M.cajas_html(a, v, G.inline))
    r["url"] = "https://%s/%s/" % (v.get("domain", "www.moticias.com"), a["id"])
    r["retoques"] = retoques_de(pid)
    # La pieza entera, para leerla en el gestor antes de aprobarla (una pendiente está en borrador:
    # «Ver en moticias.com» no la enseña).
    for k in ("kicker", "subtitle", "key_fact", "key_data", "timeline", "sources", "author_note", "author_role",
              "review_note", "risk", "relevance", "importancia", "firma_motivo", "why", "next", "revised_at"):
        if a.get(k) not in (None, "", []):
            r[k] = a[k]
    r["foto"] = foto_publica(a.get("image"))
    return r


def foto_publica(im):
    """URL pública de la foto de la pieza (la de Ghost si ya se subió) con su crédito, o None."""
    im = im or {}
    src = im.get("src") or ""
    url = src if src.startswith("http") else None
    if not url and src:
        try:
            url = json.load(open(os.path.join(ROOT, "portal", "img", "ghost-urls.json"), encoding="utf-8")).get(os.path.basename(src))
        except Exception:
            url = None
    if not url:
        return None
    return {"url": url, "alt": im.get("alt") or "", "credito": " · ".join(x for x in (im.get("credit"), im.get("license")) if x),
            "fuente": im.get("source") or ""}


# ---------- retoques del editor jefe ----------
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
            return 400, {"error": "los análisis del editor jefe no llevan contenido patrocinado"}
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
                                          "text", "cta", "url", "weight", "nivel", "image", "crm_cuenta_id", "utm_campaign", "updated_at", "propuesto_por",
                                          "formato", "modo", "imagen_movil", "alt", "fondo", "cta_tipo")})
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
    hoy, out = _hoy(), {}
    for a in anuncios():
        if a.get("status") != "activo" or not a.get("url") or not str(a.get("url")).startswith(("https://", "mailto:")):
            continue
        if (a.get("start") and a["start"] > hoy) or (a.get("end") and a["end"] < hoy):
            continue
        # La etiqueta sale siempre de src/tipos.py: el lector ve «Contenido patrocinado» (lo del grupo y lo de un cliente, este con su nombre),
        # «Contenido patrocinado · <cliente>» o «Publicidad», nunca otro texto. Todos los enlaces llevan rel="sponsored".
        caja = {"id": a["id"], "tipo": "grupo" if T.anuncio_es_del_grupo(a, v) else (a.get("type") or "publicidad"), "etiqueta": T.marca_anuncio(a, v), "rel": T.rel("patrocinado"),
                "anunciante": a.get("advertiser") or "", "titular": a.get("headline") or "", "texto": a.get("text") or "", "cta": a.get("cta") or "",
                "url": a["url"], "nivel": a.get("nivel") or "estandar", "peso": int(a.get("weight") or 1), "imagen": a.get("image") or None,
                "secciones": a.get("sections") or [], "campana": a.get("utm_campaign") or a["id"]}
        caja.update(banner_publico(a, pub))
        for h in a.get("slots") or []:
            h = "portada-premium" if h == "cabecera" else h  # el hueco «cabecera» quedaba encima de la apertura (16-11-2026)
            if h in huecos:
                out.setdefault(h, []).append(caja)
    orden = {"premium": 0, "estandar": 1, "basico": 2}
    for h in out:  # lo pagado delante de las cajas del grupo; después por nivel y peso
        out[h].sort(key=lambda c: (c["tipo"] == "grupo", orden.get(c["nivel"], 3), -c["peso"]))
    return {"huecos": out, "tope_pago": int(pub.get("tope_pago_por_pagina") or 3), "rejilla": pub.get("rejilla") or {},
            "formulario": bool((pub.get("formulario") or {}).get("activo")),
            "formulario_textos": {k: (pub.get("formulario") or {}).get(k) for k in ("version", "aviso", "consentimiento")} if (pub.get("formulario") or {}).get("activo") else None,
            "generado": datetime.datetime.now().astimezone().isoformat(timespec="minutes")}


# ---------- banner premium (cambio banner-premium, 16-11-2026) ----------
def _lum(hexa):
    v = [int(hexa[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    v = [x / 12.92 if x <= .03928 else ((x + .055) / 1.055) ** 2.4 for x in v]
    return .2126 * v[0] + .7152 * v[1] + .0722 * v[2]


def contraste(a, b):
    x, y = _lum(a), _lum(b)
    return (max(x, y) + .05) / (min(x, y) + .05)


def _fondo(pub, fid):
    for f in ((pub.get("caja_texto") or {}).get("fondos") or []):
        if f["id"] == fid:
            return f
    return None


def banner_publico(a, pub):
    """Lo que el sitio necesita para pintar el banner: formato, modo, imágenes, colores ya resueltos y botón. Si el
    formulario está apagado, «Pide más información» se pinta como «Ir a la web»."""
    out = {"formato": a.get("formato") if a.get("formato") in (pub.get("formatos") or {}) else None,
           "modo": a.get("modo") if a.get("modo") in ("imagen", "texto") else ("imagen" if a.get("image") else "texto"),
           "imagen_movil": a.get("imagen_movil") or None, "alt": a.get("alt") or ""}
    f = _fondo(pub, a.get("fondo") or "azul")
    if f:
        out["colores"] = {k: f[k] for k in ("fondo", "texto", "boton", "boton_texto")}
    ct = a.get("cta_tipo")
    if ct == "info" and not (pub.get("formulario") or {}).get("activo"):
        ct = "web"
    out["cta_tipo"] = ct if ct in ("web", "info") else None
    out["cta_texto"] = (pub.get("cta") or {}).get(ct) if ct else None
    return out


def validar_banner(a, pub):
    """Errores que impiden activar un banner (lista vacía si vale)."""
    err = []
    if a.get("formato") and a["formato"] not in (pub.get("formatos") or {}):
        err.append("formato no válido")
    if a.get("modo") == "imagen":
        if not a.get("image"):
            err.append("falta la imagen")
        if not (a.get("alt") or "").strip():
            err.append("falta el texto alternativo de la imagen (obligatorio)")
    if a.get("modo") == "texto":
        lim = (pub.get("caja_texto") or {}).get("limites") or {}
        for campo, k in (("headline", "titular"), ("text", "texto"), ("advertiser", "anunciante")):
            if lim.get(k) and len(a.get(campo) or "") > lim[k]:
                err.append("el %s pasa de %d caracteres" % (k, lim[k]))
        f = _fondo(pub, a.get("fondo") or "azul")
        if not f:
            err.append("fondo no válido")
        else:
            m = float((pub.get("caja_texto") or {}).get("contraste_minimo") or 4.5)
            if contraste(f["fondo"], f["texto"]) < m or contraste(f["boton"], f["boton_texto"]) < m:
                err.append("ese fondo no tiene contraste suficiente")
    if a.get("cta_tipo") not in (None, "", "web", "info"):
        err.append("botón no válido")
    return err


def subir_imagen_anuncio(ses, d):
    """Sube a Ghost la imagen de un banner (ya recortada en el navegador a la proporción del formato). Devuelve su URL."""
    if not ("publicidad" in ses["permisos"] or "contratos" in ses["permisos"] or "proponer" in ses["permisos"]):
        return 403, {"error": "tu perfil no sube imágenes de publicidad"}
    m = re.match(r"^data:image/(jpeg|png|webp);base64,(.+)$", str(d.get("datos") or ""), re.S)
    if not m:
        return 400, {"error": "la imagen tiene que ser JPG, PNG o WebP"}
    datos = base64.b64decode(m.group(2))
    if len(datos) > 4 * 1024 * 1024:
        return 400, {"error": "la imagen pesa más de 4 MB: guárdala más ligera"}
    url, key = os.environ.get("GHOST_URL"), os.environ.get("GHOST_ADMIN_KEY")
    if not url or not key:
        return 503, {"error": "faltan las claves de Ghost en Vercel"}
    nombre = "banner-%s-%s.%s" % (_slug(d.get("nombre") or "anuncio", 30), secrets.token_hex(3), "jpg" if m.group(1) == "jpeg" else m.group(1))
    limite = "----MoticiasBanner%d" % int(time.time() * 1000)
    cuerpo = b"".join([("--%s\r\nContent-Disposition: form-data; name=\"purpose\"\r\n\r\nimage\r\n" % limite).encode(),
                       ("--%s\r\nContent-Disposition: form-data; name=\"file\"; filename=\"%s\"\r\nContent-Type: image/%s\r\n\r\n" % (limite, nombre, m.group(1))).encode(),
                       datos, ("\r\n--%s--\r\n" % limite).encode()])
    req = urllib.request.Request(G.admin_base(url.rstrip("/")) + "/ghost/api/admin/images/upload/", data=cuerpo, method="POST",
                                 headers={"Authorization": "Ghost " + G.ghost_token(key), "Content-Type": "multipart/form-data; boundary=" + limite,
                                          "Accept-Version": "v5.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            res = json.loads(r.read())
    except urllib.error.HTTPError as e:
        return 502, {"error": "Ghost no aceptó la imagen (%s)" % e.code}
    BD.registrar(ses["nombre"], "publicidad_imagen", nombre)
    return 200, {"ok": True, "url": res["images"][0]["url"]}


FORM_CAMPOS = ("nombre", "empresa", "email", "telefono", "direccion", "cp", "ciudad", "pais")
_FORM_IP = {}


def formulario_publico(d, ua, ip):
    """«Pide más información» de un banner: guarda el envío en la base privada (pub_formularios), ligado a la campaña, y lo
    manda al anunciante (la persona de su cuenta del CRM con correo y sin «No contactar»). Solo con el formulario encendido."""
    v = vertical()
    pub = v.get("publicidad") or {}
    cfg = pub.get("formulario") or {}
    if not cfg.get("activo"):
        return 403, {"error": "el formulario todavía no está activo"}
    if S.ROBOT.search(ua or ""):
        return 204, {}
    ahora = time.time()
    _FORM_IP[ip] = [t for t in _FORM_IP.get(ip, []) if ahora - t < 600] + [ahora]
    if len(_FORM_IP[ip]) > 5:
        return 429, {"error": "demasiados envíos seguidos; prueba dentro de unos minutos"}
    a = next((x for x in anuncios() if x["id"] == d.get("anuncio") and x.get("status") == "activo"), None)
    if not a or a.get("cta_tipo") != "info":
        return 404, {"error": "anuncio no encontrado"}
    f = {k: " ".join(str(d.get(k) or "").split())[:200] or None for k in FORM_CAMPOS}
    obligatorios = [c for c, ob in cfg.get("campos") or [] if ob]
    faltan = [c for c in obligatorios if not f.get(c)]
    if faltan:
        return 400, {"error": "faltan campos obligatorios: " + ", ".join(faltan)}
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", f["email"] or ""):
        return 400, {"error": "el correo no es válido"}
    if d.get("consentimiento") is not True:
        return 400, {"error": "hace falta tu consentimiento para entregar los datos al anunciante"}
    fila = dict(f, anuncio=a["id"], campana=a.get("utm_campaign") or a["id"], anunciante=a.get("advertiser"), consentimiento=True,
                texto_legal=str(d.get("texto_legal") or cfg.get("version") or "sin versión")[:40], pagina=str(d.get("pagina") or "")[:200],
                dispositivo=str(d.get("dispositivo") or "")[:20], procedencia=str(d.get("procedencia") or "")[:80])
    try:
        r = BD.insertar("pub_formularios", fila)[0]
    except BD.ErrorBD as e:
        return 502, {"error": "no se pudo guardar: %s" % e}
    para = []
    if a.get("crm_cuenta_id"):
        try:
            para = [p["correo"] for p in BD.leer("crm_personas", select="correo", cuenta_id="eq." + str(a["crm_cuenta_id"]), correo="not.is.null",
                                                   no_contactar_at="is.null", archivada_at="is.null", limit="2")]
        except BD.ErrorBD:
            para = []
    filas = "".join("<tr><td style='padding:4px 10px;color:#5d6b82'>%s</td><td style='padding:4px 10px'>%s</td></tr>" % (k.capitalize(), html_escape(f[k] or "—")) for k in FORM_CAMPOS)
    cuerpo = ("<p>Una persona ha pedido más información desde tu anuncio «%s» en MOTICIAS y ha dado su consentimiento para que te entreguemos estos datos:</p>"
              "<table>%s</table><p style='color:#5d6b82;font-size:12px'>MOTICIAS (Avionline S.L.) solo entrega estos datos y guarda una copia %s meses para "
              "acreditar el envío y el consentimiento. Desde este momento, el tratamiento es responsabilidad del anunciante.</p>") % (
                  html_escape(a.get("headline") or a["id"]), filas, cfg.get("conservacion_meses", 12))
    ok, det = (False, "el anunciante no tiene correo en el CRM") if not para else M.enviar_correo("MOTICIAS · Petición de información: " + (a.get("headline") or "")[:80],
                                                                                              cuerpo, para, M.remitentes_avisos(v))
    if not ok:  # si no llega al anunciante, llega al editor jefe para que lo reenvíe
        M.enviar_correo("MOTICIAS · Formulario sin entregar (%s)" % a["id"], cuerpo + "<p><b>No se pudo entregar al anunciante:</b> %s</p>" % html_escape(det),
                        [v["prensa"]["aviso_editor_jefe"]], M.remitentes_avisos(v))
    try:
        BD.actualizar("pub_formularios", {"id": "eq.%s" % r["id"]}, {"entregado": ok, "entregado_at": datetime.datetime.now(datetime.timezone.utc).isoformat() if ok else None,
                                                                   "error_entrega": None if ok else det[:300]})
    except BD.ErrorBD:
        pass
    S.evento_ampliado({"a": a["id"], "h": d.get("hueco") or "portada-premium", "s": d.get("seccion"), "dv": d.get("dispositivo"), "pr": d.get("procedencia"), "t": "form_enviado"}, ua)
    return 200, {"ok": True, "mensaje": "Enviado. %s te contestará." % (a.get("advertiser") or "El anunciante")}


def html_escape(x):
    return str(x).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


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
    for k in ("image", "imagen_movil"):
        if cambios.get(k) and not str(cambios[k]).startswith("https://"):
            return 400, {"error": "la imagen tiene que estar subida (https://)"}
    if cambios.get("url") and not str(cambios["url"]).startswith(("https://", "mailto:")):
        return 400, {"error": "el enlace tiene que empezar por https:// (o mailto: para escribir a un correo)"}
    for k in ("start", "end"):
        if cambios.get(k) and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(cambios[k])):
            return 400, {"error": "fecha no válida (%s)" % k}
    for k, n in (("headline", 140), ("text", 400), ("cta", 60), ("name", 120), ("advertiser", 120), ("notes", 1000), ("utm_campaign", 60), ("alt", 200)):
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
                  "label": T.marca_anuncio({"type": cambios.get("type") or "publicidad", "advertiser": cambios.get("advertiser")}, v), "status": "propuesta",
                  "type": "publicidad", "tipo_contenido": "patrocinado", "nivel": "estandar", "slots": [], "sections": [], "weight": 1}, None
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
    if cambios.get("status") and cambios["status"] != a.get("status"):  # fechas de publicación y retirada para el seguimiento
        a.setdefault("historial", []).append({"en": datetime.datetime.now().astimezone().isoformat(timespec="minutes"), "estado": cambios["status"],
                                              "por": ses["perfil"]})
    a.update(cambios)
    if T.anuncio_es_del_grupo(a, v):  # enlaza a una empresa del grupo: siempre «servicio del grupo» (tipos-de-contenido)
        a["type"] = "grupo"
    a["tipo_contenido"] = "patrocinado"
    a["label"] = T.marca_anuncio(a, v)  # la etiqueta visible no se escribe a mano: sale del tipo (y del cliente, si paga uno)
    if a.get("status") == "activo" and (not a.get("url") or not a.get("slots") or not a.get("headline")):
        return 400, {"error": "para activarla necesita titular, enlace (https:// o mailto:) y al menos un hueco"}
    a["slots"] = ["portada-premium" if h == "cabecera" else h for h in (a.get("slots") or [])]  # «cabecera» quedaba encima de la apertura
    malos = validar_banner(a, pub)
    if malos and (a.get("status") == "activo" or "formato" in cambios or "modo" in cambios):
        return 400, {"error": "; ".join(malos)}
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
            "enfoques": {k: t.split(":")[0] for k, t in R.ENFOQUES.items()}, "entradilla_max": EN.config(v)["max"],
            "firma": {"actual": "editor_jefe" if F.es_del_editor_jefe(a, c) else "redaccion", "editor_jefe": c["editor_jefe"], "redaccion": c["redaccion"],
                      "importante": imp, "motivo": mot, "propuesta": dec["firma"], "cupo": dec["cupo"]}}


def _aplicar_firma(a, quiere, v):
    """Firma pedida por el editor jefe para esta pieza. El tope del 10 % no se salta ni a mano."""
    c = F.config(v)
    if quiere == "editor_jefe":
        q = F.cupo(F.cargar(ROOT), a.get("date") or _hoy(), c, excluir=a["id"])
        if not F.es_del_editor_jefe(a, c) and q["libres_max"] <= 0:
            raise ValueError("tu firma ya está en el %s %% de las piezas de los últimos %s días (tope %s %%): firma la redacción" % (q["pct"], c["ventana_dias"], c["max_pct"]))
        a["firma_editor_jefe"] = True
        a["author"], a["author_role"] = c["editor_jefe"], c["editor_jefe_role"]
        if a.get("author_note"):
            a["author_note"] = (v.get("editor") or {}).get("interests_note") or a["author_note"]
    elif quiere == "redaccion":
        a["firma_editor_jefe"] = False
        a["author"], a["author_role"] = c["redaccion"], c["redaccion_role"]
        if a.get("author_note"):
            a["author_note"] = (v.get("editorial") or {}).get("interests_note_redaccion") or F.NOTA_REDACCION


def proximo_lunes_8():
    """El próximo lunes a las 08:00 (Europe/Madrid; horario de invierno UTC+1, de verano UTC+2) como ISO con zona. Si hoy es
    lunes y aún no son las 08:00, hoy."""
    utc = datetime.datetime.now(datetime.timezone.utc)
    def desfase(dia):  # último domingo de marzo → último domingo de octubre: verano
        ult = lambda m: max(datetime.date(dia.year, m, d) for d in range(25, 32) if datetime.date(dia.year, m, d).weekday() == 6)  # noqa: E731
        return 2 if ult(3) <= dia < ult(10) else 1
    hoy = (utc + datetime.timedelta(hours=1)).date()
    for n in range(0, 8):
        dia = hoy + datetime.timedelta(days=n)
        if dia.weekday() != 0:
            continue
        h = desfase(dia)
        cuando = datetime.datetime(dia.year, dia.month, dia.day, 8, 0, tzinfo=datetime.timezone(datetime.timedelta(hours=h)))
        if cuando > utc + datetime.timedelta(minutes=10):
            return cuando.isoformat()
    dia = hoy + datetime.timedelta(days=7 - hoy.weekday())
    return datetime.datetime(dia.year, dia.month, dia.day, 8, 0, tzinfo=datetime.timezone(datetime.timedelta(hours=desfase(dia)))).isoformat()


def _hoy_madrid():
    """La fecha de hoy en Madrid (el servidor va en UTC: entre las 00:00 y la 01:00 o las 02:00 aún sería «ayer»)."""
    utc = datetime.datetime.now(datetime.timezone.utc)
    ult = lambda m: max(datetime.date(utc.year, m, x) for x in range(25, 32) if datetime.date(utc.year, m, x).weekday() == 6)  # noqa: E731
    return (utc + datetime.timedelta(hours=2 if ult(3) <= utc.date() < ult(10) else 1)).date().isoformat()


def voz_propuestas():
    """Las propuestas de «La voz del editor» pendientes de aprobación (kind opinion), con lo que hace falta para decidir."""
    out = []
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "articles", "*.json"))):
        try:
            a = json.load(open(f, encoding="utf-8"))
        except ValueError:
            continue
        if a.get("kind") != "opinion" or a.get("status") not in ("pendiente", "borrador", "publicado"):
            continue
        if a.get("status") == "publicado" and (a.get("published_at") or "") < datetime.datetime.now().astimezone().isoformat():
            continue  # ya salió
        img = a.get("image") or {}
        out.append({"id": a["id"], "title": a.get("title"), "subtitle": a.get("subtitle"), "enfoque": (a.get("voz") or {}).get("enfoque") or a.get("summary"),
                    "palabras": len((a.get("body_md") or "").split()), "status": a.get("status"), "published_at": a.get("published_at"),
                    "fuentes": len(a.get("sources") or []),
                    "semana": (a.get("voz") or {}).get("semana"), "image": {"src": img.get("src"), "credit": img.get("credit"), "license": img.get("license"),
                    "source_url": img.get("source_url") or img.get("url"), "alt": img.get("alt")} if img else None,
                    "ghost": FOTOS_GHOST_URL(img.get("src"))})
    return sorted(out, key=lambda x: (x["status"] != "pendiente", x["id"]))


def FOTOS_GHOST_URL(src):
    """URL para enseñar la foto en el gestor: la de Ghost si ya se subió; si no, la del repositorio (es público), para que
    una imagen candidata se pueda ver y aprobar antes de que exista en Ghost."""
    if not src:
        return None
    if str(src).startswith("http"):
        return src
    if not str(src).startswith("img/"):
        return None
    try:
        m = json.load(open(os.path.join(ROOT, "portal", "img", "ghost-urls.json"), encoding="utf-8"))
    except (OSError, ValueError):
        m = {}
    return m.get(str(src)[4:]) or "https://raw.githubusercontent.com/%s/%s/portal/%s" % (REPO, BRANCH, urllib.parse.quote(str(src)))


def voz_publicadas(n=5):
    """Las últimas columnas de «La voz del editor» ya publicadas, para verlas y abrirlas desde el gestor."""
    out, ahora, v = [], datetime.datetime.now().astimezone().isoformat(), vertical()
    for f in glob.glob(os.path.join(ROOT, "data", "articles", "*.json")):
        try:
            a = json.load(open(f, encoding="utf-8"))
        except ValueError:
            continue
        if a.get("kind") == "opinion" and a.get("status") == "publicado" and (a.get("published_at") or "") <= ahora:
            out.append({"id": a["id"], "title": a.get("title"), "date": a.get("date"), "url": _url_pieza(a, v)})
    return sorted(out, key=lambda x: x["date"] or "", reverse=True)[:n]


VOZ_MARCA = "LA VOZ DEL EDITOR · columna de opinión"  # así empieza el texto del encargo; /noticias-gestor lo reconoce


def _voz_cfg():
    return vertical().get("voz_del_editor") or {}


def _semana(dia=None):
    y, w, _ = (dia or datetime.date.today()).isocalendar()
    return "%d-W%02d" % (y, w)


OFICIALES = ("boe.es", "gob.es", "europa.eu", "congreso.es", "senado.es", "cnmc.es", "airef.es", "ine.es", "poderjudicial.es", "tribunalconstitucional.es")


def _dominio_oficial(dom):
    """Boletines, ministerios, Cortes, reguladores e instituciones europeas: cuentan como fuente oficial en una columna."""
    return bool(dom) and any(dom == o or dom.endswith("." + o) for o in OFICIALES)


def voz_nueva_pieza(d, quien, v=None):
    """Columna escrita por el editor jefe en el gestor → pieza `kind: opinion` pendiente de su propia aprobación (texto e
    imagen, como las del sábado). No publica nada. Devuelve la pieza o lanza ValueError con lo que falta."""
    v = v or vertical()
    cfg = v.get("voz_del_editor") or {}
    titulo, texto = str(d.get("title") or "").strip(), str(d.get("body_md") or "").strip()
    sub, enfoque = str(d.get("subtitle") or "").strip(), str(d.get("enfoque") or "").strip()
    if len(titulo) < 8:
        raise ValueError("ponle un título a la columna")
    if len(texto.split()) < 120:
        raise ValueError("el texto es muy corto para una columna (menos de 120 palabras): si solo tienes la idea, usa «Encargar el borrador»")
    primer = next((p.strip() for p in texto.split("\n\n") if p.strip() and not p.lstrip().startswith(("#", ">"))), texto)
    primer = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", primer).replace("**", "")
    resumen = primer if len(primer) <= 320 else primer[:320].rsplit(" ", 1)[0] + "…"
    enlaces = sorted(set(re.findall(r"\]\((https?://[^)\s]+)\)", texto)))
    hoy = _hoy()
    a = {"id": "%s-%s" % (_slug(titulo, 60), "".join(secrets.choice("abcdefghijkmnpqrstuvwxyz23456789") for _ in range(4))),
         "kind": cfg.get("kind", "opinion"), "tipo_contenido": cfg.get("tipo_contenido", "editorial"), "section": "analisis", "status": "pendiente",
         "author": cfg.get("autor", "Rainer Uphoff"), "author_role": (v.get("editor") or {}).get("role") or "Editor jefe de MOTICIAS",
         "author_note": (v.get("editor") or {}).get("interests_note"),
         "date": hoy, "event_date": hoy, "featured": 0, "kicker": "La voz del editor", "title": titulo, "subtitle": sub, "summary": resumen,
         "entradilla": EN.proponer(primer, EN.config(v)["max"]) or EN.recortar(primer, EN.config(v)["max"]),
         "body_md": texto, "image": None, "relevance": "ALTA", "importancia": 4,
         "sources": [{"kind": "oficial" if _dominio_oficial(_dominio(u)) else "medios", "outlet": _dominio(u) or "enlace", "title": u, "url": u,
                      "published": None, "accessed": hoy} for u in enlaces],
         "voz": {"semana": _semana(), "enfoque": enfoque or sub or resumen, "origen": "escrita por el editor jefe en el gestor"},
         "revisiones": [{"en": R.ahora(), "por": quien, "accion": "columna escrita en el gestor; pendiente de aprobación"}]}
    tx = TX.Taxonomia(VERTICAL)
    a.update(tx.clasificar(a))
    a.update(tx.etiquetas(a))
    a["importancia"] = 4
    if tx.faltan(a):  # una columna puede no nombrar ningún modo: va a «varios medios», ámbito estatal, tema análisis
        a["medio"], a["modos"] = (a.get("medio") if a.get("medio") in tx.medios else "varios"), a.get("modos") or []
        if not a["modos"]:
            a["medio"] = "varios"
        a["temas"], a["territorios"] = a.get("temas") or ["analisis"], a.get("territorios") or ["estado"]
    T.comprobar(a, "articles", v)
    return a


def accion_voz(ses, d):
    """«La voz del editor» desde el gestor (cambio voz-desde-el-panel, 16-11-2026). `crear`: el editor jefe escribe la columna
    y queda pendiente de su aprobación. `encargar`: da el tema y su enfoque y la redacción horaria prepara el borrador
    (docs/tarea-voz-del-editor.md), que vuelve aquí como propuesta. Ninguna de las dos publica."""
    acc, quien = d.get("accion"), ses["nombre"]
    if acc == "crear":
        if not os.environ.get("GITHUB_TOKEN"):
            return 503, {"error": "el gestor no puede escribir: falta GITHUB_TOKEN en Vercel"}
        try:
            a = voz_nueva_pieza(d, quien)
        except ValueError as e:
            return 400, {"error": str(e)}
        ok, det = escribir(_ruta_pieza(a["id"]), a, None, "La voz del editor: %s escribe «%s»" % (quien, a["title"][:60]))
        if not ok:
            return 502, {"error": det}
        BD.registrar(quien, "voz_crear", a["id"], {"commit": det, "palabras": len(a["body_md"].split())})
        return 200, {"ok": True, "id": a["id"], "commit": det, "sin_fuentes": not a["sources"],
                     "aviso": "Guardada como pendiente. Léela, añade una imagen si quieres y apruébala para publicarla."}
    if acc == "encargar":
        tema, enfoque, enlaces = str(d.get("tema") or "").strip(), str(d.get("enfoque") or "").strip(), str(d.get("enlaces") or "").strip()
        if len(tema) < 8:
            return 400, {"error": "di de qué va la columna"}
        if len(enfoque) < 15:
            return 400, {"error": "escribe tu enfoque: qué defiendes y por qué (una o dos frases bastan)"}
        texto = "%s\nTema: %s\nEnfoque del editor jefe: %s%s" % (VOZ_MARCA, tema, enfoque, "\nEnlaces y notas: " + enlaces if enlaces else "")
        m = re.search(r"https?://[^\s<>\"']+", enlaces)
        try:
            fila = BD.insertar("encargos_gestor", {"texto": texto[:20000], "enlace": (m.group(0).rstrip(".,);")[:600] if m else None), "dominio": None,
                                                   "clase_fuente": None, "pedido_por": quien, "perfil": ses["perfil"], "publicacion": "revision"})[0]
        except BD.ErrorBD as e:
            return 502, {"error": str(e)}
        BD.registrar(quien, "voz_encargar", str(fila["id"]), {"tema": tema[:120]})
        return 200, {"ok": True, "id": fila["id"],
                     "aviso": "Encargada. La redacción prepara el borrador en su próxima pasada (laborables, cada hora de 8 a 21) y lo deja aquí, pendiente de tu aprobación."}
    return 400, {"error": "acción desconocida"}


def voz_encargos():
    """Columnas encargadas a la redacción que aún no han vuelto como propuesta."""
    if not BD.configurada():
        return []
    try:
        filas = BD.leer("encargos_gestor", select="id,texto,estado,resultado,creado_at", estado="in.(pendiente,en_curso,sin_fuentes)",
                        texto="like.%s*" % VOZ_MARCA, order="creado_at.desc", limit="6")
    except BD.ErrorBD:
        return []
    out = []
    for f in filas:
        m = re.search(r"Tema: (.*)", f.get("texto") or "")
        out.append({"id": f["id"], "tema": (m.group(1) if m else "")[:160], "estado": f.get("estado"), "resultado": f.get("resultado"), "creado_at": f.get("creado_at")})
    return out


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


ACCIONES_SUBIDA = ("redaccion_publicar", "republicar", "web_reintento")
REINTENTOS_MAX = 12  # reintentos automáticos por pieza; después solo a mano, con el error a la vista


def subidas_fallidas(dias=7):
    """Piezas aprobadas en el gestor cuya última subida a Ghost falló (gestor_registro). Así el gestor no dice «publicada»
    de algo que no está en la web y el cron `web_reintentos` lo repite solo (cambio subidas-que-no-llegan, 16-11-2026).
    Devuelve {id: {"error", "desde", "intentos"}}."""
    if not BD.configurada():
        return {}
    desde = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=dias)).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        filas = BD.leer("gestor_registro", select="objeto,accion,detalle,at", accion="in.(%s)" % ",".join(ACCIONES_SUBIDA),
                        at="gte." + desde, order="at.asc", limit="1000")
    except BD.ErrorBD:
        return {}
    ult, auto, primero = {}, {}, {}
    for f in filas:
        pid, det = f.get("objeto"), f.get("detalle") or {}
        if not pid or "ghost" not in det:
            continue
        if det["ghost"]:
            auto.pop(pid, None), primero.pop(pid, None)
        else:
            primero.setdefault(pid, f.get("at"))
            if f.get("accion") == "web_reintento":
                auto[pid] = auto.get(pid, 0) + 1
        ult[pid] = det
    return {pid: {"error": str(det.get("error") or det.get("detalle") or "")[:300], "desde": primero.get(pid), "intentos": auto.get(pid, 0)}
            for pid, det in ult.items() if det["ghost"] is False}


def reintentar_subidas(max_n=4):
    """Vuelve a subir a Ghost lo aprobado que no llegó. Solo piezas que siguen `publicado`; cada intento queda en el registro."""
    hechas = []
    for pid, f in subidas_fallidas().items():
        if len(hechas) >= max_n or f["intentos"] >= REINTENTOS_MAX:
            continue
        ruta = _ruta_pieza(pid)
        a, _ = leer(ruta) if ruta else (None, None)
        if not a or a.get("status") != "publicado":
            continue
        ok, det = _subir(a, vertical(), "published")
        BD.registrar("gestor (reintento automático)", "web_reintento", pid, {"ghost": ok, "detalle": str(det)[:500]})
        hechas.append({"id": pid, "ok": ok, "detalle": str(det)[:200]})
    return {"ok": all(h["ok"] for h in hechas), "reintentadas": hechas}


def entradillas_al_dia(segundos=200):  # menos de los cinco minutos que dura el pase de Ghost
    """Deja en Ghost, como resumen de cada post, la entradilla de su pieza (cambio entradilla-y-linkedin, 17-11-2026).
    Compara lo que viene con el despliegue con lo que tiene Ghost y cambia solo el resumen de los que no coinciden —ni el
    texto, ni la fecha, ni el estado—. Antes de escribir lee la pieza fresca del repositorio, para no pisar una entradilla
    que el editor acaba de cambiar. Lo llama el cron `web_reintentos`; si no hay nada distinto, es una sola consulta."""
    url, key = os.environ.get("GHOST_URL"), os.environ.get("GHOST_ADMIN_KEY")
    if not url or not key or ":" not in key:
        return {"ok": False, "detalle": "sin clave de Ghost en el gestor"}
    fin = time.time() + segundos
    url = url.rstrip("/")
    token = G.ghost_token(key)
    posts = G.resumenes_en_ghost(url, token)
    hechas, fallos, quedan = [], [], 0
    for p in sorted(glob.glob(os.path.join(ROOT, "data", "articles", "*.json"))):
        a = json.load(open(p, encoding="utf-8"))
        post = posts.get(a["id"])
        if not post or (post.get("custom_excerpt") or "") == EN.de(a):
            continue
        if time.time() > fin:
            quedan += 1
            continue
        fresca, _ = leer("data/articles/%s.json" % a["id"])
        texto = EN.de(fresca or a)
        if (post.get("custom_excerpt") or "") == texto:
            continue
        ok, det = G.poner_resumen(post, texto, url, token)
        (hechas if ok else fallos).append(a["id"] if ok else {"id": a["id"], "error": det})
    if hechas or fallos:
        BD.registrar("gestor (entradillas)", "entradillas_al_dia", None, {"cambiadas": len(hechas), "fallos": fallos[:10], "quedan": quedan})
    return {"ok": not fallos, "cambiadas": len(hechas), "fallos": fallos[:10], "quedan": quedan}


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
            if d.get("firma") in ("editor_jefe", "redaccion"):
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
        elif acc == "publicar":  # el visto bueno del editor jefe a una pieza pendiente
            if a.get("status") not in ("pendiente", "borrador"):
                return 400, {"error": "la pieza no está pendiente"}
            if a.get("kind") == "opinion":  # «La voz del editor»: texto e imagen aprobados expresamente
                if not (d.get("texto_ok") and (d.get("imagen_ok") or not a.get("image"))):
                    return 400, {"error": "aprueba expresamente el texto y la imagen"}
                # Sale el lunes a las 08:00 salvo que el editor jefe elija «Publicar ahora» (voz-desde-el-panel, 16-11-2026).
                if d.get("cuando") == "ahora":
                    a["published_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
                    a["date"] = _hoy_madrid()
                else:
                    a["published_at"] = proximo_lunes_8()
                    a["date"] = a["published_at"][:10]
                a.setdefault("voz", {}).update({"aprobada": R.ahora(), "salida": "ahora" if d.get("cuando") == "ahora" else "lunes"})
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
    BD.registrar(quien, "redaccion_" + acc, pid, dict({"commit": det, "ghost": g_ok}, **({} if g_ok else {"error": str(g)[:500]})))
    return 200, {"ok": True, "commit": det, "ghost": {"ok": g_ok, "detalle": g}, "pieza": ficha_redaccion(pid)}


def informe_firma():
    v = vertical()
    c = F.config(v)
    arts = F.cargar(ROOT)
    q = F.cupo(arts, _hoy(), c)
    suyas = sorted([{"id": a["id"], "title": a.get("title"), "date": a.get("date"), "status": a.get("status")} for a in arts.values()
                    if F.es_del_editor_jefe(a, c) and q["desde"] <= (a.get("date") or "") <= q["hasta"]], key=lambda x: x["date"], reverse=True)
    return {"cupo": q, "piezas": suyas, "regla": ((v.get("editorial") or {}).get("firma_editor_jefe") or {}).get("regla")}


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
    try:  # agenda-de-eventos (migración 015): contactos con nivel y fuente, y eventos que organiza
        r["contactos"] = BD.leer("crm_contactos", select="*", cuenta_id="eq." + cid, archivado_at="is.null", order="nivel.asc")
        r["eventos"] = BD.leer("agenda_organizadores", select="evento_id,persona_id", cuenta_id="eq." + cid, order="evento_id.asc")
    except BD.ErrorBD:
        r["contactos"], r["eventos"] = [], []
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


# ---------- prensa (src/prensa.py) ----------
def accion_prensa(ses, d, base):
    quien, acc, per = ses["nombre"], d.get("accion"), ses["permisos"]
    jefe = "piezas" in per  # solo el editor jefe envía, anula y lanza la detección de suscriptores
    try:
        if acc == "medio_guardar":
            PR.guardar_medio(quien, d["cuenta_id"], d.get("cambios") or {})
        elif acc == "medio_nuevo":
            return 200, {"ok": True, "id": PR.nuevo_medio(quien, d)}
        elif acc == "periodista":
            return 200, {"ok": True, "id": PR.guardar_periodista(quien, d)}
        elif acc == "cobertura":
            PR.cobertura(quien, d)
        elif acc == "respuesta":
            PR.respuesta(quien, d)
        elif acc == "envio_crear":
            eid, n = PR.crear_envio(quien, d)
            return 200, {"ok": True, "id": eid, "destinatarios": n}
        elif acc == "envio_enviar":
            # La oficina aprueba y envía las notas de prensa pagadas de clientes (sala de prensa; decisión de Rainer,
            # 9-11-2026); los envíos en nombre de MOTICIAS siguen siendo solo del editor jefe.
            e = (PR.envio(int(d.get("id") or 0)) or {}).get("envio") or {}
            de_cliente = e.get("tipo") == "nota_de_prensa" and e.get("por_cuenta_de")
            if not (jefe or ("notas_clientes" in per and de_cliente)):
                return 403, {"error": "solo el editor jefe aprueba y envía" + ("" if de_cliente else " los envíos de MOTICIAS")}
            return 200, dict(PR.enviar(quien, int(d.get("id") or 0), base), ok=True)
        elif acc == "envio_anular":
            BD.actualizar("prensa_envios", {"id": "eq.%d" % int(d.get("id") or 0), "estado": "in.(borrador,aprobado)"}, {"estado": "anulado"})
            BD.registrar(quien, "prensa_envio_anulado", str(d.get("id")))
        elif acc == "sincronizar":
            return 200, dict(PR.sincronizar(d.get("id")), ok=True)
        elif acc == "suscriptores":
            if not jefe:
                return 403, {"error": "solo el editor jefe lanza la detección"}
            base_g, tok = _ghost()
            if not base_g:
                return 503, {"error": "sin clave de Ghost"}
            return 200, dict(PR.detectar_suscriptores(base_g, tok, G.api), ok=True)
        elif acc == "recalcular":
            return 200, {"ok": True, "r": PR.recalcular()}
        else:
            return 400, {"error": "acción desconocida"}
    except (ValueError, KeyError) as e:
        return 400, {"error": str(e)}
    except BD.ErrorBD as e:
        return 502, {"error": str(e)}
    return 200, {"ok": True}


def prensa_cron():
    """Miércoles (Vercel Cron): suscriptores de MOTICIAS entre los periodistas, estados de Brevo y recálculo."""
    r = {"at": datetime.datetime.now().astimezone().isoformat(timespec="seconds")}
    if not BD.configurada():
        return dict(r, error="base sin configurar")
    base_g, tok = _ghost()
    try:
        r["suscriptores"] = PR.detectar_suscriptores(base_g, tok, G.api) if base_g else "sin clave de Ghost"
    except BD.ErrorBD as e:
        r["suscriptores"] = str(e)
    try:
        r["brevo"] = PR.sincronizar() if os.environ.get("BREVO_API_KEY") else "sin BREVO_API_KEY"
    except BD.ErrorBD as e:
        r["brevo"] = str(e)
    r["recalculo"] = PR.recalcular()
    BD.registrar("cron", "prensa_cron", None, {k: v for k, v in r.items() if k != "at"})
    return r


# ---------- barrido a demanda ----------
RUTINA_API = "https://api.anthropic.com/v1/claude_code/routines/%s/fire"


def hora_madrid():
    try:
        import zoneinfo
        return datetime.datetime.now(zoneinfo.ZoneInfo("Europe/Madrid")).strftime("%H:%M")
    except Exception:  # sin base de zonas horarias en el servidor
        return datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M UTC")


def lanzar_barrido(ses, pista):
    """Botón «Iniciar barrido de noticias ahora» (decisión de Rainer, 9-11-2026; cambio fin-de-semana-barrido-y-arranque):
    lanza la batida de grandes noticias por el disparador de API de su tarea programada. El token vive solo en Vercel; el
    texto que se envía es un dato para la rutina (quién lo pidió, cuándo y la pista), nunca instrucciones."""
    token = os.environ.get("RUTINA_BARRIDO_TOKEN")
    rid = os.environ.get("RUTINA_BARRIDO_ID") or (vertical().get("rutinas") or {}).get("barrido")
    hora = hora_madrid()
    pista = " ".join(str(pista or "").split())[:200]
    if not token or not rid:
        # 16-11-2026: claude.ai solo ofrece el activador «Programación», así que no hay disparo por API. El barrido
        # queda encargado en la base privada (barridos_pedidos, migración 016) y lo recoge la siguiente tarea que corre:
        # la pasada horaria de retoques y noticias del gestor (laborables, 8 a 21) o la batida de fin de semana (11:00 y 17:30).
        try:
            fila = BD.insertar("barridos_pedidos", {"pedido_por": (ses.get("nombre") or ses.get("perfil") or "gestor")[:120],
                                                    "perfil": (ses.get("perfil") or "")[:40] or None, "pista": pista or None})[0]
        except Exception as e:
            return 502, {"error": "no pude encargar el barrido: %s" % e}
        return 200, {"ok": True, "cola": True, "hora": hora, "id": fila.get("id"),
                     "mensaje": "Barrido encargado a las %s. Empieza en la próxima pasada de la redacción (laborables, cada hora de 8 a 21; "
                                "sábados y domingos, 11:00 y 17:30). El resultado llega como aviso al móvil." % hora}
    texto = ("Barrido a demanda pedido desde el gestor de app.moticias.com por %s (perfil %s) a las %s, hora de Madrid. "
             "Pista del editor: %s." % (ses.get("nombre") or "sin nombre", ses.get("perfil"), hora, pista or "ninguna"))
    req = urllib.request.Request(RUTINA_API % urllib.parse.quote(rid), method="POST", data=json.dumps({"text": texto}).encode("utf-8"),
                                 headers={"Authorization": "Bearer " + token, "anthropic-version": "2023-06-01",
                                          "anthropic-beta": "experimental-cc-routine-2026-04-01", "Content-Type": "application/json",
                                          "User-Agent": "Moticias-gestor/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.loads(r.read().decode("utf-8") or "{}")
        return 200, {"ok": True, "hora": hora, "sesion": d.get("claude_code_session_url")}
    except urllib.error.HTTPError as e:
        det = e.read().decode("utf-8", "replace")[:300]
        if e.code == 429:
            return 429, {"error": "demasiados barridos seguidos; vuelve a intentarlo en %s s" % (e.headers.get("Retry-After") or "unos")}
        return 502, {"error": "la tarea no arrancó (HTTP %s): %s" % (e.code, det)}
    except urllib.error.URLError as e:
        return 502, {"error": "sin conexión con Claude: %s" % e}


# ---------- HTTP ----------

# ---------- moticias.com al día desde Vercel (11-11-2026) ----------
# La tarea programada no tiene las claves de Ghost; Vercel sí. Este cron mira qué edición enseña la portada de
# moticias.com (página «edicion-hoy») y, si en data/editions/ hay alguna posterior, la publica con los mismos scripts
# que la rutina (ghost_publish.py y ghost_edicion.py), en orden. Si la web ya está al día, no hace nada.
# ---------- copias de seguridad en el Mac (cambio copia-de-seguridad-mac; migración 010) ----------
# El Mac manda solo fecha, tamaños, huellas y recuentos (nunca datos). Producción no depende de él: si no hay copias,
# lo único que pasa es que el cron diario avisa por correo.
def copias_resumen():
    if not BD.configurada():
        return {"configurada": False}
    cfg = vertical().get("copias") or {}
    filas = BD.leer("copias_registro", select="id,clase,ok,inicio,fin,equipo,partes,error", order="fin.desc", limit="40")
    ult = next((f for f in filas if f["clase"] == "copia" and f["ok"]), None)
    prueba = next((f for f in filas if f["clase"] == "prueba" and f["ok"]), None)
    ahora = datetime.datetime.now(datetime.timezone.utc)
    dias = lambda f: None if not f else round((ahora - datetime.datetime.fromisoformat(f["fin"].replace("Z", "+00:00"))).total_seconds() / 86400, 1)
    return {"configurada": True, "ultima_copia": ult, "dias_sin_copia": dias(ult), "ultima_prueba": prueba, "dias_sin_prueba": dias(prueba),
            "ultimo_intento": filas[0] if filas else None, "historial": filas[:14],
            "umbral_dias": cfg.get("aviso_dias_sin_copia", 3), "umbral_prueba_dias": cfg.get("aviso_dias_sin_prueba", 35)}


def copias_vigilar():
    """Cron diario: avisa a Rainer por correo si pasan más días de los fijados sin una copia correcta, si la última falló o
    si hace más de un mes que no se prueba una restauración."""
    r = copias_resumen()
    if not r.get("configurada"):
        return {"aviso": None, "motivo": "base sin configurar"}
    motivos = []
    if r["dias_sin_copia"] is None:
        motivos.append("todavía no ha llegado ninguna copia del Mac")
    elif r["dias_sin_copia"] > r["umbral_dias"]:
        motivos.append("hace %s días de la última copia correcta (%s)" % (r["dias_sin_copia"], r["ultima_copia"]["fin"][:16].replace("T", " ")))
    if r["ultimo_intento"] and not r["ultimo_intento"]["ok"]:
        motivos.append("el último intento falló: %s" % (r["ultimo_intento"].get("error") or "sin detalle"))
    if r["ultima_copia"] and (r["dias_sin_prueba"] is None or r["dias_sin_prueba"] > r["umbral_prueba_dias"]):
        motivos.append("no hay una prueba de restauración correcta en los últimos %s días" % r["umbral_prueba_dias"])
    if not motivos:
        return {"aviso": None, "dias_sin_copia": r["dias_sin_copia"]}
    v = vertical()
    para = (v.get("copias") or {}).get("aviso_a") or (v.get("productos") or {}).get("email") or []
    cuerpo = ("<p>Copias de seguridad de MOTICIAS en el Mac:</p><ul>%s</ul><p>Producción sigue funcionando: esto solo avisa de que el "
              "respaldo no está al día. Basta con encender el Mac y dejarlo despierto un rato; la copia se hace sola. "
              "Detalle en el gestor: https://app.moticias.com/gestor/ → Equipo → Copias.</p>" % "".join("<li>%s</li>" % html_esc(m) for m in motivos))
    ok, det = M.enviar_correo("MOTICIAS · copia de seguridad: %s" % motivos[0], cuerpo, para, M.remitentes_avisos(vertical()))
    return {"aviso": motivos, "enviado": ok, "detalle": det if not ok else None}


def html_esc(t):
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---------- restauración (cambio restaurar-copia, «sí» de Rainer del 15-11-2026; migración 011, src/restaurar.py) ----------
# Contenido: versiones de un documento de data/ desde el historial del repositorio; restaurar escribe una versión nueva.
# Base privada: copia interna nocturna en el esquema `copia` (14 días); se recuperan filas o campos, nunca se borra nada.
# Cada restauración avisa al editor jefe por correo y queda en gestor_registro.
def _gh_fichero(ruta, ref):
    st, r = gh("GET", "contents/%s?ref=%s" % (urllib.parse.quote(ruta), ref))
    if st != 200 or "content" not in r:
        return None
    return json.loads(base64.b64decode(r["content"]).decode("utf-8"))


def _avisar_restauracion(asunto, lineas, enlace):
    para = (vertical().get("productos") or {}).get("email") or []
    cuerpo = "<p>%s</p><p><a href=\"%s\">Abrir en el gestor</a> (desde ahí se deshace).</p>" % ("<br>".join(html_esc(l) for l in lineas), enlace)
    try:
        ok, det = M.enviar_correo("MOTICIAS · restauración: " + asunto, cuerpo, para, M.remitentes_avisos(vertical()))
        if not ok:
            BD.registrar("sistema", "aviso_fallido", asunto[:200], {"detalle": det[:300]})
        return ok
    except Exception as e:
        BD.registrar("sistema", "aviso_fallido", asunto[:200], {"detalle": str(e)[:300]})
        return False


def restaurables(q):
    v, out = vertical(), []
    q = (q or "").lower().strip()
    for pref, nombre in (RS.cfg(v).get("contenido") or {}).items():
        for f in sorted(glob.glob(os.path.join(ROOT, pref, "*.json")), reverse=True):
            try:
                d = json.load(open(f, encoding="utf-8"))
            except ValueError:
                continue
            ruta = pref + os.path.basename(f)
            t = RS.titulo(d, ruta)
            if q and q not in (t + " " + ruta).lower():
                continue
            out.append({"ruta": ruta, "titulo": t, "clase": nombre, "fecha": d.get("date") or d.get("updated_at") or "", "autor": d.get("author")})
            if len(out) >= 60:
                return out
    return out


def versiones(ses, ruta):
    v = vertical()
    if not RS.ruta_valida(ruta, v):
        return 400, {"error": "ese documento no se restaura desde el gestor"}
    st, r = gh("GET", "commits?path=%s&sha=%s&per_page=30" % (urllib.parse.quote(ruta), BRANCH))
    if st != 200:
        return 502, {"error": "GitHub no da el historial (%s)" % st}
    lista = [{"sha": c["sha"], "fecha": (c.get("commit", {}).get("author") or {}).get("date"), "autor": (c.get("commit", {}).get("author") or {}).get("name"),
              "mensaje": (c.get("commit", {}).get("message") or "").split("\n")[0][:160]} for c in r]
    actual = _gh_fichero(ruta, BRANCH)
    return 200, {"ruta": ruta, "titulo": RS.titulo(actual, ruta), "versiones": lista}


def version(ses, ruta, sha):
    v = vertical()
    if not RS.ruta_valida(ruta, v) or not re.fullmatch(r"[0-9a-f]{7,40}", sha or ""):
        return 400, {"error": "petición no válida"}
    antigua, actual = _gh_fichero(ruta, sha), _gh_fichero(ruta, BRANCH)
    if antigua is None:
        return 404, {"error": "esa versión no tiene el documento"}
    ok, motivo = RS.puede_contenido(ses["perfil"], ruta, actual, antigua, v)
    # Se compara lo que de verdad quedaría (con lo que se conserva y se completa al restaurar), sin el registro de la operación
    quedaria = RS.restaurado(antigua, actual, ruta, ses["perfil"], "", sha, "", "", v)
    dif = [f for f in RS.diferencias(quedaria, actual) if f["campo"] not in ("revisiones", "revised_at", "updated_at")]
    return 200, {"ruta": ruta, "sha": sha, "diferencias": dif, "restaurable": ok, "motivo": motivo}


def restaurar_version(ses, d):
    v = vertical()
    ruta, sha = str(d.get("ruta") or ""), str(d.get("sha") or "")
    if not RS.ruta_valida(ruta, v) or not re.fullmatch(r"[0-9a-f]{7,40}", sha):
        return 400, {"error": "petición no válida"}
    antigua = _gh_fichero(ruta, sha)
    actual, sha_fich = leer(ruta)
    if antigua is None:
        return 404, {"error": "esa versión no tiene el documento"}
    if sha_fich is None:
        return 503, {"error": "falta GITHUB_TOKEN en Vercel"}
    ok, motivo = RS.puede_contenido(ses["perfil"], ruta, actual, antigua, v)
    if not ok:
        return 403, {"error": motivo}
    st, hist = gh("GET", "commits?path=%s&sha=%s&per_page=1" % (urllib.parse.quote(ruta), BRANCH))
    previa = hist[0]["sha"] if st == 200 and hist else None
    st, com = gh("GET", "commits/%s" % sha)
    fecha_v = ((com.get("commit") or {}).get("author") or {}).get("date", "")[:16] if st == 200 else ""
    quien = ses.get("nombre") or ses["perfil"]
    nuevo = RS.restaurado(antigua, actual, ruta, ses["perfil"], quien, sha, fecha_v, d.get("motivo"), v)
    if ruta.startswith("data/articles/"):
        try:
            T.comprobar(nuevo, "articles", v)
        except ValueError as e:
            return 400, {"error": "la versión restaurada no se puede publicar: %s" % e}
    ok, det = escribir(ruta, nuevo, sha_fich, "Restauración de %s a la versión del %s (%s), por %s" % (ruta, fecha_v or "?", sha[:7], quien))
    if not ok:
        return 502, {"error": det}
    web = None
    if ruta.startswith("data/articles/"):
        w_ok, w_det = republicar(nuevo, v)
        web = {"ok": w_ok, "detalle": w_det}
    BD.registrar(quien, "restaurar_version", ruta, {"version": sha[:7], "previa": (previa or "")[:7], "motivo": (d.get("motivo") or "")[:200]})
    enlace = "https://app.moticias.com/gestor/?" + urllib.parse.urlencode({"vista": "restaurar", "ruta": ruta})
    _avisar_restauracion(RS.titulo(nuevo, ruta), ["%s ha restaurado «%s» (%s) a la versión del %s." % (quien, RS.titulo(nuevo, ruta), ruta, fecha_v),
                                                  "Motivo: %s" % (d.get("motivo") or "sin motivo"),
                                                  "Para deshacer: abre el documento en «Restaurar» y elige la versión anterior a esta."], enlace)
    return 200, {"ok": True, "commit": det, "web": web, "deshacer": {"ruta": ruta, "sha": previa}}


def copia_rpc(nombre, cuerpo):
    try:
        return 200, BD.peticion("POST", "rpc/" + nombre, cuerpo=cuerpo)
    except BD.ErrorBD as e:
        return 400, {"error": str(e)[:300]}


def copia_recuperar(ses, d):
    v = vertical()
    tabla = str(d.get("tabla") or "")
    if tabla not in RS.tablas_permitidas(ses["perfil"], v):
        return 403, {"error": "tu perfil no recupera datos de esa tabla"}
    st, r = copia_rpc("copia_recuperar", {"p_tabla": tabla, "p_fecha": d.get("fecha"), "p_clave": d.get("clave") or {},
                                          "p_campos": d.get("campos") or None})
    if st != 200:
        return st, r
    quien = ses.get("nombre") or ses["perfil"]
    BD.registrar(quien, "copia_recuperar", tabla, {"fecha": d.get("fecha"), "clave": d.get("clave"), "resultado": r})
    _avisar_restauracion("%s · %s" % (tabla, d.get("fecha")),
                         ["%s ha recuperado de la copia interna del %s una fila de «%s»." % (quien, d.get("fecha"), tabla),
                          "Resultado: %s" % json.dumps(r, ensure_ascii=False)[:400]],
                         "https://app.moticias.com/gestor/?vista=restaurar")
    return 200, {"ok": True, "resultado": r}


# ---------- secciones de moticias.com al día (decisión de Rainer, 15-11-2026) ----------
# Las páginas de sección se pintan con el índice del buscador (app/public/buscador/index.json). Las tareas programadas no
# pueden subirlo por el buzón (solo contenido), así que el servidor lo rehace desde data/ en cada pasada del cron
# ghost_al_dia y lo sube a main si cambió. En las pasadas en que el índice ya está al día, comprueba que cada sección
# enseña lo que cabe esperar (src/secciones.py) y, si no, avisa al editor jefe por correo (una vez al día como mucho).
def indice_al_dia():
    import export_search_index as X
    if not os.environ.get("GITHUB_TOKEN"):
        return {"ok": False, "error": "falta GITHUB_TOKEN"}
    out = X.construir(os.path.join(ROOT, "data"))
    st, r = gh("GET", "contents/app/public/buscador/index.json?ref=%s" % BRANCH)
    actual = {}
    if st == 200 and r.get("content"):
        try:
            actual = json.loads(base64.b64decode(r["content"]).decode("utf-8"))
        except ValueError:
            actual = {}
    sin_fecha = lambda d: {k: v for k, v in d.items() if k != "generado"}
    if actual and sin_fecha(actual) == sin_fecha(out):
        return {"ok": True, "cambiado": False, "piezas": len(out["piezas"])}
    ix, ti = X.textos(out)
    ok, det = _commit_lote([{"ruta": "app/public/buscador/index.json", "texto": ix}, {"ruta": "app/public/buscador/tipos.json", "texto": ti}],
                           "Índice del buscador y de las secciones al día (%d piezas)" % len(out["piezas"]), "G. Jordan", "redaccion@moticias.com",
                           rutas=("app/public/buscador/",), comprobar_base=False)
    return {"ok": ok, "cambiado": ok, "piezas": len(out["piezas"]), "detalle": det}


def secciones_vigilar():
    import export_search_index as X
    import secciones as SEC
    v = vertical()
    try:
        servido = SEC._get_json(SEC.INDICE_WEB)
    except Exception as e:
        return {"ok": False, "error": "no se pudo leer el índice servido: %s" % e}
    try:
        en_ghost = SEC.publicadas_en_ghost(v)
    except Exception:
        en_ghost = None
    res = SEC.comprobar(X.construir(os.path.join(ROOT, "data")), servido, en_ghost, v)
    res["aviso"] = None
    if res["problemas"] and BD.configurada():
        hoy = datetime.date.today().isoformat()
        try:
            ya = BD.leer("gestor_registro", select="id", accion="eq.secciones_aviso", at="gte.%sT00:00:00Z" % hoy, limit="1")
        except BD.ErrorBD:
            ya = []
        if not ya:
            para = (v.get("productos") or {}).get("email") or []
            cuerpo = ("<p>Comprobación de las secciones de moticias.com tras la última actualización:</p><ul>%s</ul><p>Detalle por sección: %s</p>"
                      % ("".join("<li>%s</li>" % html_esc(p) for p in res["problemas"]),
                         html_esc(", ".join("%s %d/%d" % (s, x["servidas"], x["esperadas"]) for s, x in res["secciones"].items()))))
            ok, det = M.enviar_correo("MOTICIAS · las secciones no enseñan lo que deberían", cuerpo, para, M.remitentes_avisos(vertical()))
            BD.registrar("cron", "secciones_aviso", None, {"problemas": res["problemas"][:5], "enviado": ok})
            res["aviso"] = {"enviado": ok}
    return res


def ghost_al_dia(solo=None):
    import re as _re, shutil, subprocess
    url, key = os.environ.get("GHOST_URL"), os.environ.get("GHOST_ADMIN_KEY")
    if not url or not key:
        return {"ok": False, "error": "faltan GHOST_URL o GHOST_ADMIN_KEY en Vercel"}
    eds = {}
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "editions", "*.json"))):
        try:
            d = json.load(open(f, encoding="utf-8"))
            eds[os.path.basename(f)[:-5]] = int(d.get("number") or 0)
        except Exception:
            pass
    base, tok = G.admin_base(url.rstrip("/")), G.ghost_token(key)
    st, r = G.api("GET", base + "/ghost/api/admin/pages/slug/edicion-hoy/", tok)
    if st != 200:
        return {"ok": False, "error": "no se pudo leer la página edicion-hoy de Ghost (%s)" % st}
    pag = ((r or {}).get("pages") or [{}])[0]
    # Desde el 15-11-2026 el título es solo la fecha; el número va en <meta name="moticias-edicion"> (cambio cabecera-sin-numero).
    m = _re.search(r'name="moticias-edicion" content="(\d+)"', pag.get("codeinjection_head") or "") \
        or _re.search(r"n\D{0,3}(\d+)", pag.get("title", ""))
    en_web = int(m.group(1)) if m else 0
    if not en_web and not solo:  # sin número no se sabe qué tiene la web: no se republica todo a ciegas
        return {"ok": False, "error": "la página edicion-hoy no dice qué edición tiene; publícala a mano con ghost_edicion.py"}
    faltan = [f for f, n in sorted(eds.items()) if n > en_web] if not solo else [solo]
    if not faltan:
        return {"ok": True, "en_web": en_web, "publicadas": []}
    tmp = "/tmp/moticias-ghost"
    shutil.rmtree(tmp, ignore_errors=True)
    for sub in ("src", "verticals", "data", os.path.join("portal", "img")):
        if os.path.isdir(os.path.join(ROOT, sub)):
            shutil.copytree(os.path.join(ROOT, sub), os.path.join(tmp, sub))
    os.makedirs(os.path.join(tmp, "work"), exist_ok=True)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    hechas = []
    for fecha in faltan:
        res = {"fecha": fecha}
        for nombre, args in (("piezas", ["src/ghost_publish.py", "--date", fecha, "--status", "published"]),
                             ("portada", ["src/ghost_edicion.py", "--date", fecha])):
            pr = subprocess.run([sys.executable, "-I"] + args, cwd=tmp, env=env, capture_output=True, text=True, timeout=200)
            res[nombre] = {"ok": pr.returncode == 0, "salida": (pr.stdout or "")[-600:], "error": (pr.stderr or "")[-600:]}
        hechas.append(res)
    return {"ok": all(h["piezas"]["ok"] and h["portada"]["ok"] for h in hechas), "en_web_antes": en_web, "publicadas": hechas}


# ---------- cola del editor (cambio cola-del-editor, 15 y 16-11-2026; migración 012, src/cola.py) ----------
# Temas nuevos para el editor jefe. Solo él confirma (= encargo a la redacción horaria) y publica; los demás proponen.
COLA_CAMPOS = ("id,titulo,resumen,avisos,clave_hecho,medio,modos,temas,territorios,importancia,importancia_agente,fiabilidad,"
               "event_date,fecha_limite,no_caduca,solucion,seccion,estado,estado_antes,origen,rutina,propuesto_por,perfil,pieza,motivo,creado_at,actualizado_at")


def _ahora_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="minutes")


def _hist(t, quien, que):
    return (t.get("historial") or []) + [{"cuando": _ahora_iso(), "quien": quien, "que": que}]


def _cola_sincronizar(temas):
    """Lleva a la cola lo que ha hecho la redacción con los encargos de los temas confirmados."""
    vivos = [t for t in temas if t["estado"] in ("confirmado", "en_redaccion", "para_aprobar")]
    if not vivos:
        return
    enc = BD.leer("encargos_gestor", select="id,cola_tema,estado,pieza,resultado", cola_tema="in.(%s)" % ",".join(str(t["id"]) for t in vivos),
                  order="creado_at.desc")
    ultimo = {}
    for e in enc:
        ultimo.setdefault(e["cola_tema"], e)
    paso = {"pendiente": "confirmado", "en_curso": "en_redaccion", "pendiente_aprobacion": "para_aprobar", "publicada": "publicado",
            "sin_fuentes": "sin_fuente", "descartado": "archivado"}
    for t in vivos:
        e = ultimo.get(t["id"])
        if not e:
            continue
        nuevo = paso.get(e["estado"], t["estado"])
        if nuevo != t["estado"] or (e.get("pieza") and e["pieza"] != t.get("pieza")):
            cambios = {"estado": nuevo, "pieza": e.get("pieza") or t.get("pieza"), "actualizado_at": _ahora_iso()}
            if nuevo in ("sin_fuente", "archivado"):
                cambios["motivo"] = (e.get("resultado") or "")[:1000] or ("sin fuente primaria" if nuevo == "sin_fuente" else "descartado por la redacción")
            BD.actualizar("cola_temas", {"id": "eq.%s" % t["id"]}, cambios)
            t.update(cambios)


def cola_listar(ses, pestana):
    if not CO.puede(ses["perfil"], "ver"):
        return 403, {"error": "tu perfil no ve la cola"}
    if not BD.configurada():
        return 503, {"error": "la base privada no está conectada"}
    if pestana == "cola":
        try:
            CO.caducar()
        except BD.ErrorBD:
            pass
    estados = CO.PESTANAS.get(pestana, CO.ESTADOS_COLA)
    temas = BD.leer("cola_temas", select=COLA_CAMPOS, estado="in.(%s)" % ",".join(estados), order="creado_at.desc", limit="300")
    if pestana in ("confirmados", "cola"):
        _cola_sincronizar(temas)
        temas = [t for t in temas if t["estado"] in estados]
    cuenta = {}
    for k, est in CO.PESTANAS.items():
        try:
            cuenta[k] = len(BD.leer("cola_temas", select="id", estado="in.(%s)" % ",".join(est), limit="1000"))
        except BD.ErrorBD:
            cuenta[k] = None
    hoy = CO.hoy_madrid()
    for t in temas:
        c = CO.caduca(t)
        t["caduca"] = str(c) if c else None
        t["dias"] = (c - hoy).days if c else None
    tx = TX.Taxonomia()
    ejes = {}
    if tx:
        ejes = {"medio": {k: v["nombre"] for k, v in tx.medios.items()}, "medio_apagado": [k for k, v in tx.medios.items() if not v.get("activo")],
                "modo": {k: v["nombre"] for k, v in tx.modos_t.items()}, "tema": {k: v["nombre"] for k, v in tx.temas.items()},
                "region": {k: v.get("nombre_corto") or v["nombre"] for k, v in tx.territorios.items()}}
    yo = {"perfil": ses["perfil"], "nombre": ses["nombre"], "jefe": ses["perfil"] == "superadmin"}
    return 200, {"temas": [CO.para_perfil(t, ses["perfil"]) for t in temas], "cuenta": cuenta, "ejes": ejes, "yo": yo,
                 "secciones": list(CO.SECCIONES), "soluciones": list(CO.SOLUCIONES) if ses["perfil"] != "comercial" else []}


def _cola_encargo(ses, t):
    """«Confirmar»: encargo para la redacción horaria (/noticias-gestor), enlazado al tema."""
    lineas = [t["titulo"], ""] + ([t["resumen"], ""] if t.get("resumen") else [])
    for a in t.get("avisos") or []:
        lineas.append("· %s%s%s%s" % (a.get("texto") or "", (" — " + a["fuente"]) if a.get("fuente") else "", (" (" + a["fecha"] + ")") if a.get("fecha") else "",
                                      (" " + a["url"]) if a.get("url") else ""))
    lineas.append("")
    lineas.append("Tema confirmado desde la cola del editor (tema %s). Etiquetas: medio %s · modos %s · temas %s · regiones %s · importancia %s · "
                  "fiabilidad %s · fecha del hecho %s · fecha límite %s · sección %s." % (
                      t["id"], t.get("medio"), ",".join(t.get("modos") or []), ",".join(t.get("temas") or []), ",".join(t.get("territorios") or []),
                      t.get("importancia"), t.get("fiabilidad"), t.get("event_date") or "-", t.get("fecha_limite") or "-", t.get("seccion") or "-"))
    enlace = next((a["url"] for a in t.get("avisos") or [] if a.get("url")), None)
    fila = {"texto": "\n".join(lineas)[:20000], "enlace": enlace, "dominio": _dominio(enlace) if enlace else None, "pedido_por": ses["nombre"],
            "perfil": ses["perfil"], "publicacion": "inmediata", "cola_tema": t["id"]}
    return BD.insertar("encargos_gestor", fila)[0]


def cola_accion(ses, d):
    if not BD.configurada():
        return 503, {"error": "la base privada no está conectada"}
    op, perfil, quien = d.get("op"), ses["perfil"], ses["nombre"]
    if op == "proponer":
        if not CO.puede(perfil, "proponer"):
            return 403, {"error": "tu perfil no propone temas"}
        try:
            fila = CO.normalizar(d.get("tema") or {}, perfil=perfil, nombre=quien)
        except ValueError as e:
            return 400, {"error": str(e)}
        if perfil != "superadmin":
            fila["importancia"] = fila["importancia_agente"]  # su sugerencia; la decide el editor jefe
        fila["historial"] = [{"cuando": _ahora_iso(), "quien": quien, "que": "propuesto"}]
        r = BD.insertar("cola_temas", fila)[0]
        BD.registrar(quien, "cola_proponer", str(r["id"]), {"titulo": fila["titulo"][:120]})
        return 200, {"ok": True, "id": r["id"]}
    ids = [int(x) for x in (d.get("ids") or []) if str(x).isdigit()][:100]
    if not ids:
        return 400, {"error": "no hay temas seleccionados"}
    temas = BD.leer("cola_temas", select=COLA_CAMPOS + ",historial", id="in.(%s)" % ",".join(map(str, ids)))
    if not temas:
        return 404, {"error": "no encuentro esos temas"}
    permiso = {"confirmar": "confirmar", "importancia": "importancia", "editar": "editar", "seccion": "seccion",
               "archivar": "archivar", "papelera": "papelera", "recuperar": "recuperar"}.get(op)
    if not permiso:
        return 400, {"error": "acción desconocida"}
    negados = [t["id"] for t in temas if not CO.puede(perfil, permiso, t, quien)]
    if negados:
        return 403, {"error": "tu perfil no puede hacer eso con %s" % ("ese tema" if len(negados) == 1 else "%d de esos temas" % len(negados))}
    hechos, avisos = [], []
    if op == "confirmar":
        malos = [t for t in temas if t["fiabilidad"] == "sin_confirmar"]
        if malos:
            return 409, {"error": "hay %d tema(s) sin confirmar: busca antes una fuente mejor" % len(malos)}
        hoy = CO.hoy_madrid()
        for t in temas:
            if t["estado"] not in CO.ESTADOS_COLA:
                continue
            e = _cola_encargo(ses, t)
            BD.actualizar("cola_temas", {"id": "eq.%s" % t["id"]}, {"estado": "confirmado", "actualizado_at": _ahora_iso(),
                                                                  "historial": _hist(t, quien, "confirmado: encargo %s a la redacción" % e["id"])})
            hechos.append(t["id"])
            if not CO.laborable(hoy) and (t.get("importancia") or 0) >= 5:
                st, r = lanzar_barrido(ses, "Tema confirmado en la cola (importancia 5): %s" % t["titulo"][:200])
                avisos.append(("batida de grandes noticias encargada: empieza en la próxima pasada (11:00 o 17:30)" if r.get("cola") else "batida de grandes noticias lanzada")
                               if st == 200 else "no pude lanzar la batida: %s" % r.get("error"))
        if not CO.laborable(hoy) and not avisos:
            avisos.append("hoy no es laborable: la redacción lo escribe el próximo laborable")
    elif op == "importancia":
        delta = int(d.get("delta") or 0)
        motivo = str(d.get("motivo") or "").strip()[:500] or None
        for t in temas:
            de = t.get("importancia") or t.get("importancia_agente") or 3
            a = max(1, min(5, de + delta)) if delta else max(1, min(5, int(d.get("valor") or de)))
            if a == de:
                continue
            BD.actualizar("cola_temas", {"id": "eq.%s" % t["id"]}, {"importancia": a, "actualizado_at": _ahora_iso(),
                                                                  "historial": _hist(t, quien, "importancia %s → %s%s" % (de, a, (": " + motivo) if motivo else ""))})
            BD.insertar("cola_correcciones", {"tema": t["id"], "titulo": t["titulo"], "de": de, "a": a, "agente": t.get("importancia_agente"), "motivo": motivo,
                                              "quien": quien, "etiquetas": {k: t.get(k) for k in ("medio", "modos", "temas", "territorios", "fiabilidad")}})
            hechos.append(t["id"])
    elif op == "editar":
        t = temas[0]
        c = d.get("campos") or {}
        try:
            n = CO.normalizar(dict(t, **{k: c[k] for k in c if k in ("titulo", "resumen") + CO.CAMPOS_ETIQUETA}), rutina=t.get("rutina"))
        except ValueError as e:
            return 400, {"error": str(e)}
        cambios = {k: n[k] for k in ("titulo", "resumen") + CO.CAMPOS_ETIQUETA if k in c}
        if perfil == "comercial":
            cambios.pop("solucion", None)
        cambios.update(actualizado_at=_ahora_iso(), historial=_hist(t, quien, "editado: " + ", ".join(sorted(k for k in cambios if k not in ("actualizado_at",)))))
        BD.actualizar("cola_temas", {"id": "eq.%s" % t["id"]}, cambios)
        hechos.append(t["id"])
    elif op == "seccion":
        sec = d.get("seccion")
        if sec not in CO.SECCIONES:
            return 400, {"error": "sección desconocida"}
        for t in temas:
            BD.actualizar("cola_temas", {"id": "eq.%s" % t["id"]}, {"seccion": sec, "actualizado_at": _ahora_iso(), "historial": _hist(t, quien, "sección: " + sec)})
            hechos.append(t["id"])
    elif op in ("archivar", "papelera"):
        destino = "archivado" if op == "archivar" else "papelera"
        for t in temas:
            if t["estado"] in ("publicado", destino):
                continue
            BD.actualizar("cola_temas", {"id": "eq.%s" % t["id"]}, {"estado": destino, "estado_antes": t["estado"], "actualizado_at": _ahora_iso(),
                                                                  "historial": _hist(t, quien, "al archivo" if op == "archivar" else "a la papelera")})
            hechos.append(t["id"])
    elif op == "recuperar":
        for t in temas:
            if t["estado"] not in ("archivado", "papelera"):
                continue
            vuelve = t.get("estado_antes") if t.get("estado_antes") in CO.ESTADOS_COLA else "nuevo"
            BD.actualizar("cola_temas", {"id": "eq.%s" % t["id"]}, {"estado": vuelve, "estado_antes": t["estado"], "actualizado_at": _ahora_iso(),
                                                                  "fecha_limite": None if t["estado"] == "archivado" and (t.get("motivo") or "").startswith("caducado") else t.get("fecha_limite"),
                                                                  "historial": _hist(t, quien, "recuperado")})
            hechos.append(t["id"])
    BD.registrar(quien, "cola_" + op, ",".join(map(str, hechos))[:200], {"n": len(hechos)})
    return 200, {"ok": True, "hechos": hechos, "avisos": avisos}


# ---------- panel SEO y asistentes de IA (cambio panel-seo-llm, 16-11-2026; migración 014, src/seo.py) ----------
def seo_panel():
    v = vertical()
    cfg = v.get("seo") or {}
    out = {"propuestas": SEO.propuestas(n=60), "asesor": SEO.asesor_ultimo(), "modelos": cfg.get("modelos") or [],
           "preguntas": cfg.get("preguntas") or [], "marcas": [{"id": m["id"], "nombre": m["nombre"]} for m in cfg.get("marcas") or []],
           "search_console": {"conectado": bool(os.environ.get("GSC_CLIENT_EMAIL") and os.environ.get("GSC_PRIVATE_KEY")),
                              "pasos": (cfg.get("search_console") or {}).get("pasos") or []},
           "rondas": [], "cambios": []}
    if BD.configurada():
        try:
            filas = BD.leer("seo_llm", select="ronda,modelo,pregunta_n,pregunta,cita_moticias,marcas,error,citas", order="ronda.desc", limit="400")
            rondas = sorted({f["ronda"] for f in filas}, reverse=True)[:2]
            for r in rondas:
                fs = [f for f in filas if f["ronda"] == r]
                out["rondas"].append({"ronda": r, "resumen": SEO.resumen(fs), "detalle": fs if r == rondas[0] else None})
            out["cambios"] = BD.leer("seo_cambios", select="id,pieza,tipo,antes,despues,estado,quien,creado_at", order="creado_at.desc", limit="40")
        except BD.ErrorBD as e:
            out["error_bd"] = str(e)
    return out


def _seo_aplicar(ses, pid, tipo, valor, antes=None, nota=None):
    """Escribe el campo SEO en la pieza (commit), la republica en Ghost y lo registra para poder deshacerlo."""
    ruta = _ruta_pieza(pid)
    a, sha = leer(ruta)
    if not a:
        return 404, {"error": "pieza no encontrada"}
    previo = a.get(tipo)
    if valor in (None, "", []):
        a.pop(tipo, None)
    else:
        a[tipo] = valor
    ok, det = escribir(ruta, a, sha, "SEO: %s de %s (%s)" % (tipo, pid, ses["nombre"]))
    if not ok:
        return 502, {"error": det}
    g_ok, g = _subir(a, vertical())
    fila = None
    try:
        fila = BD.insertar("seo_cambios", {"pieza": pid, "tipo": tipo, "antes": previo if antes is None else antes, "despues": valor, "estado": "aplicado",
                                           "quien": ses["nombre"], "nota": nota})[0]
    except BD.ErrorBD:
        pass
    return 200, {"ok": True, "cambio": fila, "valor": valor, "ghost": {"ok": g_ok, "detalle": g}}


def seo_accion(ses, d, cab):
    op = d.get("op")
    if op == "ia":  # «Hazlo con IA» para un título, una descripción o las relacionadas: se aplica directo y se puede deshacer
        pid, tipo = str(d.get("pieza") or ""), d.get("tipo")
        if tipo not in ("seo_title", "seo_description", "relacionadas"):
            return 400, {"error": "esa propuesta toca el texto: se hace con vista previa desde el editor de la pieza"}
        a, _ = leer(_ruta_pieza(pid))
        if not a:
            return 404, {"error": "pieza no encontrada"}
        if tipo == "relacionadas":
            valor = SEO.relacionadas(pid)
            if not valor:
                return 409, {"error": "no encuentro piezas relacionadas de verdad (comparten poco): mejor no forzarlo"}
        else:
            clave = SEO._clave(cab)
            if not clave:
                return 503, {"error": "la IA no está disponible en el gestor (falta la clave de la pasarela)"}
            try:
                valor = SEO.proponer_ia(a, tipo, clave)
            except ValueError as e:
                return 409, {"error": str(e)}
            except (urllib.error.URLError, urllib.error.HTTPError) as e:
                return 502, {"error": "la IA no contestó: %s" % e}
        return _seo_aplicar(ses, pid, tipo, valor, nota="Hazlo con IA")
    if op in ("deshacer", "editar"):
        try:
            c = BD.leer("seo_cambios", select="id,pieza,tipo,antes,despues,estado", id="eq.%s" % int(d.get("id") or 0))[0]
        except (BD.ErrorBD, IndexError, ValueError):
            return 404, {"error": "cambio no encontrado"}
        if op == "deshacer":
            st, r = _seo_aplicar(ses, c["pieza"], c["tipo"], c.get("antes"), antes=c.get("despues"), nota="deshace el cambio %s" % c["id"])
            if st == 200:
                BD.actualizar("seo_cambios", {"id": "eq.%s" % c["id"]}, {"estado": "deshecho", "cambiado_at": datetime.datetime.now(datetime.timezone.utc).isoformat()})
            return st, r
        valor = d.get("valor")
        lim = ((vertical().get("seo") or {}).get("limites") or {}).get(c["tipo"])
        if c["tipo"] in ("seo_title", "seo_description"):
            valor = " ".join(str(valor or "").split())
            if not valor or (lim and len(valor) > lim):
                return 400, {"error": "tiene que tener entre 1 y %s caracteres" % lim}
        return _seo_aplicar(ses, c["pieza"], c["tipo"], valor, nota="editado a mano")
    if op == "bateria":  # un modelo por llamada (cada llamada cabe en el tiempo de una función)
        return seo_bateria(d.get("modelo"), SEO._clave(cab))
    return 400, {"error": "acción desconocida"}


def seo_bateria(modelo=None, clave=None):
    """Pasa la batería de preguntas a un modelo (o al siguiente que falte en la ronda de esta semana) y la guarda en seo_llm."""
    if not BD.configurada():
        return 503, {"error": "la base privada no está conectada"}
    clave = clave or SEO._clave()
    if not clave:
        return 503, {"error": "falta la clave de la pasarela de IA"}
    cfg = vertical().get("seo") or {}
    hoy = datetime.date.today()
    ronda = (hoy - datetime.timedelta(days=(hoy.weekday() + 1) % 7)).isoformat()  # la ronda es la del domingo de la semana
    modelos = cfg.get("modelos") or []
    if not modelo:
        hechos = {f["modelo"] for f in BD.leer("seo_llm", select="modelo", ronda="eq." + ronda, limit="500")}
        pend = [m for m in modelos if m["id"] not in hechos]
        if not pend:
            return 200, {"ok": True, "ronda": ronda, "nada": "la ronda de esta semana ya está completa"}
        m = pend[0]
    else:  # a mano («Pasar la batería ahora»): la ronda es la de hoy y no se repite un modelo ya preguntado hoy
        m = next((x for x in modelos if x["id"] == modelo), None)
        if not m:
            return 400, {"error": "modelo desconocido"}
        ronda = hoy.isoformat()
        if BD.leer("seo_llm", select="id", ronda="eq." + ronda, modelo="eq." + m["id"], limit="1"):
            return 200, {"ok": True, "ronda": ronda, "nada": "%s ya se preguntó hoy" % m["nombre"]}
    from concurrent.futures import ThreadPoolExecutor
    pregs = cfg.get("preguntas") or []
    def una(iq):
        filas = []
        SEO.bateria(clave, ronda, [m], [iq[1]], guardar=filas.append)
        f = filas[0]
        f["pregunta_n"] = iq[0]
        return f
    with ThreadPoolExecutor(max_workers=6) as ex:
        filas = list(ex.map(una, list(enumerate(pregs, 1))))
    try:
        BD.insertar("seo_llm", filas)
    except BD.ErrorBD as e:
        return 502, {"error": str(e)}
    return 200, {"ok": True, "ronda": ronda, "modelo": m["id"], "resumen": SEO.resumen(filas)}


# ---------- agenda de eventos (cambio agenda-de-eventos, 16-11-2026; src/agenda_gestor.py, src/ghost_agenda.py) ----------
def _eventos_actuales(cambiados=None):
    """Eventos del despliegue, con los recién cambiados desde el gestor encima (aún no están en este despliegue)."""
    import eventos as EV
    evs = {e["id"]: EV.limpio(e) for e in EV.cargar()}
    for e in cambiados or []:
        evs[e["id"]] = e
    return list(evs.values())


def agenda_republicar(cambiados):
    """Tras publicar, retirar o cambiar eventos en el gestor: rehace moticias.com/agenda/ (y sus fichas) al momento."""
    import ghost_agenda as GA
    url, key = os.environ.get("GHOST_URL"), os.environ.get("GHOST_ADMIN_KEY")
    if not url or not key:
        return {"ok": False, "detalle": "faltan las claves de Ghost; la pondrá al día el cron ghost_al_dia"}
    try:
        r = GA.publicar(_eventos_actuales(cambiados), vertical(), url, key)
        return {"ok": all(x in (200, 201) for x in r["paginas"].values()), "detalle": r}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "detalle": str(e)[:300]}


def agenda_al_dia():
    """Cron ghost_al_dia: si los eventos del despliegue o el día cambiaron desde la última vez, rehace la agenda en Ghost.
    La huella va en la propia página (data-huella), así que no hace falta guardar nada más."""
    import eventos as EV
    import ghost_agenda as GA
    url, key = os.environ.get("GHOST_URL"), os.environ.get("GHOST_ADMIN_KEY")
    if not url or not key:
        return {"ok": False, "error": "faltan GHOST_URL o GHOST_ADMIN_KEY"}
    evs = _eventos_actuales()
    huella = GA.huella(evs)
    base, tok = G.admin_base(url.rstrip("/")), G.ghost_token(key)
    st, r = G.api("GET", base + "/ghost/api/admin/pages/slug/agenda/?formats=html&fields=id,html", tok)
    actual = ((r or {}).get("pages") or [{}])[0].get("html", "") if st == 200 else ""
    rutas = GA.rutas_activas(url, key)
    if ('data-huella="%s"' % huella) in actual and ('data-rutas="%d"' % rutas) in actual:
        return {"ok": True, "al_dia": True}
    res = GA.publicar(evs, vertical(), url, key)
    return {"ok": all(x in (200, 201) for x in res["paginas"].values()), "publicado": res}


def inicio(ses):
    """Pantalla «Inicio»: el bloque «Agenda» completo y, de las demás áreas, las cifras que el gestor ya calcula."""
    per = ses["permisos"]
    out = {"agenda": AG.panel(), "areas": {}}
    a = out["areas"]
    try:
        ps = piezas(14)
        a["piezas_pendientes"] = sum(1 for p in ps if p.get("status") == "pendiente")
        a["cajas_propuestas"] = sum(1 for p in ps for m in p.get("menciones") or [] if m.get("estado") == "propuesta")
    except Exception:  # noqa: BLE001
        pass
    try:
        a["retoques_abiertos"] = sum(1 for r in RT.cargar_todos() if r.get("estado") in ("pendiente", "en_curso"))
    except Exception:  # noqa: BLE001
        pass
    if BD.configurada():
        for k, f in (("cola_nuevos", lambda: len(BD.leer("cola_temas", select="id", estado="in.(nuevo,propuesto)", limit="500"))),
                     ("pasos_hoy", lambda: len(BD.leer("crm_pasos", select="id", hecho_at="is.null", fecha="lte." + datetime.date.today().isoformat(), limit="500")) if "crm" in per else None),
                     ("publicidad_caidos", lambda: len({x["anuncio"] for x in BD.leer("pub_comprobaciones", select="anuncio,ok", at="gte." + (datetime.date.today() - datetime.timedelta(days=1)).isoformat(), ok="eq.false", limit="500")}))):
            try:
                val = f()
                if val is not None:
                    a[k] = val
            except BD.ErrorBD:
                pass
    return out


# ---------- buzón del repositorio (14-11-2026; migración 008, src/buzon.py) ----------
# Las tareas programadas que no pueden hacer push dejan en Supabase (tabla repo_buzon) los ficheros que cambian. Este
# cron los sube a `main` con GITHUB_TOKEN: un commit por lote, en orden de llegada, y se para en el primer lote que no
# encaja para no aplicar lo que dependa de él. Solo contenido (BUZON_RUTAS); nunca borra ficheros ni toca código.
BUZON_RUTAS = ("data/", "docs/ediciones.md", "docs/fuentes.md", "docs/asesor/", "portal/img/")
BUZON_ESPERA_H = 6  # un lote al que le faltan partes se da por perdido pasadas estas horas


def _blob_sha(datos):
    return hashlib.sha1(b"blob %d\0" % len(datos) + datos).hexdigest()


def _commit_lote(ficheros, mensaje, autor, correo, rutas=None, comprobar_base=True):
    """Un solo commit en BRANCH con los ficheros del lote. Devuelve (True, sha) o (False, motivo)."""
    for intento in (1, 2):
        st, ref = gh("GET", "git/ref/heads/%s" % BRANCH)
        if st != 200:
            return False, "GitHub no da la rama %s (%s): %s" % (BRANCH, st, ref.get("message"))
        head = ref["object"]["sha"]
        st, com = gh("GET", "git/commits/%s" % head)
        if st != 200:
            return False, "GitHub no da el commit %s (%s)" % (head[:7], st)
        st, arbol = gh("GET", "git/trees/%s?recursive=1" % com["tree"]["sha"])
        if st != 200 or arbol.get("truncated"):
            return False, "GitHub no da el árbol completo de %s (%s)" % (head[:7], st)
        en_main = {e["path"]: e["sha"] for e in arbol.get("tree", []) if e.get("type") == "blob"}
        nuevos = []
        for f in ficheros:
            ruta = str(f.get("ruta") or "")
            if not ruta.startswith(rutas or BUZON_RUTAS) or ".." in ruta.split("/"):
                return False, "ruta no permitida en el buzón: %s" % ruta
            if "texto" in f:
                datos = str(f["texto"]).encode("utf-8")
            elif "base64" in f:
                try:
                    datos = base64.b64decode(f["base64"], validate=True)
                except Exception:
                    return False, "base64 no válido en %s" % ruta
            else:
                return False, "fichero sin contenido: %s" % ruta
            actual, base = en_main.get(ruta), f.get("base") or None
            if actual == _blob_sha(datos):
                continue  # ya está en main tal cual
            if comprobar_base and actual != base:
                return False, "conflicto en %s: main tiene %s y el lote partía de %s" % (ruta, (actual or "nada")[:7], (base or "nada")[:7])
            if "texto" in f:
                nuevos.append({"path": ruta, "mode": "100644", "type": "blob", "content": f["texto"]})
            else:
                st, b = gh("POST", "git/blobs", {"content": f["base64"], "encoding": "base64"})
                if st != 201:
                    return False, "GitHub no acepta el fichero %s (%s)" % (ruta, st)
                nuevos.append({"path": ruta, "mode": "100644", "type": "blob", "sha": b["sha"]})
        if not nuevos:
            return True, head  # todo estaba ya en main
        st, t = gh("POST", "git/trees", {"base_tree": com["tree"]["sha"], "tree": nuevos})
        if st != 201:
            return False, "GitHub no crea el árbol (%s): %s" % (st, t.get("message"))
        st, c = gh("POST", "git/commits", {"message": mensaje, "tree": t["sha"], "parents": [head],
                                           "author": {"name": autor, "email": correo}})
        if st != 201:
            return False, "GitHub no crea el commit (%s): %s" % (st, c.get("message"))
        st, r = gh("PATCH", "git/refs/heads/%s" % BRANCH, {"sha": c["sha"], "force": False})
        if st == 200:
            return True, c["sha"]
        if st != 422 or intento == 2:
            return False, "GitHub no mueve %s (%s): %s" % (BRANCH, st, r.get("message"))
    return False, "main cambió dos veces mientras se aplicaba el lote"


def aplicar_buzon():
    if not BD.configurada():
        return {"ok": False, "error": "falta la base del gestor (SUPABASE_URL, SUPABASE_ANON_KEY, MOTICIAS_BD_CLAVE)"}
    if not os.environ.get("GITHUB_TOKEN"):
        return {"ok": False, "error": "falta GITHUB_TOKEN en Vercel"}
    try:
        filas = BD.leer("repo_buzon", estado="eq.pendiente", order="creado_at.asc,parte.asc",
                        select="id,creado_at,lote,parte,partes,origen,mensaje,autor,autor_correo,ficheros")
    except BD.ErrorBD as e:
        return {"ok": False, "error": str(e)}
    lotes = {}
    for f in filas:  # en orden de llegada del primer trozo de cada lote
        lotes.setdefault(f["lote"], []).append(f)
    ahora = datetime.datetime.now(datetime.timezone.utc)
    hechos = []
    for lote, partes in lotes.items():
        n = max(p["partes"] for p in partes)
        ids = {"id": "in.(%s)" % ",".join(p["id"] for p in partes)}
        if len({p["parte"] for p in partes}) < n:
            primero = min(datetime.datetime.fromisoformat(p["creado_at"].replace("Z", "+00:00")) for p in partes)
            if (ahora - primero).total_seconds() > BUZON_ESPERA_H * 3600:
                BD.actualizar("repo_buzon", ids, {"estado": "error", "error": "lote incompleto: llegaron %d de %d partes" % (len(partes), n)})
                hechos.append({"lote": lote, "ok": False, "error": "incompleto"})
                continue
            hechos.append({"lote": lote, "ok": None, "espera": "%d de %d partes" % (len(partes), n)})
            break  # lo que venga después puede depender de este lote
        partes.sort(key=lambda p: p["parte"])
        ficheros = [x for p in partes for x in (p["ficheros"] or [])]
        ok, res = _commit_lote(ficheros, partes[0]["mensaje"], partes[0]["autor"], partes[0]["autor_correo"])
        if ok:
            BD.actualizar("repo_buzon", ids, {"estado": "aplicado", "aplicado_at": ahora.isoformat(), "sha": res, "error": None})
            BD.registrar("buzón", "aplicar", lote, {"sha": res[:7], "ficheros": len(ficheros)})
            hechos.append({"lote": lote, "ok": True, "sha": res[:7], "ficheros": len(ficheros)})
        else:
            BD.actualizar("repo_buzon", ids, {"estado": "error", "error": res[:500]})
            hechos.append({"lote": lote, "ok": False, "error": res})
            break
    return {"ok": all(h.get("ok") is not False for h in hechos), "lotes": hechos}


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
            ag = []
            if datetime.date.today().weekday() < 5 and BD.configurada():  # agenda: enlaces de inscripción, cada día laborable
                try:
                    ag = AG.comprobar_enlaces(origen="agente", azar=True)
                except Exception:  # noqa: BLE001 — la agenda nunca tumba el comprobador de la publicidad
                    ag = []
            return self._enviar(200, {"comprobados": len(r), "fallos": [x["anuncio"] for x in r if not x["ok"]],
                                      "agenda": {"comprobados": len(ag), "caidos": [x["evento_id"] for x in ag if not x["ok"]]}})
        if a == "ghost_al_dia":  # Vercel Cron (todos los días, cada 15 min de 7 a 20; desde el 14-11 también fines de semana, por las ediciones extra): publica en moticias.com la edición que falte
            sec = os.environ.get("CRON_SECRET")
            if not sec or not hmac.compare_digest(self.headers.get("Authorization") or "", "Bearer " + sec):
                return self._enviar(401, {"error": "solo el cron"})
            r = ghost_al_dia()
            try:
                r["agenda"] = agenda_al_dia()
            except Exception as e:  # noqa: BLE001
                r["agenda"] = {"ok": False, "error": str(e)[:300]}
            try:
                r["indice"] = indice_al_dia()
                if not r["indice"].get("cambiado") and not r.get("publicadas"):  # índice servido ya al día: comprobar secciones
                    r["secciones"] = secciones_vigilar()
            except Exception as e:  # la comprobación nunca hace fallar la publicación
                r["secciones_error"] = str(e)[:300]
            return self._enviar(200, r)
        if a == "web_reintentos":  # Vercel Cron (cada 20 min, todos los días): vuelve a subir a Ghost lo aprobado que no llegó
            sec = os.environ.get("CRON_SECRET")
            if not sec or not hmac.compare_digest(self.headers.get("Authorization") or "", "Bearer " + sec):
                return self._enviar(401, {"error": "solo el cron"})
            r = reintentar_subidas()
            try:  # y, de paso, que el resumen de cada post en Ghost sea la entradilla de su pieza (nunca tumba los reintentos)
                r["entradillas"] = entradillas_al_dia()
            except Exception as e:  # noqa: BLE001
                r["entradillas"] = {"ok": False, "detalle": str(e)[:300]}
            return self._enviar(200, r)
        if a == "copias_vigilar":  # Vercel Cron (diario): ¿hay copia reciente del Mac? Si no, correo a Rainer
            sec = os.environ.get("CRON_SECRET")
            if not sec or not hmac.compare_digest(self.headers.get("Authorization") or "", "Bearer " + sec):
                return self._enviar(401, {"error": "solo el cron"})
            return self._enviar(200, copias_vigilar())
        if a == "seo_bateria":  # Vercel Cron (domingos, cuatro pasadas): un modelo de la batería de asistentes por pasada
            sec = os.environ.get("CRON_SECRET")
            if not sec or not hmac.compare_digest(self.headers.get("Authorization") or "", "Bearer " + sec):
                return self._enviar(401, {"error": "solo el cron"})
            st, r = seo_bateria(None, SEO._clave(self._cab()))
            return self._enviar(st, r)
        if a == "aplicar_buzon":  # Vercel Cron (cada 10 min): sube a main lo que las tareas dejaron en el buzón (migración 008)
            sec = os.environ.get("CRON_SECRET")
            if not sec or not hmac.compare_digest(self.headers.get("Authorization") or "", "Bearer " + sec):
                return self._enviar(401, {"error": "solo el cron"})
            return self._enviar(200, aplicar_buzon())
        if a == "publicidad":  # pública: la pide el script de moticias.com
            return self._enviar(200, publicidad_publica(), cors="*", cache="public, max-age=120, s-maxage=300, stale-while-revalidate=3600")
        if a == "prensa_baja":  # pública: enlace de baja de cada envío de prensa (firmado)
            ok = False
            try:
                ok = PR.baja(q.get("p", ""), q.get("f", ""))
            except BD.ErrorBD:
                pass
            txt = ("Hecho: no volverá a recibir correos de MOTICIAS." if ok else "El enlace no es válido. Escriba a redaccion@moticias.com y le daremos de baja.")
            b = ("<!DOCTYPE html><meta charset=utf-8><meta name=viewport content='width=device-width'><meta name=robots content=noindex>"
                 "<title>MOTICIAS</title><p style='font:18px/1.5 Georgia,serif;max-width:560px;margin:15vh auto;padding:0 20px'>%s</p>" % txt).encode()
            self.send_response(200 if ok else 400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("X-Robots-Tag", "noindex")
            self.end_headers()
            self.wfile.write(b)
            return
        if a == "prensa_cron":  # Vercel Cron (miércoles): suscriptores en Ghost, estados de Brevo y recálculo
            sec = os.environ.get("CRON_SECRET")
            if not sec or not hmac.compare_digest(self.headers.get("Authorization", ""), "Bearer " + sec):
                return self._enviar(401, {"error": "solo el cron"})
            return self._enviar(200, prensa_cron())
        if a == "yo":
            origen = self.headers.get("Origin")
            if origen == ORIGEN_SITIO:  # desde moticias.com: solo «¿es el editor jefe?»; nada más sale de aquí
                jefe = bool(ses and "redaccion" in ses["permisos"])
                return self._enviar(200, {"jefe": jefe, "gestor": self._base() + "/gestor/"}, cors=origen,
                                    cookie=None if jefe else cookie_marca(False, self._host()))
            cab = self._cab()
            r = {"rol": ses and ses["perfil"], "nombre": ses and ses["nombre"], "permisos": ses and ses["permisos"],
                 "configurado": bool(_claves()["superadmin"]), "escritura": bool(os.environ.get("GITHUB_TOKEN")),
                 "ghost": bool(os.environ.get("GHOST_ADMIN_KEY")), "oficina": bool(_claves()["oficina"]), "bd": BD.configurada(), "barrido": bool(os.environ.get("RUTINA_BARRIDO_TOKEN")), "brevo": bool(os.environ.get("BREVO_API_KEY")),
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
            if a in ("restaurables", "versiones", "version", "copia_fechas", "copia_diferencias"):
                if "restaurar" not in per:
                    return self._enviar(403, {"error": "tu perfil no restaura"})
                if a == "restaurables":
                    return self._enviar(200, {"documentos": restaurables(q.get("q")), "tablas": RS.tablas_permitidas(ses["perfil"], vertical())})
                if a == "versiones":
                    return self._enviar(*versiones(ses, q.get("ruta", "")))
                if a == "version":
                    return self._enviar(*version(ses, q.get("ruta", ""), q.get("sha", "")))
                if not BD.configurada():
                    return self._enviar(503, {"error": "la base privada no está conectada"})
                if a == "copia_fechas":
                    return self._enviar(*copia_rpc("copia_fechas", {}))
                if q.get("tabla") not in RS.tablas_permitidas(ses["perfil"], vertical()):
                    return self._enviar(403, {"error": "tu perfil no recupera datos de esa tabla"})
                return self._enviar(*copia_rpc("copia_diferencias", {"p_tabla": q.get("tabla"), "p_fecha": q.get("fecha"), "p_limite": 200}))
            if a == "copias":
                if "equipo" not in per:
                    return self._enviar(403, {"error": "solo el editor jefe ve las copias de seguridad"})
                return self._enviar(200, copias_resumen())
            if a == "comprobaciones_csv":  # historial auditable de un enlace (cambio comprobador-diario)
                if "publicidad" not in per and "contratos" not in per:
                    return self._enviar(403, {"error": "tu perfil no ve el seguimiento de la publicidad"})
                if not S.ID_OK.match(q.get("anuncio", "")) or not BD.configurada():
                    return self._enviar(400, {"error": "¿qué caja?"})
                csv = S.comprobaciones_csv(q["anuncio"], int(q.get("dias") or 30))
                b = csv.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/csv; charset=utf-8")
                self.send_header("Content-Disposition", 'attachment; filename="comprobaciones-%s.csv"' % re.sub(r"[^a-z0-9-]", "-", q["anuncio"]))
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(b)))
                self.end_headers()
                self.wfile.write(b)
                return
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
            if a == "cola":
                return self._enviar(*cola_listar(ses, q.get("pestana") or "cola"))
            if a == "seo":
                if "equipo" not in per:
                    return self._enviar(403, {"error": "el panel SEO es del editor jefe"})
                return self._enviar(200, seo_panel())
            if a == "voz":
                if "redaccion" not in per:
                    return self._enviar(403, {"error": "solo el editor jefe aprueba «La voz del editor»"})
                return self._enviar(200, {"propuestas": voz_propuestas(), "lunes": proximo_lunes_8(), "publicadas": voz_publicadas(),
                                          "sin_web": subidas_fallidas(),
                                          "encargos": voz_encargos(), "palabras": _voz_cfg().get("palabras") or [700, 1100],
                                          "pagina": "https://%s%s" % (vertical().get("domain", "www.moticias.com"), _voz_cfg().get("pagina") or "/la-voz-del-editor/")})
            if a == "agenda":  # pestaña «Agenda»: cola, publicados, por confirmar y retirados (todos los perfiles la ven; publica el editor jefe)
                if "proponer" not in per and "piezas" not in per:
                    return self._enviar(403, {"error": "tu perfil no ve la agenda"})
                v = vertical()
                return self._enviar(200, dict(AG.estado_de_cola(), cfg={k: v["agenda"][k] for k in ("temas", "formatos", "modalidades", "publicos", "estados")},
                                              territorios=[{"id": t["id"], "nombre": t["nombre"]} for t in v["taxonomia"]["territorios"] if t.get("tipo") == "ccaa"],
                                              jefe="piezas" in per, bd=BD.configurada()))
            if a == "agenda_organizadores":
                if "crm" not in per:
                    return self._enviar(403, {"error": "tu perfil no entra en el CRM"})
                if not BD.configurada():
                    return self._enviar(503, {"error": "la base privada no está conectada"})
                return self._enviar(200, AG.organizadores())
            if a == "agenda_envio":
                if not BD.configurada() or "proponer" not in per and "piezas" not in per:
                    return self._enviar(403, {"error": "sin acceso"})
                r = BD.leer("agenda_envios", select="*", id="eq." + q.get("id", "")[:40], limit="1")
                return self._enviar(200 if r else 404, r[0] if r else {"error": "no encontrado"})
            if a == "inicio":  # pantalla «Inicio» del gestor: actividad de todas las áreas (decisión 2 de agenda-de-eventos)
                return self._enviar(200, inicio(ses))
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
            if a in ("prensa_resumen", "prensa_medios", "prensa_medio", "prensa_envio", "prensa_destinatarios"):
                if "crm" not in per:
                    return self._enviar(403, {"error": "tu perfil no entra en prensa"})
                if not BD.configurada():
                    return self._enviar(503, {"error": "la base privada aún no está conectada"})
                if a == "prensa_resumen":
                    return self._enviar(200, dict(PR.resumen(), brevo=bool(os.environ.get("BREVO_API_KEY")), ghost=bool(os.environ.get("GHOST_ADMIN_KEY"))))
                if a == "prensa_medios":
                    return self._enviar(200, {"medios": PR.medios(q)})
                if a == "prensa_medio":
                    r = PR.ficha(q.get("id", ""))
                    return self._enviar(200 if r else 404, r or {"error": "medio no encontrado"})
                if a == "prensa_envio":
                    r = PR.envio(int(q.get("id") or 0))
                    return self._enviar(200 if r else 404, r or {"error": "envío no encontrado"})
                lista = PR.destinatarios(json.loads(q.get("filtro") or "{}"), q.get("tipo") or "nota_de_prensa")
                return self._enviar(200, {"n": len(lista), "muestra": lista[:40]})
        except BD.ErrorBD as e:
            return self._enviar(502, {"error": str(e)})
        return self._enviar(404, {"error": "acción desconocida"})

    def do_POST(self):
        q, ses = self._q(), self._ses()
        a = q.get("a")
        try:
            n = int(self.headers.get("Content-Length") or 0)
            d = json.loads(self.rfile.read(min(n, 6000000 if a == "anuncio_imagen" else 400000)) or b"{}") if n else {}
        except (ValueError, json.JSONDecodeError):
            return self._enviar(400, {"error": "JSON no válido"})
        if a == "copia":  # el Mac anota una copia o una prueba (token propio; solo fecha, tamaños, huellas y recuentos)
            if not BD.configurada():
                return self._enviar(503, {"error": "la base privada no está conectada"})
            datos = {k: d.get(k) for k in ("clase", "ok", "inicio", "equipo", "partes", "error")}
            try:
                fila = BD.peticion("POST", "rpc/copia_anotar", cuerpo={"p_token": str(d.get("token") or ""), "p_datos": datos})
            except BD.ErrorBD as e:
                time.sleep(1)
                return self._enviar(403 if "token" in str(e) else 502, {"error": str(e)[:200]})
            return self._enviar(200, {"ok": True, "id": fila})
        if a == "evento":  # pública: visualizaciones y clics que manda el script de moticias.com (sendBeacon, texto plano)
            S.evento(d, self.headers.get("User-Agent"))
            S.evento_ampliado(d, self.headers.get("User-Agent"))
            return self._enviar(204, {}, cors="*")
        if a == "formulario":  # pública: «Pide más información» de un banner (cambio banner-premium)
            st, r = formulario_publico(d, self.headers.get("User-Agent"), self.headers.get("x-forwarded-for", "").split(",")[0].strip())
            return self._enviar(st, r, cors="*")
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
            r = republicar_y_marcar(d.get("id"))
            BD.registrar(ses["nombre"], "republicar", d.get("id"), {"ghost": r["ok"], "detalle": str(r["detalle"])[:500]})
            return self._enviar(200, r)
        if a == "republicar_pendientes":
            ids = [p["id"] for p in piezas(60) if pendiente_web(p)]
            res = [dict(republicar_y_marcar(i), id=i) for i in ids[:15]]
            return self._enviar(200, {"ok": all(r["ok"] for r in res), "piezas": res, "quedan": max(0, len(ids) - 15)})
        if a == "voz":  # escribir o encargar una columna de «La voz del editor»: solo el editor jefe
            if "redaccion" not in per:
                return self._enviar(403, {"error": "solo el editor jefe escribe o encarga «La voz del editor»"})
            return self._enviar(*accion_voz(ses, d))
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
        if a == "agenda":
            return self._enviar(*AG.accion(ses, d, {"leer": leer, "escribir": escribir, "republicar": agenda_republicar,
                                                    "correo": lambda para, asunto, cuerpo: M.enviar_correo(asunto, cuerpo, para, M.remitentes_avisos(vertical()))[0]}))
        if a == "cola":
            return self._enviar(*cola_accion(ses, d))
        if a == "seo":
            if "equipo" not in ses["permisos"]:
                return self._enviar(403, {"error": "el panel SEO es del editor jefe"})
            return self._enviar(*seo_accion(ses, d, self._cab()))
        if a == "anuncio_imagen":
            return self._enviar(*subir_imagen_anuncio(ses, d))
        if a == "dominio":
            return self._enviar(*accion_dominio(ses, d))
        if a == "probar_aviso":  # diagnóstico: manda un correo de prueba al editor jefe y enseña lo que contesta Brevo
            if "equipo" not in per:
                return self._enviar(403, {"error": "solo el editor jefe"})
            v = vertical()
            para = (v.get("productos") or {}).get("email") or []
            ok, det = M.enviar_correo("MOTICIAS · correo de prueba de los avisos", "<p>Si lees esto, los avisos del gestor llegan.</p>", para, M.remitentes_avisos(v))
            return self._enviar(200, {"ok": ok, "detalle": det[:300], "para": para, "remitentes": [r[0] for r in M.remitentes_avisos(v)]})
        if a in ("restaurar_version", "copia_recuperar"):
            if "restaurar" not in per:
                return self._enviar(403, {"error": "tu perfil no restaura"})
            if a == "restaurar_version":
                return self._enviar(*restaurar_version(ses, d))
            if not BD.configurada():
                return self._enviar(503, {"error": "la base privada no está conectada"})
            return self._enviar(*copia_recuperar(ses, d))
        if a == "prensa":
            if "crm" not in per:
                return self._enviar(403, {"error": "tu perfil no entra en prensa"})
            if not BD.configurada():
                return self._enviar(503, {"error": "la base privada aún no está conectada"})
            return self._enviar(*accion_prensa(ses, d, self._base()))
        if a == "miembro":
            if "crm" not in per:
                return self._enviar(403, {"error": "tu perfil no cambia los suscriptores"})
            return self._enviar(*accion_miembro(ses, d))
        if a == "barrido":
            if "barrido" not in per:
                return self._enviar(403, {"error": "tu perfil no lanza barridos de noticias"})
            return self._enviar(*lanzar_barrido(ses, d.get("pista")))
        return self._enviar(404, {"error": "acción desconocida"})
