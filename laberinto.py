"""
Laberinto con un agente que aprende a encontrar la salida (Q-learning).

El agente (A) NO sabe donde esta la salida (S). Solo recibe una senal de
recompensa: positiva cuando se acerca a la salida, negativa cuando se aleja
o choca contra una pared, y una recompensa grande cuando la encuentra.
Con esa senal va construyendo una "tabla Q" que le dice, para cada casilla,
que tan buena es cada direccion. Esa tabla y el historial de episodios se
guardan en aprendizaje.txt, asi que si vuelves a ejecutar el programa el
agente continua aprendiendo desde donde quedo.

Uso basico:
    python laberinto.py                 # entrena 300 episodios y muestra el camino aprendido
    python laberinto.py --ver           # entrena mostrando al agente moverse
    python laberinto.py --episodios 1000
    python laberinto.py --nuevo --filas 15 --cols 31 --semilla 7
    python laberinto.py --solo-mostrar  # no entrena, solo muestra lo aprendido
"""

import argparse
import os
import random
import sys
import time

# Acciones posibles del agente: (desplazamiento fila, desplazamiento columna)
ACCIONES = [(-1, 0), (1, 0), (0, -1), (0, 1)]
NOMBRES_ACCION = ["ARRIBA", "ABAJO", "IZQUIERDA", "DERECHA"]

PARED, LIBRE, AGENTE, SALIDA, CAMINO, INICIO = "#", ".", "A", "S", "o", "I"


# --------------------------------------------------------------------------
# Laberinto
# --------------------------------------------------------------------------
def generar_laberinto(filas, cols, semilla):
    """Genera un laberinto perfecto (sin ciclos) con DFS iterativo."""
    if filas % 2 == 0:
        filas += 1
    if cols % 2 == 0:
        cols += 1
    rng = random.Random(semilla)
    grid = [[PARED] * cols for _ in range(filas)]
    pila = [(1, 1)]
    grid[1][1] = LIBRE
    while pila:
        r, c = pila[-1]
        vecinos = []
        for dr, dc in ((-2, 0), (2, 0), (0, -2), (0, 2)):
            nr, nc = r + dr, c + dc
            if 1 <= nr < filas - 1 and 1 <= nc < cols - 1 and grid[nr][nc] == PARED:
                vecinos.append((nr, nc, dr, dc))
        if vecinos:
            nr, nc, dr, dc = rng.choice(vecinos)
            grid[r + dr // 2][c + dc // 2] = LIBRE
            grid[nr][nc] = LIBRE
            pila.append((nr, nc))
        else:
            pila.pop()
    return grid


def distancia(a, b):
    """Distancia Manhattan. Es la unica 'pista' que el entorno usa para premiar."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def dibujar(grid, agente=None, camino=(), inicio=None, salida=None):
    filas = []
    camino = set(camino)
    for r, fila in enumerate(grid):
        linea = []
        for c, celda in enumerate(fila):
            pos = (r, c)
            if pos == agente:
                linea.append(AGENTE)
            elif pos == salida:
                linea.append(SALIDA)
            elif pos == inicio:
                linea.append(INICIO)
            elif pos in camino:
                linea.append(CAMINO)
            else:
                linea.append(celda)
        filas.append(" ".join(linea))
    return "\n".join(filas)


def limpiar_pantalla():
    os.system("cls" if os.name == "nt" else "clear")


# --------------------------------------------------------------------------
# Agente Q-learning
# --------------------------------------------------------------------------
class Agente:
    def __init__(self, alpha=0.1, gamma=0.99, epsilon=1.0, epsilon_min=0.05, decaimiento=0.995):
        self.alpha = alpha            # velocidad de aprendizaje
        self.gamma = gamma            # cuanto valora las recompensas futuras
        self.epsilon = epsilon        # probabilidad de explorar (moverse al azar)
        self.epsilon_min = epsilon_min
        self.decaimiento = decaimiento
        self.q = {}                   # (fila, col) -> [valor de cada accion]

    def valores(self, estado):
        if estado not in self.q:
            self.q[estado] = [0.0, 0.0, 0.0, 0.0]
        return self.q[estado]

    def elegir(self, estado, explorar=True):
        if explorar and random.random() < self.epsilon:
            return random.randrange(len(ACCIONES))
        v = self.valores(estado)
        mejor = max(v)
        candidatos = [i for i, x in enumerate(v) if x == mejor]
        return random.choice(candidatos)

    def aprender(self, estado, accion, recompensa, nuevo_estado, terminal):
        v = self.valores(estado)
        objetivo = recompensa if terminal else recompensa + self.gamma * max(self.valores(nuevo_estado))
        v[accion] += self.alpha * (objetivo - v[accion])

    def decaer(self):
        self.epsilon = max(self.epsilon_min, self.epsilon * self.decaimiento)


# --------------------------------------------------------------------------
# Entorno
# --------------------------------------------------------------------------
class Entorno:
    R_SALIDA = 100.0     # premio por encontrar la salida
    R_PARED = -5.0       # castigo por chocar
    R_PASO = -0.1        # pequeno costo por cada paso (incentiva caminos cortos)
    R_ACERCARSE = 1.0    # premio por cada unidad que se acerca a la salida

    def __init__(self, grid):
        self.grid = grid
        self.filas = len(grid)
        self.cols = len(grid[0])
        self.inicio = (1, 1)
        self.salida = (self.filas - 2, self.cols - 2)
        self.max_pasos = self.filas * self.cols * 10   # limite por episodio: suficiente para explorar al azar

    def paso(self, estado, accion):
        """Aplica la accion y devuelve (nuevo_estado, recompensa, terminal)."""
        dr, dc = ACCIONES[accion]
        nuevo = (estado[0] + dr, estado[1] + dc)
        if self.grid[nuevo[0]][nuevo[1]] == PARED:
            return estado, self.R_PARED, False
        if nuevo == self.salida:
            return nuevo, self.R_SALIDA, True
        delta = distancia(estado, self.salida) - distancia(nuevo, self.salida)
        return nuevo, self.R_PASO + self.R_ACERCARSE * delta, False


def correr_episodio(entorno, agente, ver=False, retardo=0.03, numero=0):
    estado = entorno.inicio
    total = 0.0
    camino = [estado]
    for paso in range(1, entorno.max_pasos + 1):
        accion = agente.elegir(estado)
        nuevo, recompensa, terminal = entorno.paso(estado, accion)
        agente.aprender(estado, accion, recompensa, nuevo, terminal)
        total += recompensa
        estado = nuevo
        camino.append(estado)
        if ver:
            limpiar_pantalla()
            print(dibujar(entorno.grid, agente=estado, inicio=entorno.inicio, salida=entorno.salida))
            print(f"Episodio {numero}  paso {paso}  recompensa acumulada {total:.1f}  epsilon {agente.epsilon:.3f}")
            time.sleep(retardo)
        if terminal:
            return paso, total, True, camino
    return entorno.max_pasos, total, False, camino


def camino_aprendido(entorno, agente):
    """Sigue la mejor accion de cada casilla sin explorar. Devuelve (camino, llego)."""
    estado = entorno.inicio
    camino = [estado]
    visitados = {estado}
    for _ in range(entorno.max_pasos):
        accion = agente.elegir(estado, explorar=False)
        nuevo, _, terminal = entorno.paso(estado, accion)
        camino.append(nuevo)
        if terminal:
            return camino, True
        if nuevo in visitados:
            return camino, False     # se quedo dando vueltas: aun no aprendio ese tramo
        visitados.add(nuevo)
        estado = nuevo
    return camino, False


# --------------------------------------------------------------------------
# Guardar / cargar aprendizaje en .txt
# --------------------------------------------------------------------------
def guardar(ruta, params, historial, agente, grid):
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("# APRENDIZAJE DEL AGENTE - generado por laberinto.py\n")
        f.write("# Este archivo se lee al iniciar para continuar aprendiendo.\n\n")
        f.write("[PARAMETROS]\n")
        for k, v in params.items():
            f.write(f"{k}={v}\n")
        f.write(f"epsilon={agente.epsilon:.6f}\n")
        f.write(f"episodios_totales={len(historial)}\n")
        llegadas = sum(1 for h in historial if h[2])
        f.write(f"veces_que_llego={llegadas}\n")
        if historial:
            ultimos = historial[-50:]
            f.write(f"pasos_promedio_ultimos_50={sum(h[0] for h in ultimos) / len(ultimos):.1f}\n")
            exitos = [h[0] for h in historial if h[2]]
            if exitos:
                f.write(f"mejor_episodio_pasos={min(exitos)}\n")

        f.write("\n[LABERINTO]\n")
        for fila in grid:
            f.write("".join(fila) + "\n")

        f.write("\n[HISTORIAL]\n")
        f.write("# episodio;pasos;recompensa_total;llego_a_la_salida;epsilon\n")
        for i, (pasos, total, llego, eps) in enumerate(historial, 1):
            f.write(f"{i};{pasos};{total:.2f};{'si' if llego else 'no'};{eps:.4f}\n")

        f.write("\n[TABLA_Q]\n")
        f.write("# fila,col: ARRIBA ABAJO IZQUIERDA DERECHA -> mejor accion\n")
        for estado in sorted(agente.q):
            v = agente.q[estado]
            mejor = NOMBRES_ACCION[v.index(max(v))]
            f.write(f"{estado[0]},{estado[1]}: " + " ".join(f"{x:.3f}" for x in v) + f" -> {mejor}\n")


def cargar(ruta):
    """Devuelve (params, historial, tabla_q, grid) o None si el archivo no existe."""
    if not os.path.exists(ruta):
        return None
    params, historial, q, grid = {}, [], {}, []
    seccion = None
    with open(ruta, encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if not linea or (linea.startswith("#") and seccion != "LABERINTO"):
                continue
            if linea.startswith("[") and linea.endswith("]"):
                seccion = linea[1:-1]
                continue
            if seccion == "PARAMETROS":
                k, v = linea.split("=", 1)
                params[k] = v
            elif seccion == "LABERINTO":
                grid.append([PARED if ch == "#" else LIBRE for ch in linea])
            elif seccion == "HISTORIAL":
                _, pasos, total, llego, eps = linea.split(";")
                historial.append((int(pasos), float(total), llego == "si", float(eps)))
            elif seccion == "TABLA_Q":
                pos, resto = linea.split(":", 1)
                r, c = pos.split(",")
                valores = resto.split("->")[0].split()
                q[(int(r), int(c))] = [float(x) for x in valores]
    return params, historial, q, grid


# --------------------------------------------------------------------------
# Programa principal
# --------------------------------------------------------------------------
def main():
    p = argparse.ArgumentParser(description="Laberinto con agente que aprende (Q-learning).")
    p.add_argument("--episodios", type=int, default=300, help="episodios a entrenar (default 300)")
    p.add_argument("--filas", type=int, default=15, help="filas del laberinto (se ajusta a impar)")
    p.add_argument("--cols", type=int, default=21, help="columnas del laberinto (se ajusta a impar)")
    p.add_argument("--semilla", type=int, default=42, help="semilla para generar el laberinto")
    p.add_argument("--archivo", default="aprendizaje.txt", help="archivo .txt donde se guarda el aprendizaje")
    p.add_argument("--nuevo", action="store_true", help="ignora lo aprendido y empieza de cero")
    p.add_argument("--ver", action="store_true", help="muestra al agente moviendose en cada episodio")
    p.add_argument("--cada", type=int, default=1, help="con --ver, anima 1 de cada N episodios")
    p.add_argument("--retardo", type=float, default=0.02, help="segundos entre cuadros de animacion")
    p.add_argument("--solo-mostrar", action="store_true", help="no entrena, solo muestra el camino aprendido")
    args = p.parse_args()

    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.archivo)

    agente = Agente()
    historial = []
    params = {"filas": args.filas, "cols": args.cols, "semilla": args.semilla}

    grid_guardado = None
    datos = None if args.nuevo else cargar(ruta)
    if datos:
        params_guardados, historial, agente.q, grid_guardado = datos
        params = {k: int(params_guardados[k]) for k in ("filas", "cols", "semilla")}
        agente.epsilon = float(params_guardados.get("epsilon", 1.0))
        print(f"Cargado {args.archivo}: {len(historial)} episodios previos, "
              f"{len(agente.q)} casillas conocidas, epsilon {agente.epsilon:.3f}")
        print("(el laberinto se toma del archivo; usa --nuevo para cambiarlo)\n")
    else:
        print("Empezando de cero: el agente no sabe nada del laberinto.\n")

    # Si el archivo trae el laberinto (tambien lo genera laberinto.html), se usa tal cual.
    grid = grid_guardado or generar_laberinto(params["filas"], params["cols"], params["semilla"])
    params["filas"], params["cols"] = len(grid), len(grid[0])
    entorno = Entorno(grid)

    if not args.solo_mostrar:
        inicio_num = len(historial)
        t0 = time.time()
        for n in range(inicio_num + 1, inicio_num + args.episodios + 1):
            animar = args.ver and (n - inicio_num) % args.cada == 0
            pasos, total, llego, _ = correr_episodio(entorno, agente, ver=animar, retardo=args.retardo, numero=n)
            historial.append((pasos, total, llego, agente.epsilon))
            agente.decaer()
            if not args.ver and (n % 25 == 0 or n == inicio_num + 1):
                print(f"Episodio {n:5d}  pasos {pasos:5d}  recompensa {total:8.1f}  "
                      f"{'LLEGO' if llego else 'no llego'}  epsilon {agente.epsilon:.3f}")
            if (n - inicio_num) % 25 == 0:
                guardar(ruta, params, historial, agente, grid)   # guardado periodico
        guardar(ruta, params, historial, agente, grid)
        print(f"\nEntrenamiento terminado en {time.time() - t0:.1f}s. Aprendizaje guardado en {args.archivo}")

    camino, llego = camino_aprendido(entorno, agente)
    if args.ver:
        limpiar_pantalla()
    print("\nCamino que el agente sigue ahora SIN explorar (I=inicio, S=salida, o=camino):\n")
    print(dibujar(grid, camino=camino[1:-1], inicio=entorno.inicio, salida=entorno.salida))
    if llego:
        print(f"\nEl agente llega a la salida en {len(camino) - 1} pasos.")
    else:
        print("\nEl agente todavia no encuentra la salida con lo aprendido. Entrena mas episodios.")
    llegadas = sum(1 for h in historial if h[2])
    print(f"Episodios totales: {len(historial)}   veces que llego: {llegadas}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrumpido.")
        sys.exit(0)
