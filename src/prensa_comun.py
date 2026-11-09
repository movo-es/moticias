"""MOTICIAS · Sala de prensa: piezas comunes (nota pública, pedido privado, firmas de enlaces). Solo biblioteca estándar.

Nota pública   → data/notas-de-prensa/<id>.json  (lo que se publica; sin correo ni teléfono de nadie salvo el contacto de
                 prensa que el propio emisor publica en su nota).
Pedido privado → tabla prensa_notas de la base privada (migración 006): cliente (cuenta y persona del CRM), plan,
                 valoración, verificación, envío asociado (prensa_envios) e informe. Coberturas en prensa_coberturas.
Destinatarios  → la base de prensa (medios, periodistas; src/prensa.py), filtrada por src/prensa_valor.py.
"""
import base64, datetime, hashlib, hmac, json, os, re, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOTAS = os.environ.get("PRENSA_NOTAS") or os.path.join(ROOT, "data", "notas-de-prensa")  # PRENSA_NOTAS: solo para pruebas


def ahora():
    return datetime.datetime.now().astimezone().isoformat(timespec="minutes")


def norm_email(e):
    e = (e or "").strip().lower()
    return e if re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", e) else ""


def slug(s, n=70):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:n].rstrip("-") or "nota"


def nuevo_id(titulo, fecha=None):
    return "%s-%s" % ((fecha or datetime.date.today().isoformat())[:10], slug(titulo, 60))


def guardar_json(ruta, obj):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    tmp = ruta + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
    os.replace(tmp, ruta)


def leer_nota(nid):
    return json.load(open(os.path.join(NOTAS, nid + ".json"), encoding="utf-8"))


def guardar_nota(n):
    guardar_json(os.path.join(NOTAS, n["id"] + ".json"), n)


def todas_las_notas():
    if not os.path.isdir(NOTAS):
        return []
    return [json.load(open(os.path.join(NOTAS, f), encoding="utf-8")) for f in sorted(os.listdir(NOTAS)) if f.endswith(".json")]


def leer_pedido(nid):
    import bd as BD
    r = BD.leer("prensa_notas", select="*", id="eq." + nid)
    return r[0] if r else None


def guardar_pedido(nid, cambios):
    import bd as BD
    cambios = dict(cambios, actualizado=ahora())
    return BD.actualizar("prensa_notas", {"id": "eq." + nid}, cambios)


# ---------- enlaces firmados (baja, informe) ----------
def _secreto():
    # La misma llave que firma las bajas de src/prensa.py: así no hace falta otra variable en Vercel ni en las tareas.
    s = os.environ.get("PRENSA_SECRETO") or os.environ.get("MOTICIAS_BD_CLAVE") or os.environ.get("GESTOR_CLAVE_SUPERADMIN")
    if not s:
        raise SystemExit("Falta MOTICIAS_BD_CLAVE en el entorno (firma de los enlaces de confirmación e informe).")
    return ("sala-de-prensa|" + s).encode()


def firmar(tipo, valor):
    """Token para URL: «tipo~valor_en_base64url.firma». Sirve para confirmar el envío de una nota y abrir su informe."""
    v = base64.urlsafe_b64encode(str(valor).encode()).decode().rstrip("=")
    msg = "%s~%s" % (tipo, v)
    return msg + "." + hmac.new(_secreto(), msg.encode(), hashlib.sha256).hexdigest()[:24]


def verificar(token, tipo):
    try:
        msg, sig = (token or "").rsplit(".", 1)
        t, v = msg.split("~", 1)
    except ValueError:
        return None
    if t != tipo or not hmac.compare_digest(sig, hmac.new(_secreto(), msg.encode(), hashlib.sha256).hexdigest()[:24]):
        return None
    return base64.urlsafe_b64decode(v + "=" * (-len(v) % 4)).decode()


def base_app():
    return (os.environ.get("APP_URL") or "https://app.moticias.com").rstrip("/")
