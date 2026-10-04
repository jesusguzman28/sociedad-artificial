# -*- coding: utf-8 -*-
"""Análisis estadístico del experimento definitivo y generación de tablas (LaTeX), figuras (PDF) y macros con los números del texto.
Entrada: datos/replicas.csv, datos/series.json. Salida: tablas/*.tex, figuras/*.pdf, macros.tex.
Estadística: media, desviación estándar, IC 95 % (t de Student), prueba t de Welch bilateral y d de Cohen frente al nivel base."""
import csv, json, math, os
from collections import defaultdict
from scipy import stats
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def guardar(fig, nombre, **kw):
    """Guarda PDF y PNG; si otro programa tiene abierto el PDF, avisa y conserva el anterior."""
    for ext, extra in (("pdf", {}), ("png", {"dpi": 150})):
        try: fig.savefig(os.path.join(AQUI, "figuras", nombre + "." + ext), **extra, **kw)
        except PermissionError: print("AVISO: no se pudo escribir figuras/" + nombre + "." + ext + " (abierto en otro programa); se conserva el anterior")

AQUI = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(AQUI, "tablas"), exist_ok=True); os.makedirs(os.path.join(AQUI, "figuras"), exist_ok=True)
with open(os.path.join(AQUI, "datos", "replicas.csv"), encoding="utf-8") as f:
    FILAS = [{k: (float(v) if k not in ("exp", "nombre") else v) for k, v in r.items()} for r in csv.DictReader(f)]
with open(os.path.join(AQUI, "datos", "series.json"), encoding="utf-8") as f:
    SERIES = json.load(f)

NOMBRE_SIS = {3: "Anarquía primitiva", 1: "Anarcocapitalismo", 4: "Capitalismo con Estado mínimo", 5: "Socialdemocracia", 6: "Socialismo (planif. parcial)", 2: "Comunismo"}
ORDEN_SIS = [3, 1, 4, 5, 6, 2]
METRICAS = [("pob", "Población", 0), ("prod", "Producción (comida/mes)", 0), ("prodPc", "Producción por persona", 2), ("gini", "Gini de reservas", 2),
            ("ataq", "Ataques por mes", 1), ("cultivos", "Parcelas cultivadas", 0), ("hambrientos", "Hambrientos (%)", 0), ("ahorro", "Reserva media", 1),
            ("esperanza", "Edad media al morir (años)", 1), ("natalidad", "Natalidad (por 100 y año)", 1), ("mayorCiudad", "Mayor ciudad (hogares)", 0),
            ("def", "Defensa media", 2), ("intercambios", "Intercambios por mes", 1), ("precioAgua", "Precio del agua", 2)]
COLORES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#4a3aa7", "#e34948"]

def grupos(exp):
    g = defaultdict(list)
    for r in FILAS:
        if r["exp"] == exp: g[r["nivel"]].append(r)
    return g

def resumen(vals):
    v = np.array(vals, dtype=float); n = len(v); m = v.mean(); sd = v.std(ddof=1) if n > 1 else float("nan")
    ic = stats.t.ppf(0.975, n - 1) * sd / math.sqrt(n) if n > 1 else float("nan")
    return m, sd, ic, n

def welch(a, b):
    a, b = np.array(a, float), np.array(b, float)
    if len(a) < 2 or len(b) < 2 or (a.std(ddof=1) == 0 and b.std(ddof=1) == 0): return float("nan"), float("nan"), float("nan")
    t, p = stats.ttest_ind(a, b, equal_var=False)
    sp = math.sqrt(((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1)) / (len(a) + len(b) - 2))
    d = (a.mean() - b.mean()) / sp if sp > 0 else float("nan")
    return t, p, d

def fnum(x, dec):
    if x is None or (isinstance(x, float) and math.isnan(x)): return "--"
    return f"{x:,.{dec}f}".replace(",", "\\,").replace(".", ",")

def fp(p):
    if math.isnan(p): return "--"
    return "$p<0{,}001$" if p < 0.001 else "$p=" + f"{p:.3f}".replace(".", "{,}") + "$"

def esc(s): return s.replace("%", "\\%").replace("&", "\\&")

macros = {}
def macro(nombre, valor): macros[nombre] = valor

# ------------------------------------------------------------------ Experimento 1: sistemas
G = grupos("sistemas")
niveles = [s for s in ORDEN_SIS if float(s) in G]
base = float(niveles[0])
# Tabla principal: media ± IC95 por sistema para las métricas clave
claves_tabla = ["pob", "prod", "gini", "ataq", "cultivos", "hambrientos", "esperanza", "mayorCiudad"]
with open(os.path.join(AQUI, "tablas", "sistemas.tex"), "w", encoding="utf-8") as f:
    f.write("\\begin{tabular}{l" + "r" * len(claves_tabla) + "}\n\\toprule\nSistema & " + " & ".join(esc(dict((k, n) for k, n, d in METRICAS)[k]) for k in claves_tabla) + " \\\\\n\\midrule\n")
    for s in niveles:
        reps = G[float(s)]
        celdas = []
        for k in claves_tabla:
            dec = dict((kk, d) for kk, n, d in METRICAS)[k]
            m, sd, ic, n = resumen([r[k] for r in reps]); celdas.append(f"{fnum(m, dec)} $\\pm$ {fnum(ic, dec)}")
        ext = sum(int(r["extinto"]) for r in reps)
        f.write(f"{NOMBRE_SIS[s]}{' (' + str(ext) + ' ext.)' if ext else ''} & " + " & ".join(celdas) + " \\\\\n")
    f.write("\\bottomrule\n\\end{tabular}\n")
# Tabla de pruebas frente a la base (anarquía primitiva) y frente al anarcocapitalismo
def tabla_pruebas(nombre_archivo, ref, claves):
    with open(os.path.join(AQUI, "tablas", nombre_archivo), "w", encoding="utf-8") as f:
        f.write("\\begin{tabular}{ll" + "rrr" + "}\n\\toprule\nMétrica & Sistema & Diferencia & $d$ de Cohen & Welch \\\\\n\\midrule\n")
        for k in claves:
            nombre, dec = dict((kk, (n, d)) for kk, n, d in METRICAS)[k]
            primera = True
            for s in niveles:
                if s == ref: continue
                a = [r[k] for r in G[float(s)]]; b = [r[k] for r in G[float(ref)]]
                t, p, d = welch(a, b); dif = np.mean(a) - np.mean(b)
                f.write(f"{esc(nombre) if primera else ''} & {NOMBRE_SIS[s]} & {('+' if dif >= 0 else '') + fnum(dif, dec)} & {fnum(d, 2)} & {fp(p)} \\\\\n")
                primera = False
            f.write("\\addlinespace\n")
        f.write("\\bottomrule\n\\end{tabular}\n")
tabla_pruebas("pruebas_sistemas.tex", 1, ["pob", "prod", "gini", "ataq", "cultivos"])
# Totales acumulados (robos de cosecha, migraciones, muertes)
with open(os.path.join(AQUI, "tablas", "totales.tex"), "w", encoding="utf-8") as f:
    f.write("\\begin{tabular}{lrrrrrr}\n\\toprule\nSistema & Nacimientos & Muertes por hambre & Ataques & Cosechas robadas & Migraciones & Hogares construidos \\\\\n\\midrule\n")
    for s in niveles:
        reps = G[float(s)]; med = lambda k: fnum(np.mean([r[k] for r in reps]), 0)
        f.write(f"{NOMBRE_SIS[s]} & {med('nacimientos')} & {med('hambre')} & {med('ataques')} & {med('robos')} & {med('migraciones')} & {med('casas')} \\\\\n")
    f.write("\\bottomrule\n\\end{tabular}\n")
# Macros con los números que usa el texto
for s in niveles:
    reps = G[float(s)]; tag = {3: "Anarq", 1: "Ancap", 4: "Minimo", 5: "Socdem", 6: "Social", 2: "Comun"}[s]
    for k, dec in [("pob", 0), ("prod", 0), ("gini", 2), ("ataq", 1), ("cultivos", 0), ("hambrientos", 0), ("prodPc", 2), ("esperanza", 1), ("mayorCiudad", 0), ("ahorro", 1)]:
        m, sd, ic, n = resumen([r[k] for r in reps]); macro(f"{k}{tag}", fnum(m, dec)); macro(f"{k}{tag}IC", fnum(ic, dec))
    macro(f"ext{tag}", str(sum(int(r["extinto"]) for r in reps)))
macro("nReplicas", str(len(G[base]))); macro("nSistemas", str(len(niveles)))
# comparaciones destacadas
for k, tag in [("prod", "Prod"), ("gini", "Gini"), ("pob", "Pob"), ("ataq", "Ataq"), ("cultivos", "Cult")]:
    t, p, d = welch([r[k] for r in G[5.0]], [r[k] for r in G[1.0]]); macro(f"pSocdemAncap{tag}", fp(p).replace("$", "")); macro(f"dSocdemAncap{tag}", fnum(d, 2))
    t, p, d = welch([r[k] for r in G[2.0]], [r[k] for r in G[1.0]]); macro(f"pComunAncap{tag}", fp(p).replace("$", "")); macro(f"dComunAncap{tag}", fnum(d, 2))
    t, p, d = welch([r[k] for r in G[3.0]], [r[k] for r in G[1.0]]); macro(f"pAnarqAncap{tag}", fp(p).replace("$", "")); macro(f"dAnarqAncap{tag}", fnum(d, 2))
n_comp = 5 * (len(niveles) - 1); macro("nComparaciones", str(n_comp)); macro("umbralBonferroni", fnum(0.05 / n_comp, 4))

# Figura 1: barras con IC por sistema (6 paneles)
fig, axes = plt.subplots(2, 3, figsize=(11, 6.2)); axes = axes.ravel()
paneles = [("pob", "Población", 0), ("prod", "Producción de comida por mes", 0), ("gini", "Desigualdad (Gini de reservas)", 2), ("ataq", "Ataques por mes", 1), ("cultivos", "Parcelas cultivadas", 0), ("hambrientos", "Hambrientos (%)", 0)]
etiquetas = ["Anarquía\nprimitiva", "Anarco-\ncapitalismo", "Estado\nmínimo", "Social-\ndemocracia", "Socialismo\nparcial", "Comunismo"]
for ax, (k, titulo, dec) in zip(axes, paneles):
    medias, ics = [], []
    for s in niveles:
        m, sd, ic, n = resumen([r[k] for r in G[float(s)]]); medias.append(m); ics.append(ic)
    ax.bar(range(len(niveles)), medias, yerr=ics, color=COLORES[:len(niveles)], capsize=4, width=0.62, edgecolor="none")
    ax.set_title(titulo, fontsize=10, loc="left"); ax.set_xticks(range(len(niveles))); ax.set_xticklabels([e.replace("\n", " ") for e in etiquetas[:len(niveles)]], fontsize=7, rotation=28, ha="right")
    ax.spines[["top", "right"]].set_visible(False); ax.grid(axis="y", color="#e6e3da", linewidth=0.8); ax.set_axisbelow(True); ax.tick_params(axis="y", labelsize=8)
fig.tight_layout(); guardar(fig, "sistemas_barras"); plt.close(fig)

# Figura 2: series temporales de población y producción (media de réplicas) por sistema
fig, axes = plt.subplots(1, 2, figsize=(11, 3.6))
for ax, (k, titulo) in zip(axes, [("pob", "Población"), ("prod", "Producción de comida por mes")]):
    for i, s in enumerate(niveles):
        ss = [x["serie"] for x in SERIES if x["exp"] == "sistemas" and x["nivel"] == s]
        L = min(len(x) for x in ss); t = [ss[0][j]["t"] / 12 for j in range(L)]; y = [np.mean([x[j][k] for x in ss]) for j in range(L)]
        ax.plot(t, y, color=COLORES[i], linewidth=1.8, label=NOMBRE_SIS[s])
    ax.set_title(titulo, fontsize=10, loc="left"); ax.set_xlabel("años"); ax.spines[["top", "right"]].set_visible(False); ax.grid(color="#e6e3da", linewidth=0.8); ax.set_axisbelow(True)
manejadores, etiq = axes[0].get_legend_handles_labels()
fig.legend(manejadores, etiq, loc="lower center", ncol=3, fontsize=8, frameon=False, bbox_to_anchor=(0.5, -0.02))
fig.tight_layout(rect=(0, 0.12, 1, 1)); guardar(fig, "series_sistemas", bbox_inches="tight"); plt.close(fig)

# ------------------------------------------------------------------ Experimento 2: barrido del impuesto
G2 = grupos("impuesto"); nivs = sorted(G2.keys())
with open(os.path.join(AQUI, "tablas", "impuesto.tex"), "w", encoding="utf-8") as f:
    f.write("\\begin{tabular}{rrrrrrr}\n\\toprule\nImpuesto mensual & Población & Producción/mes & Producción por persona & Reserva media & Natalidad & Gini \\\\\n\\midrule\n")
    for imp in nivs:
        reps = G2[imp]; c = []
        for k, dec in [("pob", 0), ("prod", 0), ("prodPc", 2), ("ahorro", 1), ("natalidad", 1), ("gini", 2)]:
            m, sd, ic, n = resumen([r[k] for r in reps]); c.append(f"{fnum(m, dec)} $\\pm$ {fnum(ic, dec)}")
        f.write(f"{int(imp * 100)}\\,\\% & " + " & ".join(c) + " \\\\\n")
    f.write("\\bottomrule\n\\end{tabular}\n")
# umbral: primer nivel cuya población media cae por debajo de la mitad de la del nivel 0
pob0 = np.mean([r["pob"] for r in G2[nivs[0]]]); umbral = next((imp for imp in nivs if np.mean([r["pob"] for r in G2[imp]]) < 0.5 * pob0), None)
macro("umbralImpuesto", f"{int(umbral * 100)}\\,\\%" if umbral is not None else "no alcanzado")
prev = max([imp for imp in nivs if umbral is not None and imp < umbral], default=nivs[0]); macro("umbralImpuestoPrevio", f"{int(prev * 100)}\\,\\%")
macro("pobImpCero", fnum(pob0, 0)); macro("pobImpUno", fnum(np.mean([r['pob'] for r in G2[nivs[-1]]]), 0))
macro("reservaImpCero", fnum(np.mean([r['ahorro'] for r in G2[nivs[0]]]), 1)); macro("reservaImpUno", fnum(np.mean([r['ahorro'] for r in G2[nivs[-1]]]), 1))
macro("natImpCero", fnum(np.mean([r['natalidad'] for r in G2[nivs[0]]]), 1)); macro("natImpUno", fnum(np.mean([r['natalidad'] for r in G2[nivs[-1]]]), 1))
macro("prodPcImpCero", fnum(np.mean([r['prodPc'] for r in G2[nivs[0]]]), 2)); macro("prodPcImpUno", fnum(np.mean([r['prodPc'] for r in G2[nivs[-1]]]), 2))
macro("nReplicasImp", str(len(G2[nivs[0]])))
fig, axes = plt.subplots(1, 3, figsize=(11, 3.4))
for ax, (k, titulo, dec) in zip(axes, [("pob", "Población", 0), ("prodPc", "Producción por persona y mes", 2), ("natalidad", "Natalidad (por 100 y año)", 1)]):
    xs = [imp * 100 for imp in nivs]; ys, es = [], []
    for imp in nivs:
        m, sd, ic, n = resumen([r[k] for r in G2[imp]]); ys.append(m); es.append(ic)
    ax.errorbar(xs, ys, yerr=es, color=COLORES[0], marker="o", capsize=4, linewidth=1.8)
    ax.set_title(titulo, fontsize=10, loc="left"); ax.set_xlabel("impuesto mensual (%)"); ax.spines[["top", "right"]].set_visible(False); ax.grid(color="#e6e3da", linewidth=0.8); ax.set_axisbelow(True)
fig.tight_layout(); guardar(fig, "impuesto"); plt.close(fig)

# Figura 4: distribución de reservas individuales al año 150 sin impuesto, con 20 % y con reparto total (mecanismo del colapso)
ruta_res = os.path.join(AQUI, "datos", "reservas.json")
if os.path.exists(ruta_res):
    with open(ruta_res, encoding="utf-8") as f: RES = json.load(f)
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.4), sharey=False)
    for ax, (clave, titulo, col) in zip(axes, [("sin_impuesto", "Sin impuesto", COLORES[0]), ("impuesto_20", "Impuesto mensual 20 %", COLORES[3]), ("reparto_total", "Reparto total mensual", COLORES[5])]):
        v = np.array(RES[clave], float); ax.hist(v, bins=np.arange(0, 31, 1), color=col, edgecolor="white", linewidth=0.6)
        ax.axvline(10, color="#14181f", linestyle="--", linewidth=1); ax.text(10.4, ax.get_ylim()[1] * 0.92, "10: lo que aporta cada" + chr(10) + "miembro de la pareja", fontsize=7.5, color="#14181f", va="top")
        ax.axvline(v.mean(), color="#52514e", linewidth=1); ax.set_title((titulo + chr(10) + f" n = {len(v)}, media {v.mean():.1f}, {(v >= 10).mean() * 100:.0f} % con 10 o más").replace(".", ","), fontsize=8.5, loc="left")
        ax.set_xlabel("reserva de comida por persona"); ax.spines[["top", "right"]].set_visible(False); ax.grid(axis="y", color="#e6e3da", linewidth=0.8); ax.set_axisbelow(True)
    axes[0].set_ylabel("personas"); fig.tight_layout(); guardar(fig, "reservas"); plt.close(fig)
    for clave, tag in [("sin_impuesto", "Cero"), ("impuesto_20", "Veinte"), ("reparto_total", "Total")]:
        v = np.array(RES[clave], float); macro(f"pctSobreDiez{tag}", fnum((v >= 10).mean() * 100, 0)); macro(f"nReservas{tag}", str(len(v)))

# Versiones PNG de las figuras para la web
with open(os.path.join(AQUI, "macros.tex"), "w", encoding="utf-8") as f:
    for k, v in macros.items(): f.write(f"\\newcommand{{\\{k}}}{{{v}}}\n")
print("tablas, figuras y", len(macros), "macros generadas")
