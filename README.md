# Photosyntech

Sistema de monitoreo y generación de música a través de señales bioeléctricas de plantas.

## Descripción del Proyecto

Este sistema captura y procesa señales bioeléctricas generadas por plantas, junto con datos ambientales de sensores (temperatura, humedad, iluminación), para generar una interpretación sonora en tiempo real.

### Clarificación Científica Importante

Las plantas generan señales bioeléctricas medibles como resultado de sus procesos fisiológicos. Este proyecto NO convierte directamente estas señales en sonido, sino que realiza un proceso de mapeo e interpretación:

1. **Captura señales bioeléctricas**: Lee voltajes generados por la planta (rango típico: -0.250V a 0V)
2. **Procesa y analiza**: Aplica filtros digitales y calcula características de la señal (variación, tendencia)
3. **Integra datos ambientales**: Combina lecturas de sensores (temperatura, humedad relativa, humedad del suelo, iluminación)
4. **Calcula bienestar**: Aplica fórmula ponderada para determinar el estado de la planta
5. **Mapea a parámetros musicales**: Interpreta estos datos como elementos musicales

### Fórmula de Bienestar

El sistema calcula un índice de bienestar (0-100%) basado en qué tan cerca están las lecturas de los rangos ideales definidos en el perfil:

```
Bienestar = Σ(contribución_sensor × ponderación_sensor)
```

Donde cada contribución se calcula como:
- Si el valor está en rango ideal: `contribución = ponderación_completa`
- Si está fuera de rango: `contribución = ponderación × (1 - desviación_normalizada)`

Ejemplo de ponderaciones por defecto:
- Humedad del suelo: 40%
- Temperatura: 25%
- Iluminación: 20%
- Humedad relativa: 15%

### Mapeo a Elementos Musicales

**Tonalidad y Escala:**
- Bienestar ≥ 80%: Escala mayor (sonido "alegre")
- Bienestar < 80%: Escala menor (sonido "melancólico")
- Tonalidad: Configurable por usuario (C, D, E, F, G, A, B con sostenidos)

**Duración de Acordes:**
Basada en la variación de la señal bioeléctrica (desviación estándar):
- Variación < 1 mV: 10-12 segundos (planta en reposo)
- Variación 1-3 mV: 8-10 segundos
- Variación 3-6 mV: 6-8 segundos
- Variación 6-10 mV: 4-6 segundos
- Variación 10-15 mV: 2.5-4 segundos
- Variación > 15 mV: 1.5-2.5 segundos (planta muy activa)

**Progresiones de Acordes:**
El sistema selecciona progresiones armónicas según el modo (mayor/menor) y genera acordes usando intervalos estándar:
- Acorde mayor: [0, 4, 7] semitonos
- Acorde menor: [0, 3, 7] semitonos
- Acorde disminuido: [0, 3, 6] semitonos

## Características

- Captura en tiempo real de señales bioeléctricas vía puerto serial
- Monitoreo de 4 sensores ambientales
- Síntesis musical MIDI adaptativa basada en estado de la planta
- Interfaz gráfica con visualización de datos históricos
- Generación de reportes en PDF
- Grabación de audio de la señal bioeléctrica
- Integración con API del clima (OpenWeatherMap)

## Requisitos

- Python 3.8+
- Arduino o microcontrolador compatible con lectura de sensores
- Puerto serial disponible (por defecto COM7)

## Instalación

1. Clonar el repositorio:
```bash
git clone <url-del-repositorio>
cd photosyntech
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Configurar variables de entorno:
```bash
cp .env.example .env
```

Editar `.env` con tus valores:
```env
OPENWEATHERMAP_API_KEY=tu_api_key_aqui
CITY=Ciudad,codigo_pais
RAIN_AUDIO_FILE=audio/rain.mp3
```

4. Configurar audio de lluvia (opcional):
El sistema puede reproducir un audio de fondo de lluvia junto con la música generada. Por motivos de derechos de autor, no se incluye el archivo `rain.mp3` en el repositorio.

Para agregar tu propio audio:
- Descarga o graba un audio de lluvia en formato MP3
- Colócalo en la carpeta `audio/` con el nombre `rain.mp3`
- O especifica otro nombre en la variable `RAIN_AUDIO_FILE` del archivo `.env`

Si no agregas un audio de lluvia, la aplicación funcionará normalmente y reproducirá la melodía generada sin el sonido ambiental de fondo.

5. Configurar perfil de planta:
Editar `Perfil.txt` con los parámetros de tu planta (rangos ideales, ponderaciones).

6. Configurar tonalidad:
Editar `configuracion.txt` para establecer la tonalidad musical deseada.

## Uso

Ejecutar la aplicación:
```bash
python main.py
```

La interfaz incluye:
- Vista principal con lecturas en tiempo real
- Gráficas de evolución de sensores
- Módulo de configuración
- Generación de reportes históricos
- Grabador de señal bioeléctrica

## Estructura del Proyecto

```
photosyntech/
├── config/           # Configuración centralizada
├── controller/       # Controladores (clima, workers)
├── core/             # Lógica central (procesamiento, storage)
├── hardware/         # Interfaz con hardware (serial)
├── model/            # Modelos de datos
├── services/         # Servicios (audio, música, perfil)
├── ui/               # Interfaz gráfica PyQt6
├── utils/            # Utilidades
├── historialLecturas/ # Datos históricos de sensores
├── audio/            # Archivos de audio (no incluidos en repo)
├── main.py           # Punto de entrada
├── Perfil.txt        # Configuración de perfil de planta
└── configuracion.txt # Configuración musical
```

## Archivos de Configuración

**Perfil.txt**: Define el perfil de la planta monitoreada
```
nombre=NombrePlanta
temperatura_min=20
temperatura_max=30
ponderacion_temperatura=25
...
```

**configuracion.txt**: Parámetros del sistema
```
tonalidad=C
dispositivo=0
...
```

**.env**: Variables de entorno
```
OPENWEATHERMAP_API_KEY=tu_api_key_aqui
CITY=Gustavo A. Madero,mx
RAIN_AUDIO_FILE=audio/rain.mp3
```

## Notas Técnicas

- La señal bioeléctrica se filtra con pasa-banda (0.1-10 Hz) y notch (60 Hz)
- El sistema opera en modo simulación si no detecta puerto serial
- Los datos históricos se guardan en formato TXT con timestamp
- La síntesis MIDI usa el instrumento 92 (Pad 4 - choir)
- El audio de lluvia se reproduce en loop a 20% de volumen (si está configurado)

## Licencia

Este proyecto es de uso académico y de investigación.
