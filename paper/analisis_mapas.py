# -*- coding: utf-8 -*-
"""Análisis del experimento factorial geografía × sistema (datos/mapas.csv).
Genera: tablas/mapas_geo.tex, tablas/mapas_matriz_*.tex, tablas/anova.tex, tablas/concordancia.tex, tablas/contrastes_mapas.tex,
figuras/mapas_heatmap.pdf, figuras/mapas_lineas.pdf y macros_mapas.tex."""
import csv, math, os, itertools
from collections import defaultdict
import numpy as np
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def guardar(fig, nombre, **kw):
    """Guarda PDF y PNG; si otro programa tiene abierto el PDF, avisa y conserva el anterior."""
    for ext, extra in (("pdf", {}), ("png", {"dpi": 150})):
        try: fig.savefig(os.path.join(AQUI, "figuras", nombre + "." + ext), **extra, **kw)
        except PermissionError: print("AVISO: no se pudo escribir figuras/" + nombre + "." + ext + " (abierto en otro programa); se conserva el anterior")

AQUI = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(AQUI, "datos", "mapas.csv"), encoding="utf-8") as f:
    FILAS = [{k: (float(v) if k not in ("exp", "nombreMapa", "nombreSistema") else v) for k, v in r.items()} for r in csv.DictReader(f)]
MAPAS = [0, 1, 2, 3, 4, 5]; NOMBRE_MAPA = {0: "4 oasis", 1: "Río", 2: "Lago central", 3: "Dos oasis lejanos", 4: "Costa", 5: "Muchos charcos"}
SIS = [3, 1, 4, 5, 6, 2]; NOMBRE_SIS = {3: "Anarquía primitiva", 1: "Anarcocapitalismo", 4: "Estado mínimo", 5: "Socialdemocracia", 6: "Socialismo parcial", 2: "Comunismo"}
COLORES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#4a3aa7", "#e34948"]
G = defaultdict(list)
for r in FILAS: G[(int(r["mapa"]), int(r["sistema"]))].append(r)
NREP = len(G[(0, 3)])

def fnum(x, dec):
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))): return "--"
    return f"{x:,.{dec}f}".replace(",", "\\,").replace(".", ",")
def fp(p): return "--" if math.isnan(p) else ("$p<0{,}001$" if p < 0.001 else "$p=" + f"{p:.3f}".replace(".", "{,}") + "$")
def esc(s): return s.replace("%", "\\%").replace("&", "\\&")
def resumen(v):
    v = np.array(v, float); n = len(v); m = v.mean(); sd = v.std(ddof=1) if n > 1 else float("nan")
    return m, sd, (stats.t.ppf(0.975, n - 1) * sd / math.sqrt(n) if n > 1 else float("nan")), n
def welch(a, b):
    a, b = np.array(a, float), np.array(b, float)
    if len(a) < 2 or len(b) < 2 or (a.std(ddof=1) == 0 and b.std(ddof=1) == 0): return float("nan"), float("nan")
    t, p = stats.ttest_ind(a, b, equal_var=False)
    sp = math.sqrt(((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1)) / (len(a) + len(b) - 2))
    return p, ((a.mean() - b.mean()) / sp if sp > 0 else float("nan"))
macros = {}
def macro(k, v): macros[k] = v
macro("nRepMapas", str(NREP))

# ---------------------------------------------------------------- descripción geográfica de cada mapa
with open(os.path.join(AQUI, "tablas", "mapas_geo.tex"), "w", encoding="utf-8") as f:
    f.write("\\begin{tabular}{lrrr}\n\\toprule\nMapa & Celdas de agua & Celdas cultivables & Distancia media al agua \\\\\n\\midrule\n")
    for m in MAPAS:
        reps = [r for (mm, s), rs in G.items() if mm == m for r in rs]
        f.write(f"{NOMBRE_MAPA[m]} & {fnum(np.mean([r['celdasAgua'] for r in reps]), 0)} & {fnum(np.mean([r['celdasFertiles'] for r in reps]), 0)} & {fnum(np.mean([r['distMediaAgua'] for r in reps]), 1)} \\\\\n")
    f.write("\\bottomrule\n\\end{tabular}\n")

# ---------------------------------------------------------------- matrices mapa × sistema
for k, dec, nombre in [("pob", 0, "poblacion"), ("prod", 0, "produccion"), ("gini", 2, "gini"), ("ataq", 1, "ataques"), ("cultivos", 0, "cultivos")]:
    with open(os.path.join(AQUI, "tablas", f"mapas_matriz_{nombre}.tex"), "w", encoding="utf-8") as f:
        f.write("\\begin{tabular}{l" + "r" * len(SIS) + "}\n\\toprule\nMapa & " + " & ".join(NOMBRE_SIS[s] for s in SIS) + " \\\\\n\\midrule\n")
        for m in MAPAS:
            celdas = []
            for s in SIS:
                mu, sd, ic, n = resumen([r[k] for r in G[(m, s)]]); ext = sum(int(r["extinto"]) for r in G[(m, s)])
                celdas.append(f"{fnum(mu, dec)} $\\pm$ {fnum(ic, dec)}" + (f" ({ext} ext.)" if ext else ""))
            f.write(f"{NOMBRE_MAPA[m]} & " + " & ".join(celdas) + " \\\\\n")
        f.write("\\bottomrule\n\\end{tabular}\n")

# ---------------------------------------------------------------- ANOVA de dos factores (tipo I: mapa, sistema, interacción) con eta parcial
def anova2(k):
    y = np.array([r[k] for r in FILAS], float); mapa = np.array([int(r["mapa"]) for r in FILAS]); sis = np.array([int(r["sistema"]) for r in FILAS])
    def dummies(fac, niveles): return np.column_stack([(fac == v).astype(float) for v in niveles[1:]])
    X0 = np.ones((len(y), 1)); Xm = np.hstack([X0, dummies(mapa, MAPAS)]); Xs = np.hstack([Xm, dummies(sis, SIS)])
    inter = np.column_stack([(mapa == a).astype(float) * (sis == b).astype(float) for a in MAPAS[1:] for b in SIS[1:]]); Xi = np.hstack([Xs, inter])
    def rss(X): beta, *_ = np.linalg.lstsq(X, y, rcond=None); return float(((y - X @ beta) ** 2).sum())
    r0, rm, rs, ri = rss(X0), rss(Xm), rss(Xs), rss(Xi)
    dfm, dfs, dfi = len(MAPAS) - 1, len(SIS) - 1, (len(MAPAS) - 1) * (len(SIS) - 1); dfe = len(y) - Xi.shape[1]
    out = []
    for nombre, ss, df in [("Mapa", r0 - rm, dfm), ("Sistema", rm - rs, dfs), ("Mapa × sistema", rs - ri, dfi)]:
        F = (ss / df) / (ri / dfe); p = 1 - stats.f.cdf(F, df, dfe); eta = ss / (ss + ri)
        out.append((nombre, df, F, p, eta))
    return out, dfe
with open(os.path.join(AQUI, "tablas", "anova.tex"), "w", encoding="utf-8") as f:
    f.write("\\begin{tabular}{llrrrr}\n\\toprule\nVariable & Fuente & g.l. & $F$ & $p$ & $\\eta^2_p$ \\\\\n\\midrule\n")
    for k, nombre in [("pob", "Población"), ("prod", "Producción"), ("gini", "Gini"), ("ataq", "Ataques"), ("cultivos", "Cultivos")]:
        out, dfe = anova2(k); primera = True
        for fuente, df, F, p, eta in out:
            f.write(f"{nombre if primera else ''} & {fuente} & {df} & {fnum(F, 1)} & {fp(p)} & {fnum(eta, 2)} \\\\\n"); primera = False
            tag = "Inter" if "×" in fuente else fuente
            macro(f"eta{k.capitalize()}{tag}", fnum(eta, 2)); macro(f"p{k.capitalize()}{tag}", fp(p).replace("$", ""))
        f.write("\\addlinespace\n")
    f.write("\\bottomrule\n\\end{tabular}\n")
    macro("glError", str(dfe))

# ---------------------------------------------------------------- concordancia de rankings entre mapas (W de Kendall) y Spearman medio
def ranking(m, k, mayor_mejor=True):
    medias = [np.mean([r[k] for r in G[(m, s)]]) for s in SIS]
    return stats.rankdata([-x if mayor_mejor else x for x in medias])
with open(os.path.join(AQUI, "tablas", "concordancia.tex"), "w", encoding="utf-8") as f:
    ABREV = {3: "Anarq.", 1: "Ancap.", 4: "E. mín.", 5: "Socdem.", 6: "Social.", 2: "Comun."}
    f.write("\\begin{tabular}{lrrp{6.2cm}}\n\\toprule\nVariable & $W$ de Kendall & $\\rho$ media & Orden de sistemas (de mejor a peor) \\\\\n\\midrule\n")
    for k, nombre, mayor in [("pob", "Población", True), ("prod", "Producción", True), ("gini", "Gini (menor = mejor)", False), ("ataq", "Ataques (menor = mejor)", False), ("cultivos", "Cultivos", True)]:
        R = np.array([ranking(m, k, mayor) for m in MAPAS]); n, mm = len(SIS), len(MAPAS)
        Rsum = R.sum(axis=0); W = 12 * ((Rsum - Rsum.mean()) ** 2).sum() / (mm ** 2 * (n ** 3 - n))
        rhos = [stats.spearmanr(R[i], R[j])[0] for i, j in itertools.combinations(range(mm), 2)]
        orden = " $>$ ".join(ABREV[SIS[i]] for i in np.argsort(Rsum))
        f.write(f"{nombre} & {fnum(W, 2)} & {fnum(np.mean(rhos), 2)} & {orden} \\\\\n")
        macro(f"kendall{k.capitalize()}", fnum(W, 2)); macro(f"spearman{k.capitalize()}", fnum(np.mean(rhos), 2))
    f.write("\\bottomrule\n\\end{tabular}\n")

# ---------------------------------------------------------------- contrastes clave por mapa
with open(os.path.join(AQUI, "tablas", "contrastes_mapas.tex"), "w", encoding="utf-8") as f:
    f.write("\\begin{tabular}{lrrrrrr}\n\\toprule\n & \\multicolumn{2}{c}{Socdem. vs ancap.: producción} & \\multicolumn{2}{c}{Socdem. vs ancap.: Gini} & \\multicolumn{2}{c}{Comunismo vs ancap.: población} \\\\\n\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}\\cmidrule(lr){6-7}\nMapa & $d$ & $p$ & $d$ & $p$ & $d$ & $p$ \\\\\n\\midrule\n")
    socdem_prod_sig, socdem_gini_sig, comun_sig = 0, 0, 0
    for m in MAPAS:
        p1, d1 = welch([r["prod"] for r in G[(m, 5)]], [r["prod"] for r in G[(m, 1)]])
        p2, d2 = welch([r["gini"] for r in G[(m, 5)]], [r["gini"] for r in G[(m, 1)]])
        p3, d3 = welch([r["pob"] for r in G[(m, 2)]], [r["pob"] for r in G[(m, 1)]])
        socdem_prod_sig += int(not math.isnan(p1) and p1 < 0.05 and d1 < 0); socdem_gini_sig += int(not math.isnan(p2) and p2 < 0.05); comun_sig += int(not math.isnan(p3) and p3 < 0.05)
        f.write(f"{NOMBRE_MAPA[m]} & {fnum(d1, 2)} & {fp(p1)} & {fnum(d2, 2)} & {fp(p2)} & {fnum(d3, 2)} & {fp(p3)} \\\\\n")
    f.write("\\bottomrule\n\\end{tabular}\n")
    macro("mapasSocdemProdMenor", str(socdem_prod_sig)); macro("mapasSocdemGiniSig", str(socdem_gini_sig)); macro("mapasComunSig", str(comun_sig)); macro("nMapas", str(len(MAPAS)))

# ---------------------------------------------------------------- efectos principales del mapa (promedio entre sistemas) y correlaciones geográficas
geo = {}
for m in MAPAS:
    reps = [r for (mm, s), rs in G.items() if mm == m for r in rs]
    geo[m] = {k: np.mean([r[k] for r in reps]) for k in ("pob", "prod", "gini", "ataq", "intercambios", "ciudades", "mayorCiudad", "migraciones", "celdasFertiles", "distMediaAgua", "celdasAgua", "riegos")}
with open(os.path.join(AQUI, "tablas", "mapas_efectos.tex"), "w", encoding="utf-8") as f:
    f.write("\\begin{tabular}{lrrrrrrr}\n\\toprule\nMapa & Población & Producción & Gini & Ataques & Intercambios/mes & Ciudades & Migraciones \\\\\n\\midrule\n")
    for m in sorted(MAPAS, key=lambda m: -geo[m]["pob"]):
        g = geo[m]; f.write(f"{NOMBRE_MAPA[m]} & {fnum(g['pob'], 0)} & {fnum(g['prod'], 0)} & {fnum(g['gini'], 2)} & {fnum(g['ataq'], 1)} & {fnum(g['intercambios'], 1)} & {fnum(g['ciudades'], 1)} & {fnum(g['migraciones'], 0)} \\\\\n")
    f.write("\\bottomrule\n\\end{tabular}\n")
orden_mapas = sorted(MAPAS, key=lambda m: -geo[m]["pob"])
macro("mapaMejor", NOMBRE_MAPA[orden_mapas[0]]); macro("mapaPeor", NOMBRE_MAPA[orden_mapas[-1]])
macro("pobMapaMejor", fnum(geo[orden_mapas[0]]["pob"], 0)); macro("pobMapaPeor", fnum(geo[orden_mapas[-1]]["pob"], 0))
rho_f, p_f = stats.spearmanr([geo[m]["celdasFertiles"] for m in MAPAS], [geo[m]["pob"] for m in MAPAS])
rho_d, p_d = stats.spearmanr([geo[m]["distMediaAgua"] for m in MAPAS], [geo[m]["pob"] for m in MAPAS])
macro("rhoFertilPob", fnum(rho_f, 2)); macro("rhoDistPob", fnum(rho_d, 2))
mapa_comercio = max(MAPAS, key=lambda m: geo[m]["intercambios"]); macro("mapaMasComercio", NOMBRE_MAPA[mapa_comercio]); macro("intercambiosMapaMas", fnum(geo[mapa_comercio]["intercambios"], 1))
mapa_ciudades = max(MAPAS, key=lambda m: geo[m]["ciudades"]); macro("mapaMasCiudades", NOMBRE_MAPA[mapa_ciudades]); macro("ciudadesMapaMas", fnum(geo[mapa_ciudades]["ciudades"], 1))
extintos = {s: sum(int(r["extinto"]) for m in MAPAS for r in G[(m, s)]) for s in SIS}
macro("extComunMapas", str(extintos[2])); macro("extSocialMapas", str(extintos[6])); macro("corridasPorSistema", str(len(MAPAS) * NREP))
# en qué mapas la socialdemocracia supera o iguala en población al anarcocapitalismo
sup = [NOMBRE_MAPA[m] for m in MAPAS if np.mean([r["pob"] for r in G[(m, 5)]]) >= np.mean([r["pob"] for r in G[(m, 1)]])]
macro("mapasSocdemPobMayor", str(len(sup))); macro("listaMapasSocdemPobMayor", ", ".join(sup) if sup else "ninguno")

# ---------------------------------------------------------------- figuras
fig, axes = plt.subplots(1, 3, figsize=(12, 3.9))
for ax, (k, titulo, dec) in zip(axes, [("pob", "Población", 0), ("prod", "Producción por mes", 0), ("gini", "Gini de reservas", 2)]):
    M = np.array([[np.mean([r[k] for r in G[(m, s)]]) for s in SIS] for m in MAPAS])
    im = ax.imshow(M, cmap="Blues", aspect="auto")
    ax.set_xticks(range(len(SIS))); ax.set_xticklabels([NOMBRE_SIS[s] for s in SIS], rotation=35, ha="right", fontsize=7.5)
    ax.set_yticks(range(len(MAPAS))); ax.set_yticklabels([NOMBRE_MAPA[m] for m in MAPAS], fontsize=8); ax.set_title(titulo, fontsize=10, loc="left")
    for i in range(len(MAPAS)):
        for j in range(len(SIS)):
            ax.text(j, i, f"{M[i, j]:.{dec}f}".replace(".", ","), ha="center", va="center", fontsize=7, color="white" if M[i, j] > M.max() * 0.6 else "#14181f")
fig.tight_layout(); guardar(fig, "mapas_heatmap", bbox_inches="tight"); plt.close(fig)

fig, axes = plt.subplots(1, 2, figsize=(11, 3.8))
for ax, (k, titulo) in zip(axes, [("pob", "Población"), ("gini", "Gini de reservas")]):
    for i, s in enumerate(SIS):
        ys = [np.mean([r[k] for r in G[(m, s)]]) for m in MAPAS]; es = [resumen([r[k] for r in G[(m, s)]])[2] for m in MAPAS]
        ax.errorbar(range(len(MAPAS)), ys, yerr=es, color=COLORES[i], marker="o", capsize=3, linewidth=1.6, label=NOMBRE_SIS[s])
    ax.set_xticks(range(len(MAPAS))); ax.set_xticklabels([NOMBRE_MAPA[m] for m in MAPAS], rotation=25, ha="right", fontsize=8)
    ax.set_title(titulo, fontsize=10, loc="left"); ax.spines[["top", "right"]].set_visible(False); ax.grid(color="#e6e3da", linewidth=0.8); ax.set_axisbelow(True)
h, l = axes[0].get_legend_handles_labels(); fig.legend(h, l, loc="lower center", ncol=3, fontsize=8, frameon=False, bbox_to_anchor=(0.5, -0.04))
fig.tight_layout(rect=(0, 0.1, 1, 1)); guardar(fig, "mapas_lineas", bbox_inches="tight"); plt.close(fig)

# Figura: series de población por mapa (seis paneles, una línea por sistema)
import json
with open(os.path.join(AQUI, "datos", "mapas_series.json"), encoding="utf-8") as f: SER = json.load(f)
fig, axes = plt.subplots(2, 3, figsize=(11, 6), sharey=True); axes = axes.ravel()
for ax, m in zip(axes, MAPAS):
    for i, s in enumerate(SIS):
        ss = [x["pob"] for x in SER if x["mapa"] == m and x["sistema"] == s]; L = min(len(x) for x in ss)
        t = [j * 5 for j in range(L)]; y = [np.mean([x[j] for x in ss]) for j in range(L)]
        ax.plot(t, y, color=COLORES[i], linewidth=1.5, label=NOMBRE_SIS[s])
    ax.set_title(NOMBRE_MAPA[m], fontsize=10, loc="left"); ax.set_xlabel("años"); ax.spines[["top", "right"]].set_visible(False); ax.grid(color="#e6e3da", linewidth=0.8); ax.set_axisbelow(True)
h, l = axes[0].get_legend_handles_labels(); fig.legend(h, l, loc="lower center", ncol=6, fontsize=8, frameon=False, bbox_to_anchor=(0.5, -0.02))
fig.tight_layout(rect=(0, 0.05, 1, 1)); guardar(fig, "mapas_series", bbox_inches="tight"); plt.close(fig)

# Figura: geografía frente a población (un punto por mapa) y mapas de calor de ataques y cultivos
fig, axes = plt.subplots(1, 3, figsize=(12, 3.8))
ax = axes[0]
for i, m in enumerate(MAPAS):
    ax.scatter(geo[m]["distMediaAgua"], geo[m]["pob"], s=60, color=COLORES[i], zorder=3); ax.annotate(NOMBRE_MAPA[m], (geo[m]["distMediaAgua"], geo[m]["pob"]), xytext=(5, 4), textcoords="offset points", fontsize=8)
ax.set_xlabel("distancia media de la tierra al agua (casillas)"); ax.set_ylabel("población (promedio de sistemas)"); ax.set_title("Geografía y población", fontsize=10, loc="left")
ax.spines[["top", "right"]].set_visible(False); ax.grid(color="#e6e3da", linewidth=0.8); ax.set_axisbelow(True)
for ax, (k, titulo, dec) in zip(axes[1:], [("ataq", "Ataques por mes", 1), ("cultivos", "Parcelas cultivadas", 0)]):
    M = np.array([[np.mean([r[k] for r in G[(m, s)]]) for s in SIS] for m in MAPAS]); ax.imshow(M, cmap="Blues", aspect="auto")
    ax.set_xticks(range(len(SIS))); ax.set_xticklabels([NOMBRE_SIS[s] for s in SIS], rotation=35, ha="right", fontsize=7.5); ax.set_yticks(range(len(MAPAS))); ax.set_yticklabels([NOMBRE_MAPA[m] for m in MAPAS], fontsize=8); ax.set_title(titulo, fontsize=10, loc="left")
    for i in range(len(MAPAS)):
        for j in range(len(SIS)): ax.text(j, i, f"{M[i, j]:.{dec}f}".replace(".", ","), ha="center", va="center", fontsize=7, color="white" if M[i, j] > M.max() * 0.6 else "#14181f")
fig.tight_layout(); guardar(fig, "mapas_geo", bbox_inches="tight"); plt.close(fig)

with open(os.path.join(AQUI, "macros_mapas.tex"), "w", encoding="utf-8") as f:
    for k, v in macros.items(): f.write(f"\\newcommand{{\\{k}}}{{{v}}}\n")
print("análisis de mapas:", len(FILAS), "corridas,", len(macros), "macros")
