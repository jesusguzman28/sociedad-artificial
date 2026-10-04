# -*- coding: utf-8 -*-
"""Construye el sitio web interactivo (carpeta ../docs para GitHub Pages): datos.js con los resultados, copia del simulador,
PDF del manuscrito, figuras PNG y CSV. El index.html es estático y lee datos.js."""
import csv, json, os, shutil, math
import numpy as np
from scipy import stats

AQUI = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.dirname(AQUI); DOCS = os.path.join(RAIZ, "docs")
for d in ["", "figuras", "datos"]: os.makedirs(os.path.join(DOCS, d), exist_ok=True)

def leer(nombre):
    with open(os.path.join(AQUI, "datos", nombre), encoding="utf-8") as f:
        return [{k: (float(v) if k not in ("exp", "nombre", "nombreMapa", "nombreSistema") else v) for k, v in r.items()} for r in csv.DictReader(f)]
rep = leer("replicas.csv"); mapas = leer("mapas.csv")
with open(os.path.join(AQUI, "datos", "series.json"), encoding="utf-8") as f: series = json.load(f)
with open(os.path.join(AQUI, "datos", "mapas_series.json"), encoding="utf-8") as f: mseries = json.load(f)
with open(os.path.join(AQUI, "datos", "reservas.json"), encoding="utf-8") as f: reservas = json.load(f)

SIS = {3: "Anarquía primitiva", 1: "Anarcocapitalismo", 4: "Capitalismo con Estado mínimo", 5: "Socialdemocracia", 6: "Socialismo (planificación parcial)", 2: "Comunismo"}
MAPAS = {0: "4 oasis", 1: "Río", 2: "Lago central", 3: "Dos oasis lejanos", 4: "Costa", 5: "Muchos charcos"}
METRICAS = [("pob", "Población", 0), ("prod", "Producción de comida por mes", 0), ("prodPc", "Producción por persona y mes", 2), ("gini", "Desigualdad (Gini de reservas)", 2),
            ("ataq", "Ataques por mes", 1), ("cultivos", "Parcelas cultivadas", 0), ("hambrientos", "Hambrientos (%)", 0), ("ahorro", "Reserva media de comida", 1),
            ("esperanza", "Edad media al morir (años)", 1), ("natalidad", "Natalidad (por 100 personas y año)", 2), ("mayorCiudad", "Mayor ciudad (hogares)", 0),
            ("casas", "Hogares ocupados", 0), ("def", "Defensa media", 2), ("herr", "Herramienta media", 2), ("intercambios", "Intercambios por mes", 1), ("precioAgua", "Precio del agua", 2)]

def resumen(v):
    v = np.array(v, float); n = len(v); m = float(v.mean()); sd = float(v.std(ddof=1)) if n > 1 else 0.0
    return {"media": m, "sd": sd, "ic": float(stats.t.ppf(0.975, n - 1) * sd / math.sqrt(n)) if n > 1 else 0.0, "n": n}
def welch(a, b):
    a, b = np.array(a, float), np.array(b, float)
    if len(a) < 2 or len(b) < 2 or (a.std(ddof=1) == 0 and b.std(ddof=1) == 0): return {"p": None, "d": None}
    t, p = stats.ttest_ind(a, b, equal_var=False); sp = math.sqrt(((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1)) / (len(a) + len(b) - 2))
    return {"p": float(p), "d": float((a.mean() - b.mean()) / sp) if sp > 0 else None}

# Experimento 1: por sistema
exp1 = {}
for s in SIS:
    filas = [r for r in rep if r["exp"] == "sistemas" and int(r["nivel"]) == s]
    exp1[s] = {"nombre": SIS[s], "n": len(filas), "extintos": sum(int(r["extinto"]) for r in filas), "metricas": {k: resumen([r[k] for r in filas]) for k, _, _ in METRICAS},
               "valores": {k: [round(r[k], 3) for r in filas] for k, _, _ in METRICAS},
               "vsAncap": {k: welch([r[k] for r in filas], [r[k] for r in rep if r["exp"] == "sistemas" and int(r["nivel"]) == 1]) for k, _, _ in METRICAS} if s != 1 else {}}
series1 = {}
for s in SIS:
    ss = [x["serie"] for x in series if x["exp"] == "sistemas" and x["nivel"] == s]; L = min(len(x) for x in ss)
    series1[s] = {"t": [ss[0][j]["t"] / 12 for j in range(L)], **{k: [float(np.mean([x[j][k] for x in ss])) for j in range(L)] for k in ("pob", "prod", "gini", "ataq")}}
# Experimento 2: impuesto
exp2 = []
for imp in sorted({r["nivel"] for r in rep if r["exp"] == "impuesto"}):
    filas = [r for r in rep if r["exp"] == "impuesto" and r["nivel"] == imp]
    exp2.append({"impuesto": imp, "n": len(filas), "metricas": {k: resumen([r[k] for r in filas]) for k, _, _ in METRICAS}})
# Experimento 3: mapa × sistema
exp3 = {}
for m in MAPAS:
    for s in SIS:
        filas = [r for r in mapas if int(r["mapa"]) == m and int(r["sistema"]) == s]
        exp3[f"{m}_{s}"] = {"n": len(filas), "extintos": sum(int(r["extinto"]) for r in filas), "metricas": {k: resumen([r[k] for r in filas]) for k, _, _ in METRICAS if k in filas[0]}}
geo = {}
for m in MAPAS:
    filas = [r for r in mapas if int(r["mapa"]) == m]
    geo[m] = {"nombre": MAPAS[m], "celdasAgua": float(np.mean([r["celdasAgua"] for r in filas])), "celdasFertiles": float(np.mean([r["celdasFertiles"] for r in filas])), "distMediaAgua": float(np.mean([r["distMediaAgua"] for r in filas])),
              "pob": float(np.mean([r["pob"] for r in filas])), "prod": float(np.mean([r["prod"] for r in filas])), "gini": float(np.mean([r["gini"] for r in filas])), "ataq": float(np.mean([r["ataq"] for r in filas])), "intercambios": float(np.mean([r["intercambios"] for r in filas])), "ciudades": float(np.mean([r["ciudades"] for r in filas])), "migraciones": float(np.mean([r["migraciones"] for r in filas]))}
series3 = {}
for m in MAPAS:
    for s in SIS:
        ss = [x["pob"] for x in mseries if x["mapa"] == m and x["sistema"] == s]; L = min(len(x) for x in ss)
        series3[f"{m}_{s}"] = [float(np.mean([x[j] for x in ss])) for j in range(L)]
# Histogramas de reservas
hist = {}
for k, v in reservas.items():
    c, b = np.histogram(np.array(v, float), bins=np.arange(0, 42, 2)); hist[k] = {"conteos": c.tolist(), "bordes": b.tolist(), "n": len(v), "media": float(np.mean(v)), "sobre20": float((np.array(v) > 20).mean() * 100)}

VALIDACION = [
    ["Capacidad de carga", "Malthus (1798); Epstein y Axtell (1996)", "209 personas con un tercio de la fertilidad frente a 303 con la normal; población estable (variación 3 %)", True],
    ["Riqueza sesgada", "Epstein y Axtell (1996); Pareto", "Gini 0,34; media 6,1 mayor que mediana 5,4", True],
    ["Redistribución total baja la producción", "Okun (1975)", "Producción 106 por mes sin reparto frente a 13 con reparto total", True],
    ["Propiedad protegida reduce depredación y sube inversión", "Demsetz (1967); North (1990)", "33,4 ataques por mes en anarquía frente a 10,8 con Estado; cultivos 18 frente a 28", True],
    ["Fecundidad y población", "Verhulst (1838)", "201 frente a 301 personas", True],
    ["Asentamiento junto al agua", "Von Thünen (1826); Christaller (1933)", "Viviendas a 3,9 casillas del agua frente a 7,8 de la tierra en general", True],
]
datos = {"sistemas": {str(k): v for k, v in SIS.items()}, "mapas": {str(k): v for k, v in MAPAS.items()}, "metricas": METRICAS, "exp1": {str(k): v for k, v in exp1.items()}, "series1": {str(k): v for k, v in series1.items()},
         "exp2": exp2, "exp3": exp3, "geo": {str(k): v for k, v in geo.items()}, "series3": series3, "reservas": hist, "validacion": VALIDACION,
         "ordenSistemas": [3, 1, 4, 5, 6, 2], "ordenMapas": [0, 1, 2, 3, 4, 5], "semillas": "2024 + 7919·r", "fecha": "octubre de 2026"}
with open(os.path.join(DOCS, "datos.js"), "w", encoding="utf-8") as f:
    f.write("window.DATOS = " + json.dumps(datos, ensure_ascii=False) + ";\n")
# copias
shutil.copy(os.path.join(RAIZ, "mundos.html"), os.path.join(DOCS, "mundos.html"))
pdf = os.path.join(AQUI, "manuscrito.pdf")
if os.path.exists(pdf): shutil.copy(pdf, os.path.join(DOCS, "manuscrito.pdf"))
for nombre in os.listdir(os.path.join(AQUI, "figuras")):
    if nombre.endswith(".png"): shutil.copy(os.path.join(AQUI, "figuras", nombre), os.path.join(DOCS, "figuras", nombre))
for nombre in ["replicas.csv", "mapas.csv"]: shutil.copy(os.path.join(AQUI, "datos", nombre), os.path.join(DOCS, "datos", nombre))
print("sitio construido en", DOCS, "| datos.js", os.path.getsize(os.path.join(DOCS, "datos.js")) // 1024, "KB")
