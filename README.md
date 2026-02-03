# PhotoSyntech v1.0

Sistema de monitoreo bioeléctrico y ambiental para plantas con síntesis musical adaptativa.

## 🏗️ Arquitectura Refactorizada

Este proyecto ha sido completamente refactorizado siguiendo principios SOLID y separación de responsabilidades.

### 📁 Estructura del Proyecto

```
photosyntech/
├── config/                 # Configuración centralizada
│   ├── settings.py        # Constantes y valores por defecto
│   └── config_manager.py  # Gestor singleton de configuración
│
├── core/                   # Lógica de negocio principal
│   ├── signal_processor.py    # Procesamiento de señales
│   ├── sensor_manager.py      # Gestión de sensores
│   └── data_storage.py        # Persistencia de datos
│
├── services/               # Servicios de aplicación
│   ├── audio_service.py   # Grabación de audio
│   ├── music_service.py   # Síntesis musical
│   └── profile_service.py # Gestión de perfiles de plantas
│
├── hardware/               # Comunicación con hardware
│   └── serial_reader.py   # Lectura del ESP32
│
├── controller/             # Controladores y APIs
│   ├── weather_controller.py  # Interfaz abstracta
│   ├── weather_api.py         # Implementación API
│   └── weather_worker.py      # Worker thread
│
├── model/                  # Modelos de datos
│   ├── weather_info.py
│   └── sensor_data.py
│
├── ui/                     # Interfaz de usuario
│   ├── main_window.py
│   ├── components/        # Componentes reutilizables
│   │   └── icon_button.py
│   ├── views/             # Vistas principales
│   │   ├── base_view.py       # Vista base abstracta
│   │   ├── main_view.py       # Vista principal (refactorizar)
│   │   ├── graphs_view.py     # Vista de gráficas (refactorizar)
│   │   ├── config_view.py     # Vista de configuración (refactorizar)
│   │   └── report_view.py     # Vista de reportes (refactorizar)
│   └── styles/            # Estilos centralizados
│       ├── fonts.py
│       └── theme.py
│
└── main.py                # Punto de entrada

```

## 🎯 Mejoras Implementadas

### 1. **Separación de Responsabilidades**
- ✅ Lógica de negocio separada de UI
- ✅ Servicios independientes y testeables
- ✅ Gestión centralizada de configuración
- ✅ Capa de persistencia abstraída

### 2. **Gestión de Configuración**
- ✅ ConfigManager singleton con cache inteligente
- ✅ Lectura/escritura centralizada
- ✅ TTL configurable para cache

### 3. **Procesamiento de Señales**
- ✅ SignalProcessor encapsula filtros
- ✅ Conversión y cálculo de features separados
- ✅ Reutilizable y testeable

### 4. **Gestión de Sensores**
- ✅ SensorManager centralizado
- ✅ Estado unificado de todos los sensores
- ✅ Validación y parsing seguros

### 5. **Servicios Desacoplados**
- ✅ AudioService para grabación
- ✅ MusicService para síntesis musical
- ✅ ProfileService para perfiles de plantas

### 6. **Hardware Abstraído**
- ✅ SerialReader encapsula comunicación
- ✅ Thread management integrado
- ✅ Parsing automático de protocolos

## 📝 Siguiente Paso: Refactorizar Vistas UI

Los módulos UI antiguos necesitan ser migrados a la nueva estructura:

### Tareas Pendientes:

1. **MainModule.py → main_view.py**
   - Usar `MusicService` en lugar de llamadas directas
   - Usar `AudioService` para grabación
   - Usar `ProfileService` para bienestar
   - Separar lógica de UI

2. **GraphsModule.py → graphs_view.py**
   - Usar `SensorManager` para datos
   - Eliminar acceso directo a privados
   - Centralizar estilos en Theme

3. **ConfigModule.py → config_view.py**
   - Usar `ConfigManager` exclusivamente
   - Simplificar lectura/escritura
   - Usar `AudioService` para dispositivos

4. **ReportModules.py → report_view.py**
   - Usar `DataStorage` para historial
   - Usar `ProfileService` para nombre
   - Separar lógica de generación

5. **MainWindow.py**
   - Actualizar imports
   - Usar nueva estructura de views
   - Aplicar Theme

## 🚀 Uso

### Configuración Inicial

```python
from config import ConfigManager, Settings

# El ConfigManager es singleton
config = ConfigManager()
config.ensure_config_exists()

# Establecer valores
config.set_tonality("C#")
config.set_device_id(0)
```

### Procesamiento de Señales

```python
from core import SignalProcessor

processor = SignalProcessor()

# Convertir voltaje
voltage_mv = processor.convert_raw_to_mv(raw_value)

# Aplicar filtros
filtered = processor.apply_filters(signal_array)

# Calcular features
features = processor.calculate_features(signal_array)
```

### Gestión de Sensores

```python
from core import SensorManager

sensors = SensorManager()

# Actualizar valores
sensors.update_sensor("temperatura", "25.5")

# Obtener valores
temp = sensors.get_sensor_value("temperatura")
all_values = sensors.get_all_sensors()
```

### Servicios

```python
from services import AudioService, MusicService, ProfileService

# Audio
audio = AudioService()
thread, filename = audio.start_recording()
audio.stop_recording()

# Música
music = MusicService()
music.start_music(scale_type="mayor")
music.stop_music()

# Perfil
profile = ProfileService()
score, status, scale = profile.calculate_wellbeing(temp, hum, light, soil)
```

## ⚙️ Configuración

El archivo `configuracion.txt` se gestiona automáticamente:

```ini
tonalidad=C
dispositivo=0
frecuenciatemperatura=60
frecuenciahumedad_relativa=600
frecuenciailuminacion=1800
frecuenciahumedad_suelo=3600
rutaalmacenamiento=grabaciones
```

## 📊 Beneficios de la Refactorización

1. **Mantenibilidad**: Código organizado por responsabilidad
2. **Testabilidad**: Servicios y lógica independientes
3. **Escalabilidad**: Fácil agregar nuevas features
4. **Reusabilidad**: Componentes desacoplados
5. **Legibilidad**: Estructura clara y documentada

## 🔧 Próximos Pasos

Para completar la refactorización:

1. Migrar cada módulo UI a la nueva estructura
2. Actualizar imports en todos los archivos
3. Testear cada vista individualmente
4. Eliminar archivos obsoletos después de migración

## 📄 Licencia

[Tu licencia aquí]

## 👤 Autor

Victor
