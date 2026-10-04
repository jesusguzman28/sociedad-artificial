# -*- coding: utf-8 -*-
"""Dibuja capturas de los mundos simulados con el atlas de sprites del simulador (capturas/estados.json → capturas/*.png y figuras/*.pdf)."""
import json, os
from PIL import Image, ImageDraw, ImageFont

AQUI = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.dirname(AQUI)
ATLAS = Image.open(os.path.join(RAIZ, "sprites", "atlas.png")).convert("RGBA")
T = 16; ESCALA = 2
def tile(i): return ATLAS.crop((i * T, 0, i * T + T, T))
TILES = {i: tile(i) for i in range(ATLAS.width // T)}
TILES_FLIP = {i: TILES[i].transpose(Image.FLIP_LEFT_RIGHT) for i in TILES}
def hash_(x, y): return (((x + 1) * 73856093) ^ ((y + 1) * 19349663)) & 0xFFFFFFFF
try: FUENTE = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 22); FUENTE_P = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 16)
except Exception: FUENTE = FUENTE_P = ImageFont.load_default()

def dibujar(e):
    W, H = e["W"], e["H"]; img = Image.new("RGBA", (W * T, H * T), (252, 252, 251, 255))
    casas = e["casa"]
    for y in range(H):
        for x in range(W):
            i = y * W + x; X, Y = x * T, y * T; h = hash_(x, y); tipo = e["tipo"][i]; com = e["comida"][i]
            if tipo == 1: img.alpha_composite(TILES[7], (X, Y)); continue
            if tipo == 2: img.alpha_composite(TILES[8 + (h % 4)], (X, Y)); continue
            img.alpha_composite(TILES[3 if com < 1.5 else (1 if h % 7 == 0 else (2 if h % 11 == 0 else 0))], (X, Y))
            if casas[i]:
                vec = 0
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        nx, ny = x + dx, y + dy
                        if (dx or dy) and 0 <= nx < W and 0 <= ny < H and casas[ny * W + nx]: vec += 1
                vacia = e["vacia"][i]; s = 37 if vec >= 4 else (36 if vec >= 2 else (35 if vacia else 34))
                t = TILES[s]
                if vacia: t = t.copy(); t.putalpha(t.getchannel("A").point(lambda a: int(a * 0.55)))
                img.alpha_composite(t, (X, Y))
            else:
                cu = e["cultivo"][i]
                if cu > 0: img.alpha_composite(TILES[28 if cu >= 1 else (26 if (cu < 0.35 or e["riego"][i] <= 0) else 27)], (X, Y))
                elif com > 6 and e["cap"][i] > 7: img.alpha_composite(TILES[(5 if h % 3 else 6) if com > 8.5 else 4], (X, Y))
                elif com > 4 and h % 13 == 0: img.alpha_composite(TILES[24], (X, Y))
    for a in e["agentes"]:
        img.alpha_composite((TILES_FLIP if a["f"] else TILES)[a["s"]], (a["x"] * T, a["y"] * T))
    return img.resize((W * T * ESCALA, H * T * ESCALA), Image.NEAREST)

def rejilla(paneles, columnas, nombre, titulo_panel):
    """paneles: lista de (imagen, etiqueta). Compone una rejilla con etiquetas y guarda PNG (capturas/) y PDF (figuras/)."""
    w, h = paneles[0][0].size; m = 8; alto_et = 34
    filas = (len(paneles) + columnas - 1) // columnas
    out = Image.new("RGB", (columnas * (w + m) + m, filas * (h + alto_et + m) + m), (255, 255, 255)); d = ImageDraw.Draw(out)
    for k, (im, et) in enumerate(paneles):
        c, r = k % columnas, k // columnas; X, Y = m + c * (w + m), m + r * (h + alto_et + m)
        d.text((X + 2, Y + 4), et, fill=(20, 24, 31), font=FUENTE); out.paste(im.convert("RGB"), (X, Y + alto_et))
    out.save(os.path.join(AQUI, "capturas", nombre + ".png")); out.convert("RGB").save(os.path.join(AQUI, "figuras", nombre + ".pdf"), resolution=150)
    return out

with open(os.path.join(AQUI, "capturas", "estados.json"), encoding="utf-8") as f: E = json.load(f)
NOMBRE_SIS = {3: "Anarquía primitiva", 1: "Anarcocapitalismo", 4: "Capitalismo con Estado mínimo", 5: "Socialdemocracia", 6: "Socialismo (planif. parcial)", 2: "Comunismo"}
NOMBRE_MAPA = {0: "4 oasis", 1: "Río", 2: "Lago central", 3: "Dos oasis lejanos", 4: "Costa", 5: "Muchos charcos"}
def etiqueta(e, extra): return f"{extra} · año {e['anio']} · {e['pob']} personas, {e['casas']} casas, {e['cultivos']} cultivos"
# capturas individuales
for clave, fotos in E.items():
    for anio, e in fotos.items(): dibujar(e).convert("RGB").save(os.path.join(AQUI, "capturas", f"{clave}_anio{anio}.png"))
rejilla([(dibujar(E[f"sistema_{s}"]["150"]), etiqueta(E[f"sistema_{s}"]["150"], NOMBRE_SIS[s])) for s in [3, 1, 4, 5, 6, 2]], 2, "mundos_sistemas", "")
rejilla([(dibujar(E[f"mapa_{m}"]["100"]), etiqueta(E[f"mapa_{m}"]["100"], NOMBRE_MAPA[m])) for m in [0, 1, 2, 3, 4, 5]], 2, "mundos_mapas", "")
rejilla([(dibujar(E["secuencia"][str(a)]), etiqueta(E["secuencia"][str(a)], "Socialdemocracia, río")) for a in [0, 10, 30, 60, 100, 150]], 2, "mundos_secuencia", "")
print("capturas y rejillas generadas")
