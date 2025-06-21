import pygame.midi
import random
import time
import pygame.mixer
import os

pygame.mixer.init()
pygame.midi.init()

player = pygame.midi.Output(0)
player.set_instrument(92, channel=0)

pygame.mixer.music.load("audio/rain.mp3")
pygame.mixer.music.set_volume(0.2)
pygame.mixer.music.play(-1)

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

# Calidades de acorde por grado para cada modo
calidades_acorde = {
    "mayor": ["mayor", "menor", "menor", "mayor", "mayor", "menor", "disminuido"],
    "menor": ["menor", "disminuido", "mayor", "menor", "menor", "mayor", "mayor"]
}

# Intervalos para cada tipo de acorde
intervalos_acorde = {
    "mayor": [0, 4, 7],      # Tónica, tercera mayor, quinta justa
    "menor": [0, 3, 7],      # Tónica, tercera menor, quinta justa
    "disminuido": [0, 3, 6]  # Tónica, tercera menor, quinta disminuida
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

def generar_acorde(base, calidad):
    """Genera acorde según la calidad especificada"""
    if calidad not in intervalos_acorde:
        calidad = "mayor"  # Valor por defecto si la calidad no es reconocida
    
    acorde = [base + i for i in intervalos_acorde[calidad]]
    return ajustar_rango(acorde)

def ajustar_rango(acorde):
    """Ajusta el acorde al rango MIDI permitido"""
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

def tocar_progresion(tipo_escala="mayor", velocidad="medio"):
    global musica_activa
    musica_activa = True

    while musica_activa:
        tonalidad = leer_tonalidad_config()
        tonos = escalas.get(tonalidad, escalas["C"])
        escala = tonos[0] if tipo_escala == "mayor" else tonos[1]

        progresion = random.choice(progressions.get(tipo_escala, progressions["mayor"]))
        calidades = calidades_acorde[tipo_escala]

        for grado in progresion:
            if not musica_activa:
                apagar_notas()
                print("🛑 Música interrumpida")
                return

            base_nota = escala[grado]
            
            # Determinar la calidad del acorde basado en el grado
            calidad = calidades[grado % 7]  # Usamos módulo para seguridad
            
            # Generar el acorde con la calidad apropiada
            acorde = generar_acorde(base_nota, calidad)

            duracion = {
                "rápido": random.uniform(2.0, 4.0),
                "medio":  random.uniform(5.0, 7.0),
                "lento":  random.uniform(8.0, 12.0)
            }.get(velocidad, 6.0)

            print(f"\n🎵 Grado {grado + 1} ({calidad}) - Acorde: {acorde} - Dur: {duracion:.1f}s")
            print(f"   Tonalidad: {tonalidad} - Modo: {tipo_escala}")

            tocar_acorde(acorde)
            time.sleep(duracion)
            apagar_acorde(acorde)

            pausa = random.uniform(1.0, 3.0)
            time.sleep(pausa)

def detener_musica():
    global musica_activa
    if musica_activa:
        print("🛑 Deteniendo música.")
        musica_activa = False
        apagar_notas()

def apagar_notas():
    player.write_short(0xB0, 120, 0)
    player.write_short(0xB0, 123, 0)

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
    print(f"🎼 Escala elegida: {tipo_escala}")

    try:
        tocar_progresion(tipo_escala)
    except KeyboardInterrupt:
        print("🛑 Ejecución detenida.")
        apagar_notas()
        pygame.midi.quit()
        pygame.mixer.music.stop()

if __name__ == "__main__":
    main()