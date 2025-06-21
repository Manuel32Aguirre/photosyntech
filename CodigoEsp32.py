from machine import Pin, ADC
import dht
import time
import uasyncio as asyncio
import _thread

# Pines
adc_pin = 34
dht_pin = 27
light_pin = 32
soil_pin = 33  # NUEVO: humedad de suelo

# ADC
adc = ADC(Pin(adc_pin))
adc.atten(ADC.ATTN_11DB)
adc.width(ADC.WIDTH_12BIT)

soil_adc = ADC(Pin(soil_pin))  # NUEVO
soil_adc.atten(ADC.ATTN_11DB)
soil_adc.width(ADC.WIDTH_12BIT)

# Sensores
dht_sensor = dht.DHT11(Pin(dht_pin))
light_adc = ADC(Pin(light_pin))
light_adc.atten(ADC.ATTN_11DB)

# Datos compartidos
sensor_data = {
    "T": "--",
    "H": "--",
    "L": "--",
    "S": "--"  # NUEVO: humedad suelo
}

# Cálculo Lux
def calcular_resistencia_ldr(raw_light, r_fija=470):
    v_out = (raw_light * 3.3) / 4095
    if v_out <= 0:
        return float('inf')
    return (3.3 * r_fija / v_out) - r_fija

def convertir_a_lux(raw_light):
    r_ldr = calcular_resistencia_ldr(raw_light)
    if r_ldr <= 0:
        return 0
    return round(500 * (r_ldr / 1000) ** -1.25, 2)

# Cálculo humedad suelo
def convertir_humedad_suelo(raw_value):
    # Suponemos calibración: seco = 0%, mojado = 100%
    # Puedes ajustar estos valores si calibras tu sensor:
    raw_seco = 3200  # valor cuando está totalmente seco
    raw_mojado = 1300  # valor cuando está completamente mojado

    porcentaje = (raw_value - raw_seco) / (raw_mojado - raw_seco)
    porcentaje = max(0.0, min(1.0, porcentaje))
    return round(porcentaje * 100, 1)

# Hilo sensores lentos
def read_sensors_thread():
    global sensor_data
    while True:
        try:
            dht_sensor.measure()
            temp = dht_sensor.temperature()
            hum = dht_sensor.humidity()
        except Exception as e:
            print("Error DHT11:", e)
            temp = hum = "--"

        try:
            raw_light = light_adc.read()
            light = convertir_a_lux(raw_light)
        except Exception as e:
            print("Error luz:", e)
            light = "--"

        try:
            raw_soil = soil_adc.read()
            soil_hum = convertir_humedad_suelo(raw_soil)
        except Exception as e:
            print("Error humedad suelo:", e)
            soil_hum = "--"

        sensor_data["T"] = temp
        sensor_data["H"] = hum
        sensor_data["L"] = light
        sensor_data["S"] = soil_hum  # NUEVO

        time.sleep(3)

# 🚀 Loop rápido (señal bioeléctrica cruda a 200 Hz)
async def send_bio_loop():
    while True:
        raw_bio = adc.read()
        volt_bio = raw_bio * 3.3 / 4095
        print(f"B:{volt_bio:.4f}")
        await asyncio.sleep(0.005)  # 5 ms → 200 Hz

# 🚀 Loop lento (sensores cada 3 s)
async def send_sensors_loop():
    while True:
        temp = sensor_data["T"]
        hum = sensor_data["H"]
        light = sensor_data["L"]
        soil = sensor_data["S"]  # NUEVO
        print(f"T:{temp},H:{hum},L:{light},S:{soil}")
        await asyncio.sleep(3)

# 🚀 Main
async def main():
    print("Esperando a que DHT11 se estabilice...")
    await asyncio.sleep(2)  # Aquí sí es compatible con asyncio
    _thread.start_new_thread(read_sensors_thread, ())
    await asyncio.gather(send_bio_loop(), send_sensors_loop())

try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Programa detenido")

