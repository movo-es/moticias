#!/usr/bin/env python3
"""MOTICIAS · Fuentes de segundo nivel · Barrido de la BDNS (Base de Datos Nacional de Subvenciones). Solo biblioteca estándar.

API pública del Sistema Nacional de Publicidad de Subvenciones (sin clave):
  búsqueda: https://www.infosubvenciones.es/bdnstrans/api/convocatorias/busqueda?vpd=GE&descripcion=<texto>&order=fechaRecepcion&direccion=desc&page=0&pageSize=50
  detalle:  https://www.infosubvenciones.es/bdnstrans/api/convocatorias?vpd=GE&numConv=<codigoBDNS>
Aviso legal de reutilización: https://www.infosubvenciones.es/bdnstrans/GE/es/avisolegal (se citan y enlazan los
datos; no se redistribuye la base). Uso moderado: una petición por segundo y tope de detalles por ejecución.

  python3 -I src/bdns_sweep.py --dias 7 [--json work/bdns.json] [--md work/bdns.md] [--min-presupuesto 100000] [--max-detalles 40]

Salida: filas con el esquema de `datasets` (dataset "subvenciones") para `senales`/`agenda`: código BDNS, órgano (nivel1/2/3),
descripción, fecha de recepción, presupuesto total, tipo, beneficiarios, sectores, regiones, plazo de solicitud (si consta),
URL de la convocatoria en la BDNS y de las bases reguladoras. Los plazos con fecha pasan además a `agenda_candidatas`.
"""
import argparse, datetime, json, os, sys, time, urllib.parse, urllib.request

API = "https://www.infosubvenciones.es/bdnstrans/api/convocatorias"
UA = "Moticias/1.0 (+https://moticias.com)"
CONSULTAS = ["transporte de viajeros", "transporte público", "movilidad sostenible", "autobús", "autobuses", "autocares",
             "plan de movilidad", "movilidad al trabajo", "ferrocarril", "ferroviario", "puerto", "aeropuerto", "taxi", "VTC",
             "vehículos eléctricos", "bono transporte", "transporte a la demanda", "intermodal", "logística"]
RUIDO = ["transporte escolar", "comedor", "becas", "transporte sanitario", "ambulancia", "transporte adaptado para personas"]


def get(url, intentos=3):
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": UA})
    for i in range(intentos):
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.load(r)
        except Exception as e:
            if i == intentos - 1:
                print("aviso:", url[:120], e, file=sys.stderr)
                return None
            time.sleep(2 * (i + 1))


def buscar(texto, desde, max_pag=4):
    out = []
    for page in range(max_pag):
        q = urllib.parse.urlencode({"vpd": "GE", "descripcion": texto, "order": "fechaRecepcion", "direccion": "desc", "page": page, "pageSize": 50})
        d = get(API + "/busqueda?" + q)
        time.sleep(1)
        if not d or not d.get("content"):
            break
        for c in d["content"]:
            if (c.get("fechaRecepcion") or "") < desde:
                return out
            out.append(c)
        if d.get("last"):
            break
    return out


def detalle(num):
    d = get(API + "?" + urllib.parse.urlencode({"vpd": "GE", "numConv": num}))
    time.sleep(1)
    return d


def es_ruido(desc):
    t = (desc or "").lower()
    return any(r in t for r in RUIDO)


def fila(c, det):
    det = det or {}
    org = det.get("organo") or {"nivel1": c.get("nivel1"), "nivel2": c.get("nivel2"), "nivel3": c.get("nivel3")}
    num = det.get("codigoBDNS") or c.get("numeroConvocatoria")
    return {
        "dataset": "subvenciones", "source_id": "bdns", "ref": "BDNS-" + str(num), "date": c.get("fechaRecepcion"),
        "url": "https://www.infosubvenciones.es/bdnstrans/GE/es/convocatoria/" + str(num),
        "fields": {
            "descripcion": det.get("descripcion") or c.get("descripcion"),
            "organo": " · ".join(x for x in (org.get("nivel1"), org.get("nivel2"), org.get("nivel3")) if x),
            "ambito": org.get("nivel1"), "territorio": org.get("nivel2"),
            "presupuesto_total": det.get("presupuestoTotal"), "tipo": det.get("tipoConvocatoria"),
            "beneficiarios": [b.get("descripcion") for b in det.get("tiposBeneficiarios") or []],
            "sectores": [s.get("descripcion") for s in det.get("sectores") or []],
            "regiones": [r.get("descripcion") for r in det.get("regiones") or []],
            "finalidad": det.get("descripcionFinalidad"), "mrr": det.get("mrr", c.get("mrr")),
            "abierto": det.get("abierto"), "fecha_inicio_solicitud": det.get("fechaInicioSolicitud"), "fecha_fin_solicitud": det.get("fechaFinSolicitud"),
            "texto_inicio": det.get("textInicio"), "texto_fin": det.get("textFin"),
            "url_bases": det.get("urlBasesReguladoras"), "sede": det.get("sedeElectronica"),
            "fondos": [f.get("descripcion") for f in det.get("fondos") or []] if isinstance(det.get("fondos"), list) else [],
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dias", type=int, default=7)
    ap.add_argument("--json"); ap.add_argument("--md")
    ap.add_argument("--min-presupuesto", type=float, default=0)
    ap.add_argument("--max-detalles", type=int, default=40)
    ap.add_argument("--consultas", help="lista separada por ; (por defecto, la del sector)")
    a = ap.parse_args()
    desde = (datetime.date.today() - datetime.timedelta(days=a.dias)).isoformat()
    consultas = [c.strip() for c in a.consultas.split(";")] if a.consultas else CONSULTAS
    vistos, hits = {}, []
    for t in consultas:
        for c in buscar(t, desde):
            n = c.get("numeroConvocatoria")
            if n in vistos or es_ruido(c.get("descripcion")):
                continue
            vistos[n] = t
            hits.append(c)
    hits.sort(key=lambda c: c.get("fechaRecepcion") or "", reverse=True)
    filas, agenda = [], []
    for c in hits[: a.max_detalles]:
        det = detalle(c.get("numeroConvocatoria"))
        f = fila(c, det)
        pres = f["fields"].get("presupuesto_total") or 0
        if a.min_presupuesto and pres and pres < a.min_presupuesto:
            continue
        f["fields"]["consulta"] = vistos.get(c.get("numeroConvocatoria"))
        filas.append(f)
        fin = f["fields"].get("fecha_fin_solicitud")
        if fin and fin >= datetime.date.today().isoformat():
            agenda.append({"date": fin, "kind": "plazo", "mode": "transversal", "authority": f["fields"]["organo"],
                           "title": "Fin del plazo de solicitud: " + (f["fields"]["descripcion"] or "")[:140],
                           "amount": pres or None, "url": f["url"], "source": "BDNS " + f["ref"]})
    res = {"generated_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"), "desde": desde, "consultas": consultas,
           "encontradas": len(hits), "detalladas": len(filas), "datasets": filas, "agenda_candidatas": agenda,
           "aviso_legal": "https://www.infosubvenciones.es/bdnstrans/GE/es/avisolegal"}
    if a.json:
        os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True)
        json.dump(res, open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if a.md:
        l = ["# BDNS · convocatorias de transporte y movilidad desde %s (%d encontradas, %d detalladas)" % (desde, len(hits), len(filas)), ""]
        for f in filas:
            x = f["fields"]
            pres = ("%s €" % format(int(x["presupuesto_total"]), ",").replace(",", ".")) if x.get("presupuesto_total") else "importe no consta"
            plazo = x.get("fecha_fin_solicitud") or (x.get("texto_fin") or "plazo no consta")
            l.append("- **%s** · %s · %s · %s · plazo: %s · [BDNS](%s)%s" % (f["date"], x["organo"], (x["descripcion"] or "")[:160], pres, plazo, f["url"],
                                                                          (" · [bases](%s)" % x["url_bases"]) if x.get("url_bases") else ""))
        os.makedirs(os.path.dirname(os.path.abspath(a.md)), exist_ok=True)
        open(a.md, "w", encoding="utf-8").write("\n".join(l) + "\n")
    print(json.dumps({k: res[k] for k in ("desde", "encontradas", "detalladas")} | {"agenda": len(agenda)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
