#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETL electoral → barrios.geojson  (Bogotá con Cepeda)

Reemplaza los datos electorales ilustrativos de barrios.geojson por una
estimación basada en datos reales:

  1. Patrón espacial real 2022: resultados oficiales mesa a mesa de la
     1ª vuelta presidencial 2022 (Registraduría, archivo MMV), agregados
     por puesto de votación.
  2. Geolocalización oficial de puestos (IDECA, código DIVIPOLE).
  3. Swing 2026 por localidad: calibrado con los anclajes del escrutinio
     al 98% publicados por prensa (La Silla Vacía, 2026-06-02) y
     restringido para que el agregado coincida con el resultado oficial
     de Bogotá 1ª vuelta 2026 (Cepeda 41,67%, De la Espriella 37,69%).

Cuando la Registraduría publique el archivo MMV de 2026 (o la campaña
comparta el archivo de divulgación por mesa), basta pasar
--mmv2026 <archivo.csv> para sustituir la estimación por datos reales.

Uso:
  python3 etl/build_barrios_electoral.py --data-dir <dir-datos> \
      --barrios barrios.geojson --out barrios.geojson

Insumos esperados en --data-dir:
  MMV_NACIONAL_PRESIDENTE_2022_1v.csv  (observatorio.registraduria.gov.co/anexos/MMV_NACIONAL_PRESIDENTE_2022_1v.zip)
  puestos_ideca.geojson                (datosabiertos.bogota.gov.co dataset "puesto-de-votacion", formato GeoJSON)

Dependencias: shapely (pip install shapely)
"""
import argparse, csv, json, math, sys, unicodedata
from collections import defaultdict

from shapely.geometry import shape, Point
from shapely.strtree import STRtree

DEP_BOGOTA = "16"

# --- Resultado oficial Bogotá, 1ª vuelta 2026 (resultados.registraduria.gov.co, ACT/PR/16001) ---
CEPEDA_BOG_2026 = 41.67   # % sobre votos válidos
ADLE_BOG_2026   = 37.69

# --- Anclajes por localidad: % Cepeda 2026 (escrutinio ~98%, La Silla Vacía 2026-06-02) ---
ANCHORS_2026 = {
    "KENNEDY": 44.0,
    "CIUDAD BOLIVAR": 57.0,
    "USAQUEN": 22.0,
    "ANTONIO NARINO": 40.0,
    "SUMAPAZ": 76.0,
}
# Ganador conocido por localidad (prensa): A = De la Espriella, C = Cepeda
WINNERS_2026 = {
    "ENGATIVA": "A", "ANTONIO NARINO": "A", "TEUSAQUILLO": "A", "FONTIBON": "A",
    "PUENTE ARANDA": "A", "MARTIRES": "A", "CHAPINERO": "A", "BARRIOS UNIDOS": "A",
    "USAQUEN": "A", "SUBA": "A",
    "CANDELARIA": "C", "SANTA FE": "C", "KENNEDY": "C", "BOSA": "C",
    "CIUDAD BOLIVAR": "C", "USME": "C", "SUMAPAZ": "C", "SAN CRISTOBAL": "C",
    "RAFAEL URIBE URIBE": "C", "TUNJUELITO": "C",
}

RIGHT_2022 = ("HERN", "GUTI", "GOMEZ", "MILTON")  # Rodolfo, Fico, E. Gómez, J.M. Rodríguez


def norm(s):
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return " ".join(s.upper().replace(".", " ").split()).replace("LA CANDELARIA", "CANDELARIA").replace("LOS MARTIRES", "MARTIRES")


def load_mmv(path, left=("PETRO",), right=RIGHT_2022):
    """Agrega un archivo MMV por puesto (zona, puesto) para Bogotá.

    left/right: patrones en CANNOMBRE para el campo izquierda/derecha.
    Para 2026: left=("CEPEDA",), right=("ESPRIELLA",).
    """
    pet, rig, valid = defaultdict(int), defaultdict(int), defaultdict(int)
    with open(path, encoding="latin-1") as f:
        for row in csv.DictReader(f, delimiter=";"):
            if row["DEP"] != DEP_BOGOTA:
                continue
            c = norm(row["CANNOMBRE"])
            if "NULOS" in c or "NO MARCADOS" in c:
                continue  # válidos = candidatos + en blanco
            key = (row["ZONA"], row["PUESTO"])
            v = int(row["VOTOS"])
            valid[key] += v
            if any(k in c for k in left):
                pet[key] += v
            elif any(k in c for k in right):
                rig[key] += v
    return pet, rig, valid


load_2022 = load_mmv  # alias retrocompatible


def load_divulgacion(path):
    """Archivo de divulgación preconteo (ancho fijo, sin encabezados), p.ej.
    PRE_MMV_9999.txt. Layout (38 chars):
      dep(0:2) mun(2:5) zona(5:7) puesto(7:9) mesa(9:15) ?(15:17) 9999(17:21)
      candidato(21:27) orden(27:30) votos(30:38)
    Códigos 2026 validados contra los totales oficiales del portal:
      Cepeda=('000026','001')  De la Espriella=('001003','004')
      blanco=('000000','996')  nulos=('000000','997')  no marcados=('000000','998')
    """
    CEP, ADLE = ("000026", "001"), ("001003", "004")
    NUL, NM = ("000000", "997"), ("000000", "998")
    cep, adle, valid = defaultdict(int), defaultdict(int), defaultdict(int)
    with open(path) as f:
        for ln in f:
            ln = ln.rstrip("\r\n")
            if len(ln) != 38 or ln[:2] != DEP_BOGOTA:
                continue
            cand = (ln[21:27], ln[27:30])
            if cand in (NUL, NM):
                continue  # válidos = candidatos + en blanco
            key = (ln[5:7], ln[7:9])
            v = int(ln[30:38])
            valid[key] += v
            if cand == CEP:
                cep[key] += v
            elif cand == ADLE:
                adle[key] += v
    return cep, adle, valid


def is_divulgacion(path):
    with open(path, encoding="latin-1") as f:
        ln = f.readline().rstrip("\r\n")
    return len(ln) == 38 and ln.isdigit()


def is_escrutinio(path):
    with open(path, encoding="latin-1") as f:
        ln = f.readline().rstrip("\r\n")
    return ln.startswith("9999;") and ln.count(";") >= 11


def load_escrutinio(path):
    """Escrutinio definitivo (ESCRUTINIOS_MMV_*.csv): CSV con ';' sin encabezados.
    Campos: corte;dep;mun;zona(3);puesto(2);mesa(6);cir;?;?;cand(4);orden(3);votos
    Códigos 2026 (validados contra el escrutinio oficial):
      Cepeda=('0026','001')  De la Espriella=('1003','004')
      blanco=('0000','996')  nulos=('0000','997')  no marcados=('0000','998')
    """
    CEP, ADLE = ("0026", "001"), ("1003", "004")
    NUL, NM = ("0000", "997"), ("0000", "998")
    cep, adle, valid = defaultdict(int), defaultdict(int), defaultdict(int)
    with open(path, encoding="latin-1") as f:
        for ln in f:
            p = ln.rstrip("\r\n;").split(";")
            if len(p) < 12 or p[1] != DEP_BOGOTA:
                continue
            cand = (p[9], p[10])
            if cand in (NUL, NM):
                continue  # válidos = candidatos + en blanco
            key = (p[3][-2:], p[4])  # zona a 2 dígitos para casar con IDECA
            v = int(p[11])
            valid[key] += v
            if cand == CEP:
                cep[key] += v
            elif cand == ADLE:
                adle[key] += v
    return cep, adle, valid


def load_puestos(path):
    """Puntos IDECA: código DIVIPOLE 16001+ZZ+PP → (geom, zona, localidad)."""
    out = {}
    for f in json.load(open(path, encoding="utf-8"))["features"]:
        p = f["properties"]
        cod = p["Código_del_puesto"]          # ej. 160011901
        zona, puesto = cod[5:7], cod[7:9]
        out[(zona, puesto)] = {
            "pt": shape(f["geometry"]),
            "zona": zona,
            "loc": norm(p["Nombre_de_localidad"]),
        }
    return out


def fit_swing(loc22, weights):
    """Swing 2026 por localidad.

    Anclados: swing observado (prensa). No anclados: ajuste cuadrático
    swing ~ a·p² + b·p + c sobre los anclajes, con corrección aditiva
    para que el agregado ponderado dé el resultado oficial de Bogotá.
    """
    pts = [(loc22[l], ANCHORS_2026[l] - loc22[l]) for l in ANCHORS_2026 if l in loc22]
    n = len(pts)
    sx = sum(p for p, _ in pts); sx2 = sum(p * p for p, _ in pts)
    sx3 = sum(p ** 3 for p, _ in pts); sx4 = sum(p ** 4 for p, _ in pts)
    sy = sum(s for _, s in pts); sxy = sum(p * s for p, s in pts)
    sx2y = sum(p * p * s for p, s in pts)
    # resolver sistema 3x3 (mínimos cuadrados cuadrático)
    import numpy as np
    A = np.array([[sx4, sx3, sx2], [sx3, sx2, sx], [sx2, sx, n]])
    b = np.array([sx2y, sxy, sy])
    qa, qb, qc = np.linalg.solve(A, b)

    swing = {}
    for l, p in loc22.items():
        if l in ANCHORS_2026:
            swing[l] = ANCHORS_2026[l] - p
        else:
            swing[l] = float(qa * p * p + qb * p + qc)
    # corrección: agregado ponderado debe dar CEPEDA_BOG_2026
    W = sum(weights.values())
    est = sum(weights[l] * (loc22[l] + swing[l]) for l in loc22) / W
    corr = CEPEDA_BOG_2026 - est
    free_w = sum(w for l, w in weights.items() if l not in ANCHORS_2026)
    for l in swing:
        if l not in ANCHORS_2026:
            swing[l] += corr * W / free_w
    return swing


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="etl/data")
    ap.add_argument("--barrios", default="barrios.geojson")
    ap.add_argument("--out", default="barrios.geojson")
    ap.add_argument("--mmv2026", help="CSV mesa a mesa 2026 (cuando exista): usa datos reales en vez del modelo de swing")
    ap.add_argument("--mmv2022-2v", default=None, help="CSV mesa a mesa 2ª vuelta 2022: añade p2 (Petro 2v) y g22 (crecimiento entre vueltas) por barrio")
    args = ap.parse_args()

    pet, right, valid = load_2022(f"{args.data_dir}/MMV_NACIONAL_PRESIDENTE_2022_1v.csv")

    pet2v, valid2v = {}, {}
    if args.mmv2022_2v:
        pet2v, _, valid2v = load_2022(args.mmv2022_2v)
        tp, tv = sum(pet2v.values()), sum(valid2v.values())
        print(f"2ª vuelta 2022 Bogotá: Petro {100*tp/tv:.2f}% ({tp:,}/{tv:,}) en {len(valid2v)} puestos")
    puestos = load_puestos(f"{args.data_dir}/puestos_ideca.geojson")

    # share 2022 por puesto, ubicado
    located = []
    for key in valid:
        if key not in puestos or valid[key] == 0:
            continue
        rec = {
            "key": key, "pt": puestos[key]["pt"], "loc": puestos[key]["loc"],
            "p22": 100 * pet[key] / valid[key],
            "r22": 100 * right[key] / valid[key],
            "w": valid[key],
        }
        if valid2v.get(key):
            rec["p2v"] = 100 * pet2v[key] / valid2v[key]
        located.append(rec)
    missing = [k for k in valid if k not in puestos]
    print(f"puestos 2022: {len(valid)} | geolocalizados: {len(located)} | sin punto IDECA: {len(missing)}")

    # localidades: baseline 2022 y swing 2026
    locp, locv, locr = defaultdict(int), defaultdict(int), defaultdict(int)
    for d in located:
        locv[d["loc"]] += d["w"]
        locp[d["loc"]] += d["w"] * d["p22"] / 100
        locr[d["loc"]] += d["w"] * d["r22"] / 100
    loc22 = {l: 100 * locp[l] / locv[l] for l in locv}
    locr22 = {l: 100 * locr[l] / locv[l] for l in locv}

    # ---------- MODO DATOS REALES 2026 ----------
    if args.mmv2026:
        if is_escrutinio(args.mmv2026):
            cep26, adle26, valid26 = load_escrutinio(args.mmv2026)
        elif is_divulgacion(args.mmv2026):
            cep26, adle26, valid26 = load_divulgacion(args.mmv2026)
        else:
            cep26, adle26, valid26 = load_mmv(args.mmv2026, left=("CEPEDA",), right=("ESPRIELLA",))
        tc, ta, tv = sum(cep26.values()), sum(adle26.values()), sum(valid26.values())
        print(f"2026 REAL Bogotá: Cepeda {100*tc/tv:.2f}% | ADLE {100*ta/tv:.2f}% | {len(valid26)} puestos, {tv:,} válidos")
        print(f"   (oficial: Cepeda {CEPEDA_BOG_2026}% | ADLE {ADLE_BOG_2026}%) — si difiere >0.3 pts, revisar el archivo")
        matched = sum(1 for d in located if d["key"] in valid26 and valid26[d["key"]] > 0)
        nuevos = [k for k in valid26 if k not in puestos]
        print(f"   puestos 2026 cruzados con 2022/IDECA: {matched} | puestos 2026 sin punto IDECA: {len(nuevos)}")
        for d in located:
            k = d["key"]
            if valid26.get(k):
                d["c26"] = 100 * cep26[k] / valid26[k]
                d["a26"] = 100 * adle26[k] / valid26[k]
                d["w26"] = valid26[k]
            else:
                d["c26"] = d["a26"] = None
            d["d"] = (d["c26"] - d["p22"]) if d["c26"] is not None else None
        # puestos nuevos 2026 con punto IDECA pero sin histórico 2022: añadirlos
        for k in valid26:
            if k in puestos and not any(d["key"] == k for d in located) and valid26[k] > 0:
                located.append({
                    "key": k, "pt": puestos[k]["pt"], "loc": puestos[k]["loc"],
                    "p22": None, "r22": None, "w": valid26[k], "w26": valid26[k],
                    "c26": 100 * cep26[k] / valid26[k],
                    "a26": 100 * adle26[k] / valid26[k], "d": None,
                })
        assign_and_write(located, args, real=True)
        return

    swing = fit_swing(loc22, locv)
    k_adle = ADLE_BOG_2026 / (sum(locv[l] * locr22[l] for l in locv) / sum(locv.values()))

    # factor ADLE por localidad: parte del factor global y se ajusta lo mínimo
    # para respetar el ganador conocido por prensa (margen 0.5 pts);
    # luego se renormalizan las demás para conservar el agregado oficial.
    k_loc = {l: k_adle for l in locv}
    fixed = set()
    for l in locv:
        c = loc22[l] + swing[l]
        a = locr22[l] * k_loc[l]
        wp = WINNERS_2026.get(norm(l), WINNERS_2026.get(l, "?"))
        if wp == "A" and a <= c:
            k_loc[l] = (c + 0.5) / locr22[l]; fixed.add(l)
        elif wp == "C" and a >= c:
            k_loc[l] = (c - 0.5) / locr22[l]; fixed.add(l)
    W = sum(locv.values())
    target = ADLE_BOG_2026 * W
    fixed_sum = sum(locv[l] * locr22[l] * k_loc[l] for l in fixed)
    free_base = sum(locv[l] * locr22[l] * k_adle for l in locv if l not in fixed)
    scale = (target - fixed_sum) / free_base if free_base else 1.0
    for l in k_loc:
        if l not in fixed:
            k_loc[l] = k_adle * scale

    print("\nlocalidad                 p22    swing   c26e   a26e  ganador(modelo/prensa)")
    issues = 0
    for l in sorted(locv, key=lambda x: -locv[x]):
        c = loc22[l] + swing[l]
        a = locr22[l] * k_loc[l]
        wm = "C" if c >= a else "A"
        wp = WINNERS_2026.get(l, "?")
        flag = " <-- REVISAR" if wp != "?" and wm != wp else ""
        if flag: issues += 1
        print(f"{l:24} {loc22[l]:6.1f} {swing[l]:+7.1f} {c:6.1f} {a:6.1f}   {wm}/{wp}{flag}")
    print(f"\nlocalidades con ganador inconsistente vs prensa: {issues}")

    # por puesto: c/a/d 2026 estimados.
    # Swing logístico dentro de cada localidad: el retroceso observado entre
    # localidades sigue la forma p·(1−p) (máximo cerca del 50%, menor en los
    # extremos: AN −7.1 con 47%, Usaquén −3.6 con 26%, Sumapaz −3.5 con 79%).
    # Se aplica la misma forma dentro de la localidad: cada puesto retrocede
    # según su nivel 2022 real, manteniendo el promedio de la localidad anclado.
    def logit(p):  return math.log(p / (1 - p))
    def sigm(x):   return 1 / (1 + math.exp(-x))

    by_loc = defaultdict(list)
    for d in located:
        by_loc[d["loc"]].append(d)
    for l, ds in by_loc.items():
        target = (loc22[l] + swing[l]) / 100
        lo, hi = -3.0, 3.0
        for _ in range(60):
            mid = (lo + hi) / 2
            W = sum(d["w"] for d in ds)
            est = sum(d["w"] * sigm(logit(min(max(d["p22"] / 100, .005), .995)) + mid) for d in ds) / W
            if est < target: lo = mid
            else: hi = mid
        delta = (lo + hi) / 2
        for d in ds:
            p = min(max(d["p22"] / 100, .005), .995)
            d["c26"] = max(1.0, min(97.0, 100 * sigm(logit(p) + delta)))
            d["a26"] = max(1.0, min(97.0, d["r22"] * k_loc[l]))
            d["d"] = d["c26"] - d["p22"]

    assign_and_write(located, args, real=False)


def assign_and_write(located, args, real):
    """Asignación puesto→barrio (dentro del polígono; si no hay, el más cercano)
    y escritura del geojson. real=True: c/a/d vienen de conteos 2026 (campo 'src')."""
    bar = json.load(open(args.barrios, encoding="utf-8"))
    geoms = [shape(f["geometry"]) for f in bar["features"]]
    usable = [d for d in located if d.get("c26") is not None]
    pts = [d["pt"] for d in usable]
    tree = STRtree(pts)
    pt_index = {id(p): i for i, p in enumerate(pts)}

    def to_idx(i):
        return int(i) if isinstance(i, (int,)) or hasattr(i, "__index__") else pt_index[id(i)]

    n_inside, n_nearest = 0, 0
    for f, g in zip(bar["features"], geoms):
        idxs = [to_idx(i) for i in tree.query(g)]
        idxs = [i for i in idxs if g.contains(pts[i])]
        if idxs:
            n_inside += 1
        else:
            n_nearest += 1
            idxs = [to_idx(tree.nearest(g.centroid))]
        sel = [usable[i] for i in idxs]
        wkey = "w26" if real else "w"
        W = sum(s.get(wkey) or s["w"] for s in sel)
        c26 = sum(s["c26"] * (s.get(wkey) or s["w"]) for s in sel) / W
        a26 = sum(s["a26"] * (s.get(wkey) or s["w"]) for s in sel) / W
        seld = [s for s in sel if s.get("d") is not None]
        p = f["properties"]
        p["c"] = round(c26, 1)
        p["a"] = round(a26, 1)
        if seld:
            Wd = sum(s.get(wkey) or s["w"] for s in seld)
            p["d"] = round(sum(s["d"] * (s.get(wkey) or s["w"]) for s in seld) / Wd, 1)
        p["w"] = "C" if c26 >= a26 else "A"
        p["np"] = len(sel)              # nº de puestos que sustentan el dato
        if real:
            p["src"] = "2026"           # conteo real 2026 por puesto
        sel2 = [s for s in sel if s.get("p2v") is not None]
        if sel2:
            W2 = sum(s["w"] for s in sel2)
            p2v = sum(s["p2v"] * s["w"] for s in sel2) / W2
            p1v = sum(s["p22"] * s["w"] for s in sel2) / W2
            p["p2"] = round(p2v, 1)     # Petro 2ª vuelta 2022 (real)
            p["g22"] = round(p2v - p1v, 1)  # crecimiento entre vueltas 2022 (real)
    print(f"\nbarrios con puesto propio: {n_inside} | asignados al puesto más cercano: {n_nearest}")

    wkey = "w26" if real else "w"
    Wt = sum(d.get(wkey) or d["w"] for d in usable)
    cc = sum(d["c26"] * (d.get(wkey) or d["w"]) for d in usable) / Wt
    aa = sum(d["a26"] * (d.get(wkey) or d["w"]) for d in usable) / Wt
    fuente = "conteo real 2026" if real else "ponderado por votos 2022"
    print(f"validación citywide ({fuente}): Cepeda {cc:.2f}% (oficial {CEPEDA_BOG_2026}) | ADLE {aa:.2f}% (oficial {ADLE_BOG_2026})")

    json.dump(bar, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"escrito: {args.out}")


if __name__ == "__main__":
    main()
