import pygame.midi
import pygame.mixer
import random
import time
import os

player = None


pygame.midi.init()

player = pygame.midi.Output(0)
player.set_instrument(92, channel=0)

escalas = {
    "C":  ([60, 62, 64, 65, 67, 69, 71, 72], [60, 62, 63, 65, 67, 68, 70, 72]),
    "C#": ([61, 63, 65, 66, 68, 70, 72, 73], [61, 63, 64, 66, 68, 69, 71, 73]),
    "D":  ([62, 64, 66, 67, 69, 71, 73, 74], [62, 64, 65, 67, 69, 70, 72, 74]),
    "D#": ([63, 65, 67, 68, 70, 72, 74, 75], [63, 65, 66, 68, 70, 71, 73, 75]),
    "E":  ([64, 66, 68, 69, 71, 73, 75, 76], [64, 66, 67, 69, 71, 72, 74, 76]),
    "F":  ([65, 67, 69, 70, 72, 74, 76, 77], [65, 67, 68, 70, 72, 73, 75, 77]),
    "F#": ([66, 68, 70, 71, 73, 75, 77, 78], [66, 68, 69, 71, 73, 74, 76, 78]),
    "G":  ([67, 69, 71, 72, 74, 76, 78, 79], [67, 69, 70, 72, 74, 75, 77, 79]),
    "G#": ([68, 70, 72, 73, 75, 77, 79, 80], [68, 70, 71, 73, 75, 76, 78, 80]),
    "A":  ([69, 71, 73, 74, 76, 78, 80, 81], [69, 71, 72, 74, 76, 77, 79, 81]),
    "A#": ([70, 72, 74, 75, 77, 79, 81, 82], [70, 72, 73, 75, 77, 78, 80, 82]),
    "B":  ([71, 73, 75, 76, 78, 80, 82, 83], [71, 73, 74, 76, 78, 79, 81, 83]),
}

calidades_acorde = {
    "mayor": ["mayor", "menor", "menor", "mayor", "mayor", "menor", "disminuido"],
    "menor": ["menor", "disminuido", "mayor", "menor", "menor", "mayor", "mayor"]
}

intervalos_acorde = {
    "mayor": [0, 4, 7],
    "menor": [0, 3, 7],
    "disminuido": [0, 3, 6]
}

progressions = {
    "mayor": [
        [0, 4, 5, 1], [0, 2, 5, 1], [0, 5, 6, 4],
        [0, 3, 4, 1], [0, 5, 2, 4], [0, 1, 4, 5]
    ],
    "menor": [
        [3, 6, 2, 0], [5, 6, 4, 0], [6, 5, 1, 4],
        [4, 3, 0, 5], [6, 1, 4, 2], [5, 4, 3, 0]
    ],
}

musica_activa = False

RANGO_MIN = 48
RANGO_MAX = 60

def iniciar_lluvia():
    print("Iniciando lluvia...")
    pygame.mixer.music.load("audio/rain.mp3")
    pygame.mixer.music.set_volume(0.2)
    pygame.mixer.music.play(-1)


def generar_acorde(base, calidad):
    if calidad not in intervalos_acorde:
        calidad = "mayor"
    acorde = [base + i for i in intervalos_acorde[calidad]]
    return ajustar_rango(acorde)

def ajustar_rango(acorde):
    while max(acorde) > RANGO_MAX:
        acorde = [n - 12 for n in acorde]
    while min(acorde) < RANGO_MIN:
        acorde = [n + 12 for n in acorde]
    return acorde

def tocar_acorde(acorde, velocity=80):
    for nota in acorde:
        player.note_on(nota, velocity, 0)

def apagar_acorde(acorde):
    for nota in acorde:
        player.note_off(nota, 0, 0)

def tocar_progresion(tonalidad=None, tipo_escala="mayor", velocidad="medio", evento_stop=None):
    global musica_activa
    musica_activa = True

    if tonalidad is None:
        tonalidad = leer_tonalidad_config()

    print(f"Iniciando progresión en {tonalidad} {tipo_escala}")

    # Persistencia de progresiones no repetidas
    if not hasattr(tocar_progresion, "progresiones_restantes"):
        tocar_progresion.progresiones_restantes = {}

    clave = (tonalidad, tipo_escala)
    if clave not in tocar_progresion.progresiones_restantes or not tocar_progresion.progresiones_restantes[clave]:
        todas = progressions.get(tipo_escala, progressions["mayor"])[:]
        random.shuffle(todas)
        tocar_progresion.progresiones_restantes[clave] = todas

    progresion = tocar_progresion.progresiones_restantes[clave].pop()
    calidades = calidades_acorde[tipo_escala]
    tonos = escalas.get(tonalidad, escalas["C"])
    escala = tonos[0] if tipo_escala == "mayor" else tonos[1]

    print(f"🎹 Progresión seleccionada: {[grado + 1 for grado in progresion]}")

    while musica_activa:
        for grado in progresion:
            if not musica_activa:
                apagar_notas()
                print("Música interrumpida")
                return

            if evento_stop and evento_stop.is_set():
                evento_stop.clear()
                apagar_notas()
                print("Cambio de tonalidad detectado, reiniciando progresión")
                return

            base_nota = escala[grado]
            calidad = calidades[grado % 7]
            acorde = generar_acorde(base_nota, calidad)

            duracion = {
                "rápido": random.uniform(2.0, 4.0),
                "medio":  random.uniform(5.0, 7.0),
                "lento":  random.uniform(8.0, 12.0)
            }.get(velocidad, 6.0)

            print(f"\n🎵 Grado {grado + 1} ({calidad}) - Acorde: {acorde} - Dur: {duracion:.1f}s")
            print(f"   Tonalidad: {tonalidad} - Modo: {tipo_escala}")

            tocar_acorde(acorde)

            tiempo = 0
            while tiempo < duracion:
                if evento_stop and evento_stop.is_set():
                    evento_stop.clear()
                    apagar_acorde(acorde)
                    print("Cambio de tonalidad detectado durante acorde")
                    return
                time.sleep(0.1)
                tiempo += 0.1

            apagar_acorde(acorde)

            pausa = random.uniform(1.0, 3.0)
            pausa_tiempo = 0
            while pausa_tiempo < pausa:
                if evento_stop and evento_stop.is_set():
                    evento_stop.clear()
                    print("Cambio de tonalidad detectado durante pausa")
                    return
                time.sleep(0.1)
                pausa_tiempo += 0.1

        # Al terminar la progresión, se escoge una nueva para seguir
        if not tocar_progresion.progresiones_restantes[clave]:
            todas = progressions.get(tipo_escala, progressions["mayor"])[:]
            random.shuffle(todas)
            tocar_progresion.progresiones_restantes[clave] = todas

        progresion = tocar_progresion.progresiones_restantes[clave].pop()


def detener_musica():
    global musica_activa
    if musica_activa:
        print("Deteniendo música.")
        musica_activa = False
        apagar_notas()

def apagar_notas():
    player.write_short(0xB0, 120, 0)
    player.write_short(0xB0, 123, 0)

def tocar_un_acorde(tonalidad=None, tipo_escala="mayor", variacion=0):
    global player
    if player is None:
        print("🎹 Inicializando MIDI player...")
        pygame.midi.init()
        player = pygame.midi.Output(0)
        player.set_instrument(92, channel=0)

    tonos = escalas.get(tonalidad, escalas["C"])
    escala = tonos[0] if tipo_escala == "mayor" else tonos[1]

    progresion = random.choice(progressions.get(tipo_escala, progressions["mayor"]))
    calidades = calidades_acorde[tipo_escala]

    grado = random.choice(progresion)
    base_nota = escala[grado]
    calidad = calidades[grado % 7]

    acorde = generar_acorde(base_nota, calidad)

    if variacion < 1:
        duracion = random.uniform(10.0, 12.0)
    elif variacion < 3:
        duracion = random.uniform(8.0, 10.0)
    elif variacion < 6:
        duracion = random.uniform(6.0, 8.0)
    elif variacion < 10:
        duracion = random.uniform(4.0, 6.0)
    elif variacion < 15:
        duracion = random.uniform(2.5, 4.0)
    else:
        duracion = random.uniform(1.5, 2.5)

    print(f"\n🎵 Grado {grado + 1} ({calidad}) - Acorde: {acorde} - Dur: {duracion:.1f}s - Variacion: {variacion:.1f} mV")
    print(f"   Tonalidad: {tonalidad} - Modo: {tipo_escala}")

    tocar_acorde(acorde)
    time.sleep(duracion)
    apagar_acorde(acorde)


def leer_tonalidad_config():
    try:
        if os.path.exists("configuracion.txt"):
            with open("configuracion.txt", "r", encoding="utf-8") as f:
                for linea in f:
                    linea = linea.strip()
                    if linea.lower().startswith("tonalidad="):
                        return linea.split("=", 1)[1].strip()
    except Exception as e:
        print("[ERROR] No se pudo leer configuracion.txt:", e)
    return "C"

def elegir_tipo_escala():
    return random.choice(["mayor", "menor"])

def main(tipo=None):
    tipo_escala = tipo if tipo in ["mayor", "menor"] else elegir_tipo_escala()
    print(f"Escala elegida: {tipo_escala}")

    try:
        tocar_progresion(tipo_escala)
    except KeyboardInterrupt:
        print("Ejecución detenida.")
        apagar_notas()
        pygame.midi.quit()
        pygame.mixer.music.stop()
