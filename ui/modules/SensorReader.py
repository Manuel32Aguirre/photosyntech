import random

def get_sensor_data():
    return {
        "Temperatura": random.uniform(15, 30),
        "Humedad Suelo": random.uniform(20, 90),
        "Humedad Ambiente": random.uniform(30, 90),
        "Iluminación": random.uniform(200, 1000)
    }
