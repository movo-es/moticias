"""Servidor de pruebas: sirve el gestor real y finge la API. Sin red, sin datos reales fuera del texto de la pieza."""
import json, sys, http.server, urllib.parse, threading
RAIZ = sys.argv[1]; PUERTO = int(sys.argv[2])
ART = json.load(open(RAIZ + "/data/articles/el-carbono-llega-al-surtidor-sin-su-contrapartida-r4tc.json", encoding="utf-8"))
CAMPOS = ("title", "subtitle", "kicker", "summary", "body_md", "key_fact", "actors", "relevance_for", "why", "next")
E = {"llamadas": [], "fallos_publicar": 0, "cifras": False, "ghost_ok": True}
def nueva():
    E.update(llamadas=[], fallos_publicar=0, cifras=False, ghost_ok=True)
    E["a"] = dict(ART, status="pendiente")
def ficha():
    a = E["a"]
    return {"id": a["id"], "campos": {k: a.get(k) or "" for k in CAMPOS}, "nombres": {k: k for k in CAMPOS}, "status": a["status"], "kind": a.get("kind"),
            "date": a.get("date"), "author": a.get("author"), "section": a.get("section"), "url": "https://www.moticias.com/x/", "revisiones": [],
            "correcciones": [], "fuentes": [], "enfoques": {"a": "Otro"},
            "firma": {"actual": "editor_jefe" if a.get("author") == "Rainer Uphoff" else "redaccion", "editor_jefe": "Rainer Uphoff", "redaccion": "G. Jordan",
                      "importante": True, "motivo": "prueba", "propuesta": "x", "cupo": {"editor_jefe": 6, "total": 115, "pct": 5.2, "max": 10}}}
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _j(self, st, o):
        b = json.dumps(o).encode(); self.send_response(st); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        u = urllib.parse.urlparse(self.path); q = dict(urllib.parse.parse_qsl(u.query))
        if u.path.startswith("/gestor"):
            b = open(RAIZ + "/app/public/gestor/index.html", "rb").read()
            self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.send_header("Content-Length", str(len(b))); self.end_headers(); return self.wfile.write(b)
        if u.path == "/_estado": return self._j(200, {"llamadas": E["llamadas"], "status": E["a"]["status"]})
        if u.path == "/_nueva":
            nueva(); E["fallos_publicar"] = int(q.get("fallos", 0)); E["cifras"] = q.get("cifras") == "1"; E["ghost_ok"] = q.get("ghost", "1") == "1"; return self._j(200, {})
        if u.path != "/api/gestor": return self._j(404, {"error": "no"})
        a = q.get("a")
        if a == "yo": return self._j(200, {"rol": "superadmin", "nombre": "Prueba", "permisos": ["redaccion", "piezas", "proponer"], "configurado": True, "escritura": True, "ghost": True, "bd": True})
        if a == "redaccion": return self._j(200, ficha())
        if a == "pieza": return self._j(200, {"id": E["a"]["id"], "status": E["a"]["status"], "title": E["a"]["title"], "menciones": []})
        return self._j(200, {})
    def do_POST(self):
        u = urllib.parse.urlparse(self.path); q = dict(urllib.parse.parse_qsl(u.query))
        d = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
        if q.get("a") != "redaccion": return self._j(200, {})
        E["llamadas"].append({k: (v if k != "cambios" else sorted(v)) for k, v in d.items()})
        acc = d.get("accion")
        if acc == "editar":
            if E["cifras"] and not d.get("confirmo_cifras"): return self._j(409, {"error": "hay cifras nuevas", "cifras": ["2031"]})
            cam = {k: v.strip() for k, v in (d.get("cambios") or {}).items()}
            firma = d.get("firma"); actual = ficha()["firma"]["actual"]
            if not cam and firma == actual: return self._j(400, {"error": "no hay cambios"})
            E["a"].update(cam)
            if firma: E["a"]["author"] = "Rainer Uphoff" if firma == "editor_jefe" else "G. Jordan"
            return self._j(200, {"ok": True, "ghost": {"ok": True}, "pieza": ficha()})
        if acc == "publicar":
            if E["a"]["status"] != "pendiente": return self._j(400, {"error": "la pieza no está pendiente"})
            if not d.get("texto_ok") or not d.get("imagen_ok"): return self._j(400, {"error": "aprueba expresamente el texto y la imagen"})
            if E["fallos_publicar"] > 0:
                E["fallos_publicar"] -= 1; return self._j(502, {"error": "GitHub no ha aceptado el cambio (prueba)"})
            pieza_vieja = ficha()  # como si la lectura posterior llegara atrasada: sigue diciendo «pendiente»
            E["a"]["status"] = "publicado"
            return self._j(200, {"ok": True, "ghost": {"ok": E["ghost_ok"], "detalle": "" if E["ghost_ok"] else "Ghost 503"}, "pieza": pieza_vieja})
        return self._j(400, {"error": "acción desconocida"})
nueva()
http.server.ThreadingHTTPServer(("127.0.0.1", PUERTO), H).serve_forever()
