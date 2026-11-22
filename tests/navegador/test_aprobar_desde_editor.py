"""Aprobar y publicar desde el editor del gestor, en un navegador de verdad contra una API fingida (sin red ni datos reales).
Necesita Playwright y Chrome:  python3 tests/navegador/test_aprobar_desde_editor.py   (CHROME=/ruta/al/chrome si no está en /usr/bin/google-chrome)."""
import json, os, subprocess, sys, time, urllib.request
from playwright.sync_api import sync_playwright
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ, P = os.path.dirname(os.path.dirname(AQUI)), 8765
srv = subprocess.Popen([sys.executable, "-I", os.path.join(AQUI, "gestor_api_fingida.py"), RAIZ, str(P)])
time.sleep(1.2)
B = "http://127.0.0.1:%d" % P
PID = "el-carbono-llega-al-surtidor-sin-su-contrapartida-r4tc"
def get(r): return json.load(urllib.request.urlopen(B + r))
fallos = []
def ok(cond, que):
    print(("  ok  " if cond else "  MAL ") + que)
    if not cond: fallos.append(que)
try:
    with sync_playwright() as pw:
        nav = pw.chromium.launch(executable_path=os.environ.get("CHROME", "/usr/bin/google-chrome"), args=["--no-sandbox"])
        def abrir(nueva=""):
            get("/_nueva" + nueva)
            pg = nav.new_page(viewport={"width": 1200, "height": 900})
            pg.dialogos, pg.errores = [], []
            pg.on("dialog", lambda d: (pg.dialogos.append(d.message), d.dismiss()))   # un diálogo del navegador = rechazado, como si estuviera bloqueado
            pg.on("pageerror", lambda e: pg.errores.append(str(e)))
            pg.goto(B + "/gestor/?pieza=%s&accion=editar" % PID)
            pg.wait_for_selector("#apr-ahora")
            return pg
        def pub(): return [l for l in get("/_estado")["llamadas"] if l["accion"] == "publicar"]
        def edi(): return [l for l in get("/_estado")["llamadas"] if l["accion"] == "editar"]

        print("A. Sin cambios: aprobar y publicar ahora")
        pg = abrir()
        ok("todavía no está publicada" in pg.inner_text("#app"), "antes de aprobar, avisa de que está pendiente")
        pg.click("#apr-ahora"); pg.wait_for_selector("#apr-si")
        ok(len(pub()) == 0, "el primer toque no publica: pide confirmación dentro de la página")
        pg.click("#apr-si"); pg.wait_for_selector("#ed-hecho")
        t = pg.inner_text("#app")
        ok(len(pub()) == 1 and pub()[0].get("cuando") == "ahora" and pub()[0].get("texto_ok") and pub()[0].get("imagen_ok"), "llega al servidor una sola aprobación, «ahora», con texto e imagen aprobados")
        ok(len(edi()) == 0, "no guarda nada si no había cambios")
        ok(get("/_estado")["status"] == "publicado", "la pieza queda publicada en el servidor")
        ok("Publicada en moticias.com" in t, "la pantalla dice «Publicada en moticias.com»")
        ok("todavía no está publicada" not in t and "sigue pendiente" not in t and "· pendiente" not in pg.inner_text("#app .card .mute"), "ya no dice «todavía no está publicada» ni «pendiente» (aunque el servidor devuelva la ficha atrasada)")
        ok(pg.query_selector("#apr-ahora") is None and "Publicar cambios" in t, "desaparecen los botones de aprobar; queda «Publicar cambios»")
        ok(pg.evaluate("window.scrollY") == 0 and pg.is_visible("#ed-hecho"), "el resultado se ve sin desplazarse")
        ok(not pg.dialogos and not pg.errores, "sin diálogos del navegador ni errores de script")
        pg.close()

        print("B. Con texto cambiado y un fallo del servidor al publicar")
        pg = abrir("?fallos=1")
        pg.fill('[data-c="title"]', "Titular retocado  ")
        pg.click("#apr-ahora"); pg.wait_for_selector("#apr-si")
        ok("se guardan los cambios" in pg.inner_text("#apr-estado"), "avisa de que antes guarda los cambios")
        pg.click("#apr-si"); pg.wait_for_selector("#apr-otra")
        t = pg.inner_text("#apr-estado")
        ok("No se ha publicado" in t and "GitHub no ha aceptado" in t, "el fallo queda escrito en la tarjeta, con su motivo")
        ok(pg.is_visible("#apr-estado") and "todavía no está publicada" in pg.inner_text("#app"), "y sigue diciendo que está pendiente (es verdad)")
        time.sleep(7.5); ok(pg.is_visible("#apr-estado"), "el mensaje de fallo no se va solo")
        pg.click("#apr-otra"); pg.wait_for_selector("#ed-hecho")
        ok(len(edi()) == 1 and edi()[0]["cambios"] == ["title"], "los cambios se guardaron una sola vez, también tras reintentar")
        ok(len(pub()) == 2 and get("/_estado")["status"] == "publicado", "el reintento publica")
        ok("Titular retocado" in pg.inner_text("h1") and "todavía no está publicada" not in pg.inner_text("#app"), "pantalla al día, con el titular nuevo")
        ok(not pg.dialogos and not pg.errores, "sin diálogos ni errores")
        pg.close()

        print("C. Aprobar para el lunes y cambio de firma")
        pg = abrir()
        pg.click('#firma [data-f="redaccion"]')
        pg.click("#apr-lunes"); pg.wait_for_selector("#apr-si"); pg.click("#apr-si"); pg.wait_for_selector("#ed-hecho")
        ok(len(edi()) == 1 and edi()[0]["firma"] == "redaccion" and edi()[0]["cambios"] == [], "guarda antes el cambio de firma")
        ok(len(pub()) == 1 and pub()[0]["cuando"] == "lunes", "la aprobación va con «lunes»")
        ok("Sale el lunes a las 08:00" in pg.inner_text("#ed-hecho"), "la pantalla dice que sale el lunes a las 08:00")
        ok(not pg.dialogos and not pg.errores, "sin diálogos ni errores")
        pg.close()

        print("D. Cancelar, cifras nuevas y web que no responde")
        pg = abrir()
        pg.click("#apr-ahora"); pg.wait_for_selector("#apr-si"); pg.click("#apr-no")
        ok(len(pub()) == 0 and not pg.is_visible("#apr-estado"), "«Cancelar» no publica nada")
        pg.close()
        pg = abrir("?cifras=1")
        pg.fill('[data-c="subtitle"]', "Desde 2031 cambia todo")
        pg.click("#apr-ahora"); pg.wait_for_selector("#apr-si"); pg.click("#apr-si"); pg.wait_for_selector("#apr-igual")
        ok(len(pub()) == 0 and "2031" in pg.inner_text("#apr-estado"), "con una cifra nueva se para y la enseña; no publica")
        pg.click("#apr-igual"); pg.wait_for_selector("#ed-hecho")
        ok(len(pub()) == 1 and edi()[-1].get("confirmo_cifras") is True, "si respondes de la cifra, guarda y publica")
        pg.close()
        pg = abrir("?ghost=0")
        pg.click("#apr-ahora"); pg.wait_for_selector("#apr-si"); pg.click("#apr-si"); pg.wait_for_selector("#ed-hecho")
        ok("todavía no ha llegado a la web" in pg.inner_text("#ed-hecho") and "Ghost 503" in pg.inner_text("#ed-hecho"), "si la web no responde, lo dice (aprobada, pendiente de subir)")
        pg.close()

        print("E. Guardar sin aprobar sigue funcionando")
        pg = abrir()
        pg.fill('[data-c="kicker"]', "Otro antetítulo")
        pg.click("#pub"); pg.wait_for_function("document.querySelector('#aviso').textContent.includes('sigue pendiente')")
        ok(len(edi()) == 1 and len(pub()) == 0 and get("/_estado")["status"] == "pendiente", "guarda, no publica y lo dice")
        ok(pg.query_selector("#ed-hecho") is None and pg.query_selector("#apr-ahora") is not None, "siguen los botones de aprobar")
        pg.close()

        print("F. Móvil")
        get("/_nueva")
        pg = nav.new_page(viewport={"width": 390, "height": 800}); pg.dialogos = []
        pg.goto(B + "/gestor/?pieza=%s&accion=editar" % PID); pg.wait_for_selector("#apr-ahora")
        pg.click("#apr-ahora"); pg.wait_for_selector("#apr-si")
        ok(pg.evaluate("(()=>{const r=document.querySelector('#apr-si').getBoundingClientRect();return r.top>=0&&r.bottom<=innerHeight})()"), "la confirmación queda a la vista")
        pg.click("#apr-si"); pg.wait_for_selector("#ed-hecho")
        ok(pg.is_visible("#ed-hecho") and pg.evaluate("window.scrollY") == 0, "y el resultado también")
        pg.close(); nav.close()
finally:
    srv.terminate()
print("\nRESULTADO:", "TODO BIEN" if not fallos else "%d FALLOS: %s" % (len(fallos), fallos))
sys.exit(1 if fallos else 0)
