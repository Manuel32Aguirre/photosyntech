from machine import Pin, ADC
import dht
import time
import uasyncio as asyncio
import _thread

# Pines
adc_pin = 34
dht_pin = 14
soil_pin = 33
light_pin = 35

# Inicialización ADC
adc = ADC(Pin(adc_pin))
adc.atten(ADC.ATTN_11DB)       # Rango 0–3.3V
adc.width(ADC.WIDTH_12BIT)     # Resolución de 12 bits

# Sensores
dht_sensor = dht.DHT11(Pin(dht_pin))
soil_adc = ADC(Pin(soil_pin)); soil_adc.atten(ADC.ATTN_11DB)
light_adc = ADC(Pin(light_pin)); light_adc.atten(ADC.ATTN_11DB)

# Datos compartidos
sensor_data = {
    "temp": "--",
    "hum": "--",
    "soil": "--",
    "light": "--"
}

# 🔁 Sensor loop en segundo hilo
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
            raw_soil = soil_adc.read()
            raw_light = light_adc.read()
            soil = 100 - (raw_soil * 100 // 4095)
            light = raw_light * 1000 // 4095
        except Exception as e:
            print("Error suelo/luz:", e)
            soil = light = "--"

        sensor_data["temp"] = temp
        sensor_data["hum"] = hum
        sensor_data["soil"] = soil
        sensor_data["light"] = light

        time.sleep(3)

# 📤 Enviar señal cruda (en voltios)
async def send_data():
    while True:
        raw_bio = adc.read()
        volt_bio = raw_bio * 3.3 / 4095  # Solo voltaje real, sin calibrar

        # Copiar datos de sensores
        temp = sensor_data["temp"]
        hum = sensor_data["hum"]
        soil = sensor_data["soil"]
        light = sensor_data["light"]

        print(f"DATA:BIO:{volt_bio:.4f},TEMP:{temp},HUM:{hum},SOIL:{soil},LIGHT:{light}")
        await asyncio.sleep(0.025)  # 40 Hz

# 🚀 Main
async def main():
    _thread.start_new_thread(read_sensors_thread, ())
    while True:
        await send_data()

try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Programa detenido")

