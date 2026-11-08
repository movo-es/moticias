#!/usr/bin/env python3
"""MOTICIAS · Taxonomía de tres ejes (modo · tema · territorio) y diccionario de sinónimos. Solo biblioteca estándar.

Lee `verticals/<vertical>.json` → `taxonomia` y `busqueda`. Lo usan:
  - src/buscador.py (sinónimos, detección de territorio, vecinos),
  - src/export_search_index.py (índice del buscador web),
  - src/ghost_publish.py (etiquetas de modo, tema y territorio),
  - la edición diaria, al clasificar cada pieza nueva.

Uso directo (clasificar lo publicado):
  python3 -I src/taxonomia.py informe            # tabla con la clasificación propuesta para cada pieza, sin tocar nada
  python3 -I src/taxonomia.py aplicar            # escribe modo, submodo, temas y territorios en las piezas que no los tengan
  python3 -I src/taxonomia.py aplicar --forzar   # recalcula también las ya clasificadas (respeta `taxonomia_manual: true`)
  python3 -I src/taxonomia.py pieza data/articles/<id>.json   # clasificación de una sola pieza (JSON)
"""
import glob, json, os, re, sys, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def plano(s):
    """Minúsculas, sin tildes, solo letras/números/espacios. «Prórroga tácita» → «prorroga tacita»."""
    s = unicodedata.normalize("NFKD", str(s or ""))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9ñ/ ]+", " ", s.lower().replace("ñ", "ñ")).strip()


def raiz(w):
    """Raíz tosca para plurales y derivados: autobuses→autobus, concesiones→concesion, licitación→licitac."""
    for suf in ("ciones", "siones", "iones", "es", "s"):
        if w.endswith(suf) and len(w) - len(suf) >= 4:
            w = w[: -len(suf)] + ("ion" if suf in ("ciones", "siones", "iones") else "")
            break
    return w[:7] if len(w) > 7 else w


def cargar_vertical(vertical="movilidad"):
    return json.load(open(os.path.join(ROOT, "verticals", vertical + ".json"), encoding="utf-8"))


class Taxonomia:
    def __init__(self, vertical="movilidad"):
        v = cargar_vertical(vertical)
        self.tax = v["taxonomia"]
        self.busqueda = v.get("busqueda", {})
        self.modos = {m["id"]: m for m in self.tax["modos"]}
        self.submodos = {s["id"]: (m["id"], s) for m in self.tax["modos"] for s in m["submodos"]}
        self.temas = {t["id"]: t for t in self.tax["temas"]}
        self.territorios = {t["id"]: t for t in self.tax["territorios"]}
        # alias planos → id (frases de varias palabras incluidas)
        self._alias_sub = [(plano(a), s["id"]) for m in self.tax["modos"] for s in m["submodos"] for a in s["alias"]]
        self._alias_tema = [(plano(a), t["id"]) for t in self.tax["temas"] for a in t["alias"]]
        self._alias_terr = [(plano(a), t["id"]) for t in self.tax["territorios"] for a in t["alias"]]
        # sinónimos: palabra plana → índice de grupo
        self.grupos = [[plano(w) for w in g] for g in self.busqueda.get("sinonimos", [])]
        self._sin = {}
        for i, g in enumerate(self.grupos):
            for w in g:
                self._sin.setdefault(w, set()).add(i)
                self._sin.setdefault(raiz(w), set()).add(i)

    # ---- sinónimos -------------------------------------------------------------------------------------------------
    def expandir(self, termino):
        """Términos equivalentes a uno (incluido él mismo), planos."""
        t = plano(termino)
        out = {t}
        for i in self._sin.get(t, set()) | self._sin.get(raiz(t), set()):
            out.update(self.grupos[i])
        return sorted(out)

    # ---- territorio -------------------------------------------------------------------------------------------------
    def territorios_en(self, texto, solo_ccaa=False):
        """Ids de territorio citados en un texto (alias de palabra completa). Orden: más veces citado primero."""
        t = " " + plano(texto) + " "
        cuenta = {}
        for alias, tid in self._alias_terr:
            if solo_ccaa and self.territorios[tid]["tipo"] != "ccaa":
                continue
            n = t.count(" " + alias + " ")
            if n:
                cuenta[tid] = cuenta.get(tid, 0) + n * (2 if " " in alias else 1)
        return [k for k, _ in sorted(cuenta.items(), key=lambda kv: -kv[1])]

    def vecinos(self, tid):
        return list(self.territorios.get(tid, {}).get("vecinos", []))

    def nombre_territorio(self, tid):
        return self.territorios.get(tid, {}).get("nombre", tid)

    # ---- modo y tema -------------------------------------------------------------------------------------------------
    def submodos_en(self, texto):
        t = " " + plano(texto) + " "
        cuenta = {}
        for alias, sid in self._alias_sub:
            n = t.count(" " + alias + " ")
            if n:
                cuenta[sid] = cuenta.get(sid, 0) + n * (2 if " " in alias else 1)
        return [k for k, _ in sorted(cuenta.items(), key=lambda kv: -kv[1])]

    def temas_en(self, texto):
        t = " " + plano(texto) + " "
        cuenta = {}
        for alias, tid in self._alias_tema:
            n = t.count(" " + alias + " ")
            if n:
                cuenta[tid] = cuenta.get(tid, 0) + n * (2 if " " in alias else 1)
        return [k for k, _ in sorted(cuenta.items(), key=lambda kv: -kv[1])]

    # ---- clasificación de una pieza -------------------------------------------------------------------------------------
    SUBSECTOR_A_SUBMODO = {
        "autobús": "autobus", "ferrocarril": "ferrocarril", "carretera": "carretera", "urbano": "urbano",
        "aéreo": "aerolineas", "aerolíneas": "aerolineas", "aeropuertos": "aeropuertos", "carga aérea": "logistica-aire",
        "puertos": "puertos", "marítimo": "maritimo", "naviero": "maritimo", "regulación marítima": "maritimo",
        "ferrocarril de mercancías": "logistica-tierra", "multimodal": "logistica-tierra", "transversal": "transversal",
    }
    SECCION_A_TEMA = {"regulacion": "regulacion", "licitaciones": "concesiones", "analisis": "analisis", "tecnologia": "tecnologia"}
    PISTAS_ESTADO = ("ministerio", "consejo de ministros", "moncloa", "sede de adif", "direccion general", "cortes", "congreso", "boe")

    def clasificar(self, a):
        """Devuelve {modo, submodo, temas, territorios} para una pieza (dict con los campos del manual operativo)."""
        cab = " ".join(str(a.get(k) or "") for k in ("kicker", "title", "subtitle"))
        cab_tags = cab + " " + " ".join(a.get("tags") or [])
        cuerpo = " ".join(str(a.get(k) or "") for k in ("summary", "why", "relevance_for")) + " " + " ".join(a.get("actors") or [])
        geo = (a.get("geo") or {}).get("place", "") if isinstance(a.get("geo"), dict) else ""

        # modo / submodo: subsector manda; «aéreo» y «marítimo» se afinan por alias; sección logística fuerza logistica-*
        sub = self.SUBSECTOR_A_SUBMODO.get(a.get("subsector") or "")
        hallados = self.submodos_en(cab_tags)
        if a.get("subsector") == "aéreo":
            sub = "aeropuertos" if hallados and hallados[0] == "aeropuertos" else "aerolineas"
        if a.get("subsector") == "marítimo":
            sub = "puertos" if hallados and hallados[0] == "puertos" else "maritimo"
        if a.get("subsector") == "multimodal" and a.get("section") != "logistica":
            sub = "transversal"
        if a.get("section") == "logistica":
            sub = {"puertos": "logistica-mar", "maritimo": "logistica-mar", "aerolineas": "logistica-aire", "aeropuertos": "logistica-aire",
                   "logistica-mar": "logistica-mar", "logistica-aire": "logistica-aire"}.get(sub, "logistica-tierra")
            for h in hallados:
                if h.startswith("logistica-"):
                    sub = h
                    break
        if not sub:
            hallados = hallados or self.submodos_en(cuerpo)
            sub = hallados[0] if hallados else "transversal"
        modo = self.submodos[sub][0]

        # temas: sección → tema principal; después alias de cabecera+etiquetas; máximo 2
        temas = []
        if a.get("kind") == "analisis":
            temas.append("analisis")
        t0 = self.SECCION_A_TEMA.get(a.get("section") or "")
        if t0 and t0 not in temas:
            temas.append(t0)
        for t in self.temas_en(cab_tags) + self.temas_en(cuerpo):
            if t not in temas and t != "analisis":
                temas.append(t)
            if len(temas) >= 2:
                break
        if not temas:
            temas = ["empresas"]

        # territorios: etiquetas y cabecera primero; después geo; después cuerpo. Sede estatal en Madrid → estado, no Madrid
        terr = self.territorios_en(cab_tags)
        geo_terr = self.territorios_en(geo)
        geo_p = plano(geo)
        if any(p in geo_p for p in self.PISTAS_ESTADO):
            geo_terr = ["estado"] + [t for t in geo_terr if t != "madrid"]
        for t in geo_terr + self.territorios_en(cuerpo):
            if t not in terr:
                terr.append(t)
        # «estado» en cabecera por alias de empresa pública (Renfe, Adif, Aena) no desplaza a una comunidad citada
        ccaa = [t for t in terr if self.territorios[t]["tipo"] == "ccaa"]
        ambitos = [t for t in terr if self.territorios[t]["tipo"] == "ambito"]
        terr = (ccaa[:3] + ambitos[:1]) if ccaa else (ambitos[:1] or ["estado"])
        return {"modo": modo, "submodo": sub, "temas": temas, "territorios": terr}


def _articulos(data_dir):
    return sorted(glob.glob(os.path.join(data_dir, "articles", "*.json")))


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("accion", choices=["informe", "aplicar", "pieza"])
    ap.add_argument("ruta", nargs="?")
    ap.add_argument("--data", default=os.path.join(ROOT, "data"))
    ap.add_argument("--forzar", action="store_true")
    ap.add_argument("--vertical", default="movilidad")
    a = ap.parse_args()
    tx = Taxonomia(a.vertical)
    if a.accion == "pieza":
        print(json.dumps(tx.clasificar(json.load(open(a.ruta, encoding="utf-8"))), ensure_ascii=False))
        return
    cambiadas = 0
    for p in _articulos(a.data):
        d = json.load(open(p, encoding="utf-8"))
        c = tx.clasificar(d)
        if a.accion == "informe":
            print("%-60s %-10s %-16s %-24s %s" % (d["id"][:60], d.get("section"), c["submodo"], "+".join(c["temas"]), ",".join(c["territorios"])))
            continue
        if d.get("taxonomia_manual") or (not a.forzar and all(k in d for k in c)):
            continue
        d.update(c)
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        open(p, "a", encoding="utf-8").write("\n")
        cambiadas += 1
    if a.accion == "aplicar":
        print("piezas clasificadas:", cambiadas)


if __name__ == "__main__":
    main()
