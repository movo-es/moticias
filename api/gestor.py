"""MOTICIAS · Gestor de patrocinios y publicidad (función de Vercel, Python, solo biblioteca estándar).

Sirve la API de app.moticias.com/gestor/ (la página está en app/public/gestor/index.html). Lee el contenido que viene
con el despliegue (data/, verticals/, src/; Vercel redespliega en cada push) y, para escribir, usa GitHub como fuente de
verdad: lee el fichero fresco, lo cambia y lo guarda con un commit. Después actualiza el post en Ghost si existe.

Variables de entorno (en Vercel, nunca en el repositorio):
  GESTOR_CLAVE_SUPERADMIN   contraseña del superadministrador (todo: menciones, productos, publicidad)
  GESTOR_CLAVE_OFICINA      contraseña del perfil oficina (menciones de las piezas; opcional)
  GITHUB_TOKEN              token de GitHub con permiso de escritura en contenidos de movo-es/moticias
  GHOST_URL, GHOST_ADMIN_KEY  para republicar la pieza al momento (si faltan, la verá la rutina siguiente)
  GITHUB_REPO               opcional, por defecto movo-es/moticias; GITHUB_BRANCH, por defecto main

Rutas: GET/POST /api/gestor?a=<acción>  (yo, entrar, salir, piezas, pieza, mencion, republicar, productos, producto,
anuncios, anuncio). Reglas: openspec/changes/patrocinios-en-linea/.
"""
import base64, datetime, glob, hashlib, hmac, http.cookies, json, os, sys, time, urllib.error, urllib.parse, urllib.request
from http.server import BaseHTTPRequestHandler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import menciones as M  # noqa: E402
import ghost_publish as G  # noqa: E402

REPO = os.environ.get("GITHUB_REPO", "movo-es/moticias")
BRANCH = os.environ.get("GITHUB_BRANCH", "main")
COOKIE = "gestor"
DIAS_SESION = 90
VERTICAL = "movilidad"

# Campos que el superadministrador puede cambiar en un producto y en un anuncio (lista cerrada).
CAMPOS_PRODUCTO = {"modo", "umbral", "exclusividad", "posicion", "max_por_semana", "status", "url", "one_liner", "contexto", "textos", "excluir"}
CAMPOS_ANUNCIO = {"status", "start", "end", "headline", "text", "cta", "url", "weight"}


# ---------- sesión ----------
def _claves():
    return {"superadmin": os.environ.get("GESTOR_CLAVE_SUPERADMIN") or "", "oficina": os.environ.get("GESTOR_CLAVE_OFICINA") or ""}


def _secreto():
    c = _claves()
    # La firma depende de las contraseñas: cambiar una contraseña cierra todas las sesiones abiertas.
    return hashlib.sha256(("moticias-gestor|" + c["superadmin"] + "|" + c["oficina"]).encode()).digest()


def firmar(rol, dias=DIAS_SESION):
    exp = int(time.time()) + dias * 86400
    msg = "%s.%d" % (rol, exp)
    return msg + "." + hmac.new(_secreto(), msg.encode(), hashlib.sha256).hexdigest()


def rol_de(valor):
    try:
        rol, exp, sig = (valor or "").split(".")
        msg = "%s.%s" % (rol, exp)
        if hmac.compare_digest(sig, hmac.new(_secreto(), msg.encode(), hashlib.sha256).hexdigest()) and int(exp) > time.time() and rol in ("superadmin", "oficina"):
            return rol
    except ValueError:
        pass
    return None


# ---------- datos ----------
def vertical():
    return json.load(open(os.path.join(ROOT, "verticals", VERTICAL + ".json"), encoding="utf-8"))


def productos():
    return M.cargar_productos(os.path.join(ROOT, "data"))


def gh(method, path, body=None):
    tok = os.environ.get("GITHUB_TOKEN")
    if not tok:
        return 0, {"message": "falta GITHUB_TOKEN"}
    req = urllib.request.Request("https://api.github.com/repos/%s/%s" % (REPO, path), method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": "Bearer " + tok, "Accept": "application/vnd.github+json",
                                          "User-Agent": "moticias-gestor", "X-GitHub-Api-Version": "2022-11-28"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")
    except urllib.error.URLError as e:
        return 0, {"message": str(e)}


def leer(ruta):
    """Devuelve (objeto, sha). Primero GitHub (fresco); si no hay token, el fichero del despliegue (sha None)."""
    st, r = gh("GET", "contents/%s?ref=%s" % (urllib.parse.quote(ruta), BRANCH))
    if st == 200:
        return json.loads(base64.b64decode(r["content"]).decode("utf-8")), r["sha"]
    p = os.path.join(ROOT, ruta)
    if os.path.exists(p):
        return json.load(open(p, encoding="utf-8")), None
    return None, None


def escribir(ruta, obj, sha, mensaje):
    txt = json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    body = {"message": mensaje + "\n\nGestor de patrocinios (app.moticias.com/gestor/)", "content": base64.b64encode(txt.encode("utf-8")).decode(), "branch": BRANCH}
    if sha:
        body["sha"] = sha
    st, r = gh("PUT", "contents/%s" % urllib.parse.quote(ruta), body)
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
    return r


def accion_mencion(rol, d):
    pid, prod_id, acc = d.get("id"), d.get("producto"), d.get("accion")
    if acc not in ("publicar", "retirar", "proponer", "editar", "anadir", "posicion"):
        return 400, {"error": "acción desconocida"}
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
        if m:  # estaba retirada: se reactiva (nunca se borra; queda en el historial)
            m["estado"] = "publicada"
        else:
            pts, motivos = M.puntuar(a, prod)
            m = M.nueva_mencion(a, prod, pts or 0, ["añadida a mano por %s" % rol] + (motivos if isinstance(motivos, list) else [motivos]), "publicada", origen="manual")
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
            for k in ("texto", "cta"):
                if isinstance(d.get(k), str) and d[k].strip():
                    m[k] = d[k].strip()[:600]
            if d.get("posicion") in M.POSICIONES:
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
        out.append({k: a.get(k) for k in ("id", "name", "advertiser", "type", "label", "status", "start", "end", "slots", "sections", "headline", "text", "cta", "url", "weight", "pricing", "amount_eur")})
    return out


def accion_anuncio(d):
    ruta = "data/ads/%s.json" % d.get("id")
    a, sha = leer(ruta)
    if not a:
        return 404, {"error": "anuncio no encontrado"}
    if sha is None:
        return 503, {"error": "falta GITHUB_TOKEN en Vercel"}
    cambios = {k: val for k, val in (d.get("cambios") or {}).items() if k in CAMPOS_ANUNCIO}
    a.update(cambios)
    a["updated_at"] = datetime.datetime.now().astimezone().isoformat(timespec="minutes")
    ok, det = escribir(ruta, a, sha, "Publicidad %s: %s" % (a["id"], ", ".join(sorted(cambios))))
    return (200, {"ok": True, "commit": det}) if ok else (502, {"error": det})


# ---------- HTTP ----------
class handler(BaseHTTPRequestHandler):
    def _enviar(self, st, obj, cookie=None):
        b = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(st)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Robots-Tag", "noindex")
        if cookie is not None:
            self.send_header("Set-Cookie", cookie)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def _rol(self):
        c = http.cookies.SimpleCookie(self.headers.get("Cookie") or "")
        return rol_de(c[COOKIE].value) if COOKIE in c else None

    def _q(self):
        return {k: v[0] for k, v in urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).items()}

    def do_GET(self):
        q, rol = self._q(), self._rol()
        a = q.get("a", "yo")
        if a == "yo":
            return self._enviar(200, {"rol": rol, "configurado": bool(_claves()["superadmin"]), "escritura": bool(os.environ.get("GITHUB_TOKEN")),
                                      "ghost": bool(os.environ.get("GHOST_ADMIN_KEY")), "oficina": bool(_claves()["oficina"])})
        if not rol:
            return self._enviar(401, {"error": "sin sesión"})
        if a == "piezas":
            return self._enviar(200, {"piezas": piezas(int(q.get("dias") or 14))})
        if a == "pieza":
            r = detalle(q.get("id", ""))
            return self._enviar(200 if r else 404, r or {"error": "pieza no encontrada"})
        if a == "productos":
            return self._enviar(200, {"productos": productos(), "modos": list(M.MODOS)})
        if a == "anuncios":
            return self._enviar(200, {"anuncios": anuncios()})
        return self._enviar(404, {"error": "acción desconocida"})

    def do_POST(self):
        q, rol = self._q(), self._rol()
        a = q.get("a")
        try:
            n = int(self.headers.get("Content-Length") or 0)
            d = json.loads(self.rfile.read(min(n, 200000)) or b"{}") if n else {}
        except (ValueError, json.JSONDecodeError):
            return self._enviar(400, {"error": "JSON no válido"})
        if a == "entrar":
            clave = str(d.get("clave") or "")
            for r, c in _claves().items():
                if c and hmac.compare_digest(clave.encode(), c.encode()):
                    ck = "%s=%s; Path=/; Max-Age=%d; HttpOnly; Secure; SameSite=Lax" % (COOKIE, firmar(r), DIAS_SESION * 86400)
                    return self._enviar(200, {"rol": r}, ck)
            time.sleep(1.2)
            return self._enviar(401, {"error": "contraseña incorrecta"})
        if a == "salir":
            return self._enviar(200, {"rol": None}, "%s=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Lax" % COOKIE)
        if not rol:
            return self._enviar(401, {"error": "sin sesión"})
        if self.headers.get("X-Gestor") != "1":  # protección CSRF: solo la página del gestor envía esta cabecera
            return self._enviar(403, {"error": "petición no válida"})
        if a == "mencion":
            return self._enviar(*accion_mencion(rol, d))
        if a == "republicar":
            return self._enviar(200, republicar_y_marcar(d.get("id")))
        if a == "republicar_pendientes":
            ids = [p["id"] for p in piezas(60) if pendiente_web(p)]
            res = [dict(republicar_y_marcar(i), id=i) for i in ids[:15]]
            return self._enviar(200, {"ok": all(r["ok"] for r in res), "piezas": res, "quedan": max(0, len(ids) - 15)})
        if rol != "superadmin":
            return self._enviar(403, {"error": "solo el superadministrador puede cambiar productos y publicidad"})
        if a == "producto":
            return self._enviar(*accion_producto(d))
        if a == "anuncio":
            return self._enviar(*accion_anuncio(d))
        return self._enviar(404, {"error": "acción desconocida"})
