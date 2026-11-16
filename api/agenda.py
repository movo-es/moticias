"""MOTICIAS · API pública de la agenda (función de Vercel, Python, solo biblioteca estándar). Cambio `agenda-de-eventos`.

  POST /api/agenda?a=enviar   formulario «Subir mi evento» de moticias.com → base privada (agenda_envios), nunca publica
  GET  /api/agenda?a=ics      calendario de la agenda (también en app.moticias.com/feed/agenda.ics, por reescritura)

El gestor (pestaña «Agenda») vive en api/gestor.py. Variables de entorno: las de src/bd.py y BREVO_API_KEY (avisos).
"""
import json, os, sys, urllib.parse
from http.server import BaseHTTPRequestHandler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import agenda_gestor as AG  # noqa: E402
import eventos as EV  # noqa: E402
import ghost_agenda as GA  # noqa: E402

ORIGENES = ("https://www.moticias.com", "https://moticias.com", "https://moticias.ghost.io")


def correo(para, asunto, cuerpo):
    try:
        import menciones as M
        v = EV.vertical()
        ok, _ = M.enviar_correo(asunto, cuerpo, para, M.remitentes_avisos(v))
        return ok
    except Exception:  # noqa: BLE001 — sin correo, el envío queda igualmente en la cola
        return False


class handler(BaseHTTPRequestHandler):
    def _enviar(self, st, obj, tipo=None):
        b = obj.encode("utf-8") if isinstance(obj, str) else json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(st)
        self.send_header("Content-Type", tipo or "application/json; charset=utf-8")
        o = self.headers.get("Origin") or ""
        if o in ORIGENES:
            self.send_header("Access-Control-Allow-Origin", o)
            self.send_header("Vary", "Origin")
        self.send_header("Cache-Control", "public, max-age=900" if tipo and "calendar" in tipo else "no-store")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def _q(self):
        return {k: v[0] for k, v in urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).items()}

    def do_OPTIONS(self):
        self._enviar(204, "")

    def do_GET(self):
        if self._q().get("a", "ics") == "ics":
            v = EV.vertical()
            return self._enviar(200, GA.ics([EV.limpio(e) for e in EV.cargar()], v), "text/calendar; charset=utf-8")
        return self._enviar(404, {"error": "acción desconocida"})

    def do_POST(self):
        if self._q().get("a") != "enviar":
            return self._enviar(404, {"error": "acción desconocida"})
        try:
            n = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(min(n, 60000)) if n else b""
            if (self.headers.get("Content-Type") or "").startswith("application/x-www-form-urlencoded"):
                d = {k: v[0] for k, v in urllib.parse.parse_qs(raw.decode("utf-8", "replace")).items()}
                d["t"] = 999  # sin JavaScript no hay cronómetro; el campo trampa y el límite por origen siguen valiendo
            else:
                d = json.loads(raw or b"{}")
        except (ValueError, json.JSONDecodeError):
            return self._enviar(400, {"error": "Datos no válidos"})
        ip = (self.headers.get("x-forwarded-for") or "").split(",")[0].strip()
        st, r = AG.recibir(d, self.headers.get("User-Agent"), ip, correo)
        return self._enviar(st, r)
