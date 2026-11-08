#!/usr/bin/env python3
"""MOTICIAS · «Quién decide» (módulo 7) · semilla y candidatos. Solo biblioteca estándar.

  python3 -I src/quien_decide_semilla.py candidatos [--out work/cargos-candidatos.json]
      Recorre data/articles y data/boletines y extrae pares «Persona, cargo» con la pieza y la fecha en que
      aparecen. Es una lista para revisar, NO se publica: una persona la confirma y la pasa a sembrar.

  python3 -I src/quien_decide_semilla.py sembrar --desde work/semilla.json
      Escribe un JSON por cargo en data/cargos/<id>.json a partir de una lista revisada:
      [{"persona","cargo","organizacion","tipo_org","desde","hasta","vigente","fuentes":[{"tipo","url","fecha"}],
        "piezas":["<id>"],"notas"}]. Sin al menos una fuente no se escribe (regla «nada sin fuente»).
      Si el cargo ya existe, conserva lo anterior y añade las fuentes y piezas nuevas.

Regla RGPD: solo cargos públicos y profesionales; aquí no se guardan correos ni teléfonos personales. Los datos
de contacto profesional (email_profesional, tel_profesional) se añaden más adelante desde fuentes oficiales.
"""
import argparse, datetime, glob, json, os, re, sys, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARGOS = os.path.join(ROOT, "data", "cargos")
HOY = datetime.date.today().isoformat()

PAT = re.compile(r"([A-ZÁÉÍÓÚÑ][a-záéíóúñü]+(?:\s+(?:de|del|la|y|[A-ZÁÉÍÓÚÑ][a-záéíóúñü\-]+)){1,4}),\s+"
                 r"((?:ex\s?)?(?:ministr[oa]|secretari[oa] de estado|secretari[oa] general|subsecretari[oa]|director[a]? general|"
                 r"director[a]?|presidenta?|consejer[oa] delegad[oa]|consejer[oa]|alcalde(?:sa)?|delegad[oa]|gerente|comisari[oa]|"
                 r"vicepresidenta?|portavoz|CEO|responsable|jef[ea])[^.;,\n]{0,80})")
NO_NOMBRE = {"El", "La", "Los", "Las", "En", "Según", "Por", "Con", "Sin", "Este", "Esta", "Real", "Decreto", "Ley", "Orden", "Consejo",
             "Ministerio", "Gobierno", "Comisión", "Autoridad", "Puerto", "Puertos", "Adif", "Renfe", "Aena", "Tren", "Línea", "Junta",
             "Nacional", "Economista", "Dirección", "Secretaría", "Agencia", "Grupo", "Empresa"}


def slug(s):
    s = unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def candidatos(out):
    seen = {}
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "articles", "*.json"))):
        a = json.load(open(f, encoding="utf-8"))
        txt = " ".join(str(a.get(k) or "") for k in ("actors", "summary", "body_md"))
        for m in PAT.finditer(txt):
            nom, cargo = m.group(1).strip(), m.group(2).strip()
            if nom.split()[0] in NO_NOMBRE:
                continue
            seen.setdefault(nom, []).append({"cargo": cargo, "pieza": a["id"], "fecha": a.get("event_date") or a.get("date"),
                                             "oficiales": [s.get("url") for s in (a.get("sources") or []) if s.get("kind") == "oficial"][:3]})
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "boletines", "*.json"))):
        b = json.load(open(f, encoding="utf-8"))
        t = (b.get("titulo") or "") + " " + (b.get("titulo_corto") or "")
        if re.search(r"\b(nombra|nombramiento|cese|cesa|dispone el cese|designa)\b", t, re.I):
            seen.setdefault("(boletín) " + (b.get("titulo_corto") or b.get("referencia")), []).append(
                {"cargo": b.get("tipo"), "pieza": b["id"], "fecha": b.get("fecha"), "oficiales": [b.get("url")]})
    lista = [{"persona": k, "menciones": v} for k, v in sorted(seen.items(), key=lambda kv: -len(kv[1]))]
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump({"generated_at": HOY, "aviso": "Lista para revisar; no se publica sin confirmación humana.", "candidatos": lista},
              open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"candidatos": len(lista), "out": out}, ensure_ascii=False))


def sembrar(desde):
    lista = json.load(open(desde, encoding="utf-8"))
    os.makedirs(CARGOS, exist_ok=True)
    n_new = n_upd = n_skip = 0
    for c in lista:
        if not c.get("fuentes"):
            n_skip += 1
            print("omitido (sin fuente):", c.get("persona"), c.get("cargo"), file=sys.stderr)
            continue
        cid = slug("%s %s %s" % (c["persona"], c["cargo"], c.get("organizacion") or ""))[:80]
        path = os.path.join(CARGOS, cid + ".json")
        reg = {"id": cid, "vertical": c.get("vertical") or "movilidad", "persona": c["persona"], "cargo": c["cargo"],
               "organizacion": c.get("organizacion"), "tipo_org": c.get("tipo_org"), "desde": c.get("desde"), "hasta": c.get("hasta"),
               "vigente": c.get("vigente", c.get("hasta") in (None, "")), "email_profesional": None, "tel_profesional": None,
               "fuentes": c.get("fuentes") or [], "piezas": c.get("piezas") or [], "notas": c.get("notas"),
               "verificado_en": c.get("verificado_en") or HOY, "creado_en": HOY}
        if os.path.exists(path):
            old = json.load(open(path, encoding="utf-8"))
            urls = {f.get("url") for f in old.get("fuentes", [])}
            old["fuentes"] += [f for f in reg["fuentes"] if f.get("url") not in urls]
            old["piezas"] = sorted(set(old.get("piezas", [])) | set(reg["piezas"]))
            for k in ("hasta", "vigente", "desde", "notas"):
                if c.get(k) is not None:
                    old[k] = c[k]
            old["verificado_en"] = reg["verificado_en"]
            reg = old
            n_upd += 1
        else:
            n_new += 1
        json.dump(reg, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True)
    print(json.dumps({"nuevos": n_new, "actualizados": n_upd, "omitidos": n_skip, "carpeta": CARGOS}, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="modo", required=True)
    c = sub.add_parser("candidatos"); c.add_argument("--out", default=os.path.join(ROOT, "work", "cargos-candidatos.json"))
    s = sub.add_parser("sembrar"); s.add_argument("--desde", required=True)
    a = ap.parse_args()
    if a.modo == "candidatos":
        candidatos(a.out)
    else:
        sembrar(a.desde)


if __name__ == "__main__":
    main()
