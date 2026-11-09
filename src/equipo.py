"""MOTICIAS · Equipo del gestor (app.moticias.com/gestor/): personas, perfiles, invitaciones y contraseñas.

Solo biblioteca estándar. Los datos de las personas (nombre, correo, perfil, huella de la contraseña) NO viven en este
repositorio, que es público: viven en el repositorio privado `movo-es/moticias-equipo` (`equipo.json`), al que el
gestor accede con su GITHUB_TOKEN. Este módulo solo tiene la lógica; `api/gestor.py` lee y guarda el fichero.

Perfiles (decisiones de Rainer, 9-11-2026; los suscriptores y la redacción de Ghost se gestionan en Ghost):
- superadmin (= editor jefe): todo. Solo él publica: edita, retira y reenfoca piezas con IA, publica cajas de contenido
  patrocinado, activa publicidad y patrocinios, cambia productos y gestiona el equipo. «Imposible para quien no sea editor
  jefe» (9-11-2026, tarde): los demás proponen y él publica.
- editor: propone cajas en las piezas y trabaja en el CRM (fuentes, medios); ve suscriptores.
- comercial: propone publicidad y patrocinios y trabaja en el CRM con sus contratos; ve suscriptores.
- oficina: propone cajas y trabaja en el CRM; ve suscriptores; aprueba y envía las notas de prensa pagadas de clientes (no las de MOTICIAS).
Nadie salvo el superadministrador ve ni cambia el equipo. Nunca se borra a nadie: se suspende.
Los datos de las personas viven en la base privada del gestor (Supabase «moticias», tabla `equipo`) y, si no está
configurada, en el repositorio privado `movo-es/moticias-equipo`.
"""
import datetime, hashlib, hmac, re, secrets

PERFILES = {
    "superadmin": {"nombre": "Superadministrador (editor jefe)",
                   "permisos": ["piezas", "redaccion", "productos", "publicidad", "equipo", "suscriptores", "crm", "contratos", "proponer", "barrido"]},
    "editor": {"nombre": "Editor", "permisos": ["proponer", "crm", "suscriptores", "barrido"]},  # barrido: «Iniciar barrido de noticias ahora» (9-11-2026)
    "comercial": {"nombre": "Comercial", "permisos": ["proponer", "crm", "contratos", "suscriptores"]},
    "oficina": {"nombre": "Oficina", "permisos": ["proponer", "crm", "suscriptores", "notas_clientes"]},  # notas_clientes: aprueba y envía notas de prensa pagadas de clientes (decisión de Rainer, 9-11-2026)
}
ITERACIONES = 210_000
DIAS_INVITACION = 7


def ahora():
    return datetime.datetime.now().astimezone().isoformat(timespec="minutes")


def vacio():
    return {"personas": [], "actualizado": ahora()}


def normal(email):
    return (email or "").strip().lower()


def email_valido(email):
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", normal(email)))


def huella(clave, sal=None):
    sal = sal or secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", clave.encode("utf-8"), bytes.fromhex(sal), ITERACIONES).hex()
    return sal, h


def comprobar(persona, clave):
    if not persona.get("huella") or not persona.get("sal"):
        return False
    return hmac.compare_digest(huella(clave, persona["sal"])[1], persona["huella"])


def clave_valida(clave):
    """Mínimo 10 caracteres. Sin más reglas: mejor una frase larga que una contraseña rara."""
    return isinstance(clave, str) and len(clave) >= 10


def buscar(datos, pid=None, email=None):
    for p in datos.get("personas", []):
        if (pid and p.get("id") == pid) or (email and normal(p.get("email")) == normal(email)):
            return p
    return None


def publica(p):
    """Lo que el gestor enseña de una persona (nunca la huella ni el token)."""
    inv = p.get("invitacion") or {}
    return {"id": p["id"], "nombre": p.get("nombre"), "email": p.get("email"), "perfil": p.get("perfil"),
            "perfil_nombre": PERFILES.get(p.get("perfil"), {}).get("nombre", p.get("perfil")), "estado": p.get("estado"),
            "creado": p.get("creado"), "ultimo_acceso": p.get("ultimo_acceso"), "invitacion_expira": inv.get("expira")}


def nueva_invitacion(p):
    """Genera un enlace de un solo uso (7 días). Guarda solo la huella del token; devuelve el token para el enlace."""
    token = secrets.token_urlsafe(24)
    exp = (datetime.datetime.now().astimezone() + datetime.timedelta(days=DIAS_INVITACION)).isoformat(timespec="minutes")
    p["invitacion"] = {"huella": hashlib.sha256(token.encode()).hexdigest(), "expira": exp}
    p["version"] = int(p.get("version") or 0) + 1  # cierra las sesiones abiertas de esa persona
    return "%s.%s" % (p["id"], token)


def invitar(datos, nombre, email, perfil, por):
    if perfil not in PERFILES:
        raise ValueError("perfil no válido")
    if not (nombre or "").strip():
        raise ValueError("falta el nombre")
    if not email_valido(email):
        raise ValueError("correo no válido")
    if buscar(datos, email=email):
        raise ValueError("ya hay una persona con ese correo")
    p = {"id": secrets.token_hex(6), "nombre": nombre.strip()[:80], "email": normal(email), "perfil": perfil, "estado": "invitada",
         "creado": ahora(), "creado_por": por, "version": 0, "historial": [{"en": ahora(), "por": por, "accion": "invitar", "perfil": perfil}]}
    enlace = nueva_invitacion(p)
    datos.setdefault("personas", []).append(p)
    return p, enlace


def aceptar(datos, invitacion, clave):
    try:
        pid, token = invitacion.split(".", 1)
    except ValueError:
        raise ValueError("enlace no válido")
    p = buscar(datos, pid=pid)
    inv = (p or {}).get("invitacion") or {}
    if not p or not inv.get("huella") or not hmac.compare_digest(hashlib.sha256(token.encode()).hexdigest(), inv["huella"]):
        raise ValueError("enlace no válido o ya usado")
    if inv.get("expira", "") < ahora():
        raise ValueError("el enlace ha caducado: pide otro al superadministrador")
    if p.get("estado") == "suspendida":
        raise ValueError("esta cuenta está suspendida")
    if not clave_valida(clave):
        raise ValueError("la contraseña necesita al menos 10 caracteres")
    p["sal"], p["huella"] = huella(clave)
    p["estado"] = "activa"
    p.pop("invitacion", None)
    p["version"] = int(p.get("version") or 0) + 1
    p.setdefault("historial", []).append({"en": ahora(), "por": p["nombre"], "accion": "crear contraseña"})
    return p


def cambiar(datos, pid, accion, por, perfil=None):
    p = buscar(datos, pid=pid)
    if not p:
        raise ValueError("persona no encontrada")
    enlace = None
    if accion == "perfil":
        if perfil not in PERFILES:
            raise ValueError("perfil no válido")
        p["perfil"] = perfil
        p["version"] = int(p.get("version") or 0) + 1
    elif accion == "suspender":
        p["estado"] = "suspendida"
        p["version"] = int(p.get("version") or 0) + 1
    elif accion == "reactivar":
        p["estado"] = "activa" if p.get("huella") else "invitada"
    elif accion == "nuevo_enlace":  # olvido de contraseña o invitación caducada
        enlace = nueva_invitacion(p)
        if p.get("estado") != "suspendida" and not p.get("huella"):
            p["estado"] = "invitada"
    else:
        raise ValueError("acción desconocida")
    p.setdefault("historial", []).append({"en": ahora(), "por": por, "accion": accion, **({"perfil": perfil} if perfil else {})})
    return p, enlace


def superadmins_activos(datos):
    return [p for p in datos.get("personas", []) if p.get("perfil") == "superadmin" and p.get("estado") == "activa"]
