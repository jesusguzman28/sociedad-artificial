# Manuscrito: Instituciones, incentivos y colapso demográfico en una economía artificial

Carpeta del artículo generado a partir del simulador `../mundos.html`.

## Archivos

- `manuscrito.tex`: el artículo en LaTeX (español, estructura ODD, resultados enlazados a `macros.tex`).
- `referencias.bib`: bibliografía (estilo apalike).
- `analisis.py`: estadística (media, IC 95 %, t de Welch, d de Cohen) y generación de `tablas/*.tex`, `figuras/*.pdf` y `macros.tex` para los experimentos 1 (sistemas) y 2 (barrido del impuesto).
- `analisis_mapas.py`: experimento 3 (6 mapas × 6 sistemas): ANOVA de dos factores, W de Kendall, contrastes por mapa, mapas de calor; genera `macros_mapas.tex`.
- `datos/replicas.csv`, `datos/replicas.json`, `datos/series.json`: experimentos 1 y 2 (108 réplicas).
- `datos/mapas.csv`, `datos/mapas_series.json`: experimento 3 (216 corridas).
- `datos/log_experimento.txt`: registro de la corrida.
- `manuscrito_v2.pdf`: PDF compilado.

## Cómo reproducir

1. Experimento (desde la carpeta `simulador`, con Node.js): el script usado está documentado en el manuscrito; recrea las réplicas con las semillas 2024 + 7919·r.
2. Análisis: `python analisis.py` (requiere numpy, scipy y matplotlib).
3. Compilación: `latexmk -pdf manuscrito.tex` (MiKTeX o TeX Live). También compila en Overleaf subiendo toda la carpeta.

## Antes de enviar

- Autor ya consignado: Pedro Jesús Guzmán Ramos, IESTP "Sara Sara", Ayacucho, Perú, ORCID 0009-0005-5673-7452.
- Añadir el DOI de Zenodo o CoMSES en "Disponibilidad de código y datos".
- Para JASSS o Computational Economics hace falta la versión en inglés; el resumen ya está en los dos idiomas.
- Revisar y firmar la "Declaración sobre el uso de inteligencia artificial".
