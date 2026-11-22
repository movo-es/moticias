"""Imágenes del banner premium (cambio OpenSpec `imagenes-de-banner`, 22-11-2026), en un navegador de verdad y sin red:
A. Gestor: tabla de píxeles por formato, vista previa antes de subir, la imagen se encaja entera (no se estira) o se recorta, y nada
   llega al servidor hasta pulsar «Subir esta imagen».
B. moticias.com (`app/public/sitio/m.js`): la caja guarda la proporción del formato a cualquier ancho y, donde no coincide (el móvil sin
   imagen propia), la imagen sale entera con bandas, nunca estirada.
Necesita Playwright, Pillow y Chrome:  python3 tests/navegador/test_imagen_banner.py   (CAPTURAS=/carpeta para guardar capturas)."""
import base64, io, json, os, sys, threading, http.server, urllib.parse
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ, P = os.path.dirname(os.path.dirname(AQUI)), 8766
PUB = json.load(open(os.path.join(RAIZ, "verticals", "movilidad.json"), encoding="utf-8"))["publicidad"]
CAP = os.environ.get("CAPTURAS")
E = {"llamadas": [], "subidas": []}


def png(w, h):
    """Mitad izquierda roja y mitad derecha azul, con un círculo blanco en el centro: si se estira, el círculo deja de serlo."""
    im = Image.new("RGB", (w, h), (200, 30, 30)); d = ImageDraw.Draw(im)
    d.rectangle([w // 2, 0, w, h], fill=(20, 60, 200)); r = min(w, h) // 4
    d.ellipse([w // 2 - r, h // 2 - r, w // 2 + r, h // 2 + r], fill=(255, 255, 255))
    b = io.BytesIO(); im.save(b, "PNG"); return b.getvalue()


class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def _b(self, st, b, tipo):
        self.send_response(st); self.send_header("Content-Type", tipo); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

    def _j(self, st, o): self._b(st, json.dumps(o).encode(), "application/json")

    def do_GET(self):
        u = urllib.parse.urlparse(self.path); q = dict(urllib.parse.parse_qsl(u.query))
        if u.path.startswith("/gestor"):
            return self._b(200, open(RAIZ + "/app/public/gestor/index.html", "rb").read(), "text/html; charset=utf-8")
        if u.path.startswith("/subida/"):
            return self._b(200, E["subidas"][int(u.path.split("/")[2])], "image/jpeg")
        a = q.get("a")
        if a == "yo":
            return self._j(200, {"rol": "superadmin", "nombre": "Prueba", "permisos": ["publicidad", "proponer"], "configurado": True, "escritura": True, "ghost": True, "bd": False})
        if a == "anuncios":
            return self._j(200, {"anuncios": [], "publicidad": PUB})
        return self._j(200, {})

    def do_POST(self):
        q = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(self.path).query))
        d = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
        E["llamadas"].append((q.get("a"), d))
        if q.get("a") == "anuncio_imagen":
            E["subidas"].append(base64.b64decode(d["datos"].split(",", 1)[1]))
            return self._j(200, {"ok": True, "url": "http://127.0.0.1:%d/subida/%d" % (P, len(E["subidas"]) - 1)})
        return self._j(200, {"ok": True, "nota": "Guardada"})


srv = http.server.ThreadingHTTPServer(("127.0.0.1", P), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
B = "http://127.0.0.1:%d" % P
fallos = []


def ok(cond, que):
    print(("  ok  " if cond else "  MAL ") + que)
    if not cond: fallos.append(que)


def px(pg, sel, x, y):
    return pg.evaluate("([s,x,y]) => [...document.querySelector(s).getContext('2d').getImageData(x,y,1,1).data].slice(0,3)", [sel, x, y])


def cerca(a, b, t=40): return all(abs(i - j) <= t for i, j in zip(a, b))


def captura(pg, nombre, sel=None):
    if CAP:
        pg.evaluate("() => { const n = document.querySelector('#aviso'); if (n) n.style.display = 'none'; }")  # el aviso flotante taparía la captura
        (pg.locator(sel) if sel else pg).screenshot(path=os.path.join(CAP, nombre))


ROJO, AZUL, BLANCO = (200, 30, 30), (20, 60, 200), (255, 255, 255)
try:
    with sync_playwright() as pw:
        nav = pw.chromium.launch(executable_path=os.environ.get("CHROME", "/usr/bin/google-chrome"), args=["--no-sandbox"])

        print("A. Gestor (móvil, 390 px): subir una imagen apaisada al formato 2x4")
        pg = nav.new_page(viewport={"width": 390, "height": 844}); errores = []
        pg.on("pageerror", lambda e: errores.append(str(e)))
        pg.goto(B + "/gestor/?vista=anuncios"); pg.wait_for_selector("#nueva"); pg.click("#nueva")
        pg.check('#form .chk input[value="portada-premium"]'); pg.wait_for_selector("#b-formato")
        pg.click('#b-modo [data-v="imagen"]'); pg.wait_for_selector(".t-med")
        t = pg.inner_text(".t-med")
        ok("2406 × 280 px" in t and "1176 × 1288 px" in t and "716 × 240 px" in t, "la tabla da los píxeles de cada formato y del móvil")
        ok("Vertical" not in pg.inner_text(".t-med tr:nth-child(2)") and "más alta que ancha" in t, "y dice la forma real de cada uno (horizontal, casi cuadrada…)")
        pg.set_input_files("#b-img", {"name": "x.png", "mimeType": "image/png", "buffer": png(800, 400)})
        ok(pg.inner_text("#aviso") == "Elige primero el formato" and pg.query_selector("#p-lienzo") is None, "sin formato elegido no deja seguir y lo dice")
        pg.click('#b-formato [data-v="2x4"]')
        ok("1176 × 1288 px" in pg.inner_text("#f-ban label:has(+ input#b-img), #f-ban"), "al elegir formato, la etiqueta del campo dice sus píxeles")
        pg.set_input_files("#b-img", {"name": "apaisada.png", "mimeType": "image/png", "buffer": png(1200, 400)})
        pg.wait_for_selector("#p-lienzo")
        t = pg.inner_text("#b-previa")
        ok("1200 × 400 px" in t and "1176 × 1288 px" in t and "no se estira" in t, "avisa de que no coincide, con las dos medidas, y de que no se estira")
        ok("Todavía no se ha subido nada" in t and not E["llamadas"], "hay vista previa y aún no se ha subido nada")
        dim = pg.evaluate("() => { const c = document.querySelector('#p-lienzo'); return [c.width, c.height]; }")
        ok(dim == [1176, 1288], "la vista previa tiene la proporción exacta del formato (1176 × 1288)")
        # encajada: 1176 × 392 centrada en vertical (filas 448–840); arriba y abajo, banda del color del borde (rojo/azul mezclados)
        banda, izq, der, centro = px(pg, "#p-lienzo", 588, 100), px(pg, "#p-lienzo", 150, 644), px(pg, "#p-lienzo", 1020, 644), px(pg, "#p-lienzo", 588, 644)
        ok(cerca(izq, ROJO) and cerca(der, AZUL) and cerca(centro, BLANCO), "encajada: la imagen entra entera (rojo a la izquierda, azul a la derecha)")
        ok(not cerca(banda, ROJO) and not cerca(banda, AZUL) and not cerca(banda, BLANCO), "y lo que sobra arriba y abajo es banda de color, no imagen estirada")
        # el círculo sigue siendo un círculo: radio 100 px en origen → 98 px en la vista previa, igual a lo ancho que a lo alto
        ok(cerca(px(pg, "#p-lienzo", 588 + 90, 644), BLANCO) and cerca(px(pg, "#p-lienzo", 588, 644 + 90), BLANCO)
           and not cerca(px(pg, "#p-lienzo", 588 + 106, 644), BLANCO) and not cerca(px(pg, "#p-lienzo", 588, 644 + 106), BLANCO), "el círculo sigue redondo: no se ha deformado")
        ok(pg.query_selector("#p-lienzo-m") is not None and "Así se verá en el móvil" in t, "enseña también cómo queda en el móvil")
        captura(pg, "gestor-previa-encajar.png", "#b-previa")
        pg.click('#p-color [title="Blanco"]')
        ok(cerca(px(pg, "#p-lienzo", 588, 100), BLANCO, 3), "el color de las bandas se puede cambiar (blanco)")
        pg.click('#p-encaje [data-v="recortar"]'); pg.wait_for_selector("#p-x")
        arriba = px(pg, "#p-lienzo", 100, 20)
        ok(cerca(arriba, ROJO) or cerca(arriba, AZUL) or cerca(arriba, BLANCO), "recortada: la imagen llena la caja, sin bandas")
        ok(cerca(px(pg, "#p-lienzo", 588 + 300, 644), BLANCO) and cerca(px(pg, "#p-lienzo", 588, 644 + 300), BLANCO), "y el círculo sigue redondo (crece igual a lo ancho que a lo alto)")
        captura(pg, "gestor-previa-recortar.png", "#b-previa")
        ok(not E["llamadas"], "probar las dos formas tampoco sube nada")
        pg.click('#p-encaje [data-v="encajar"]'); pg.click("#p-subir"); pg.wait_for_selector("#f-ban .ban-pv img")
        ok(len(E["subidas"]) == 1 and Image.open(io.BytesIO(E["subidas"][0])).size == (1176, 1288), "al pulsar «Subir esta imagen» llega una sola, ya a 1176 × 1288")
        ok(pg.query_selector("#b-previa .card") is None, "la vista previa se cierra y queda la imagen subida en su marco")
        pg.fill("#f-name", "Prueba"); pg.fill("#f-h", "Titular"); pg.fill("#b-alt", "Un círculo blanco"); pg.fill("#f-url", "https://example.org")
        captura(pg, "gestor-subida.png", "#f-ban")
        pg.click("#f-ok"); pg.wait_for_timeout(400)
        g = [d for a, d in E["llamadas"] if a == "anuncio"]
        c = g[0]["cambios"] if g else {}
        ok(c.get("modo") == "imagen" and c.get("formato") == "2x4" and str(c.get("image", "")).endswith("/subida/0") and c.get("imagen_fondo", "").lower() == "#ffffff",
           "al guardar viajan el formato, la imagen y el color de las bandas")
        ok(not errores, "sin errores de script en el gestor" + (": " + errores[0] if errores else ""))
        pg.close()

        print("B. moticias.com: la imagen en la portada")
        m2x4, m4x1 = png(1176, 1288), png(2406, 280)
        html = """<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
          <style>body{margin:0}.wrap{max-width:1203px;margin:0 auto;padding:0 16px}</style>
          <body class="home-template"><section class="cover"><div class="wrap"><h1>Apertura</h1><a href="/a/">Una noticia</a></div></section>
          <footer class="site">pie</footer><script src="https://app.moticias.com/sitio/m.js"></script>"""

        def portada(ancho, alto, formato, img, movil=None, fondo="#102a54"):
            caja = {"id": "p", "tipo": "publicidad", "etiqueta": "Publicidad", "rel": "sponsored", "anunciante": "X", "titular": "T", "texto": "", "cta": "", "url": "https://example.org",
                    "nivel": "premium", "peso": 1, "imagen": "https://img.test/a.png", "secciones": [], "campana": "p", "formato": formato, "modo": "imagen",
                    "imagen_movil": "https://img.test/m.png" if movil else None, "alt": "círculo", "imagen_fondo": fondo, "cta_tipo": None}
            datos = {"huecos": {"portada-premium": [caja]}, "tope_pago": 3, "rejilla": PUB["rejilla"], "formulario": False}
            pg = nav.new_page(viewport={"width": ancho, "height": alto}); pg.errores = []
            pg.on("pageerror", lambda e: pg.errores.append(str(e)))

            def ruta(r):
                u = r.request.url
                if u.startswith("https://www.moticias.com/") and r.request.resource_type == "document": return r.fulfill(status=200, content_type="text/html", body=html)
                if u.endswith("/sitio/m.js"): return r.fulfill(status=200, content_type="text/javascript", body=open(RAIZ + "/app/public/sitio/m.js", encoding="utf-8").read())
                if "a=publicidad" in u: return r.fulfill(status=200, content_type="application/json", body=json.dumps(datos), headers={"Access-Control-Allow-Origin": "*"})
                if u == "https://img.test/a.png": return r.fulfill(status=200, content_type="image/png", body=img)
                if u == "https://img.test/m.png": return r.fulfill(status=200, content_type="image/png", body=movil)
                return r.fulfill(status=200, content_type="application/json", body="{}", headers={"Access-Control-Allow-Origin": "*"})
            pg.route("**/*", ruta); pg.goto("https://www.moticias.com/"); pg.wait_for_selector(".mtx-ban img"); pg.wait_for_timeout(500)
            r = pg.evaluate("""() => { const b = document.querySelector('.mtx-ban'), i = b.querySelector('img'), r = b.getBoundingClientRect(), ri = i.getBoundingClientRect();
                return {w: r.width, h: r.height, iw: ri.width, ih: ri.height, fit: getComputedStyle(i).objectFit, nat: i.naturalWidth / i.naturalHeight, fondo: getComputedStyle(b).backgroundColor,
                        lab: b.querySelector('.mtx-ban-lab').textContent}; }""")
            return pg, r

        for ancho in (1280, 1000, 800):
            pg, r = portada(ancho, 900, "2x4", m2x4)
            ok(abs(r["w"] / r["h"] - 1176 / 1288) < 0.01 and abs(r["iw"] - r["w"]) < 3 and abs(r["ih"] - r["h"]) < 3,
               "2x4 a %d px: la caja mide %d × %d, la proporción de la imagen, y la imagen la llena entera" % (ancho, r["w"], r["h"]))
            if ancho == 1280: captura(pg, "web-2x4-1280.png")
            ok(not pg.errores, "sin errores de script"); pg.close()
        pg, r = portada(1280, 900, "4x1", m4x1)
        ok(abs(r["w"] / r["h"] / (2406 / 280) - 1) < 0.02 and r["fit"] == "cover" and r["lab"] == "Publicidad", "4x1: banda a todo el ancho (%d × %d) con su etiqueta" % (r["w"], r["h"])); pg.close()
        pg, r = portada(390, 844, "2x4", m2x4)
        ok(r["fit"] == "contain" and abs(r["w"] / r["h"] - 358 / 120) < 0.05, "móvil sin imagen propia: franja de %d × %d y la imagen entra entera (contain), sin estirar ni cortar" % (r["w"], r["h"]))
        ok(r["fondo"] == "rgb(16, 42, 84)", "las bandas del móvil llevan el color elegido en el gestor")
        captura(pg, "web-2x4-movil.png", ".mtx-ban"); pg.close()
        pg, r = portada(390, 844, "2x4", m2x4, movil=png(716, 240))
        ok(abs(r["nat"] - 716 / 240) < 0.01 and r["fit"] == "cover", "móvil con imagen propia: se usa esa y llena la franja")
        captura(pg, "web-2x4-movil-propia.png", ".mtx-ban"); pg.close()
        pg, r = portada(1280, 900, "3x2", m2x4)
        ok(r["fit"] == "contain", "una imagen hecha para otro formato sale entera con bandas, no estirada")
        captura(pg, "web-otro-formato.png", ".mtx-ban"); pg.close()
        nav.close()
finally:
    srv.shutdown()
print("\n%s" % ("TODO BIEN" if not fallos else "FALLOS: %d\n- %s" % (len(fallos), "\n- ".join(fallos))))
sys.exit(1 if fallos else 0)
