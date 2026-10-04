# Sociedad artificial que aprende

Simulador basado en agentes en el que la biología y los instintos son fijos y la conducta económica evoluciona por selección natural. Sirve para comparar sistemas económicos (anarquía primitiva, anarcocapitalismo, capitalismo con Estado mínimo, socialdemocracia, socialismo con planificación parcial, comunismo) en distintas geografías, con experimentos con réplicas, estadística e informe automático.

**Paper interactivo y simulador en línea:** https://jesusguzman28.github.io/sociedad-artificial/

Autor: Pedro Jesús Guzmán Ramos · IESTP "Sara Sara", Ayacucho, Perú · ORCID 0009-0005-5673-7452

## Contenido

- `mundos.html`: el simulador completo en un solo archivo (sin dependencias; funciona sin conexión).
- `docs/`: sitio web publicado en GitHub Pages: paper interactivo (`index.html`), simulador, manuscrito en PDF y datos.
- `paper/`: manuscrito en LaTeX, bibliografía, scripts de análisis (`analisis.py`, `analisis_mapas.py`, `construir_web.py`) y datos de los tres experimentos (`datos/`).
- `economia.html`, `laberinto.html`, `laberinto.py`: versiones anteriores del proyecto.
- `sprites/`: gráficos CC0 de Kenney.nl usados por el simulador.

## Reproducir

1. Abrir `mundos.html` en un navegador. Pestaña **Experimentos** para réplicas con estadística; pestaña **Validación** para los hechos estilizados.
2. Los experimentos del paper usan las semillas `2024 + 7919·r` (réplica r). Con la misma semilla y configuración el simulador reproduce exactamente la misma historia.
3. Análisis y manuscrito: `cd paper && python analisis.py && python analisis_mapas.py && latexmk -pdf manuscrito.tex` (numpy, scipy, matplotlib y una distribución LaTeX).
4. Sitio web: `python paper/construir_web.py` regenera `docs/`.

## Licencia

Código y texto: © Pedro Jesús Guzmán Ramos. Gráficos: Kenney.nl, CC0.
