import time
import math
import board
import busio
import adafruit_tcs34725


class SensorCor:
    def __init__(self, integration_time=100, gain=4):
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.sensor = adafruit_tcs34725.TCS34725(self.i2c)

        # Ajustes do sensor
        # integration_time: tempo de integração em ms
        # gain: ganho do sensor
        self.sensor.integration_time = integration_time
        self.sensor.gain = gain

    def ler_bruto(self):
        r, g, b, c = self.sensor.color_raw
        return {
            "r": r,
            "g": g,
            "b": b,
            "c": c
        }

    def ler_media(self, amostras=10, intervalo=0.05):
        leituras = []
        for _ in range(amostras):
            leituras.append(self.ler_bruto())
            time.sleep(intervalo)

        # Para maior precisão, descarta as leituras extremas (ruído) se houver amostras suficientes
        if amostras >= 5:
            leituras = sorted(leituras, key=lambda x: x["c"])[1:-1]
            amostras = len(leituras)

        soma_r = sum(l["r"] for l in leituras)
        soma_g = sum(l["g"] for l in leituras)
        soma_b = sum(l["b"] for l in leituras)
        soma_c = sum(l["c"] for l in leituras)

        return {
            "r": soma_r / amostras,
            "g": soma_g / amostras,
            "b": soma_b / amostras,
            "c": soma_c / amostras
        }

    def normalizar_rgb(self, leitura):
        r = leitura["r"]
        g = leitura["g"]
        b = leitura["b"]

        total = r + g + b
        if total == 0:
            return {
                "rn": 0,
                "gn": 0,
                "bn": 0
            }

        return {
            "rn": r / total,
            "gn": g / total,
            "bn": b / total
        }

    def brilho_relativo(self, leitura):
        c = leitura["c"]
        rgb_total = leitura["r"] + leitura["g"] + leitura["b"]

        if c <= 0:
            return 0

        return rgb_total / c

    def distancia(self, a, b):
        return math.sqrt(
            (a["rn"] - b["rn"]) ** 2 +
            (a["gn"] - b["gn"]) ** 2 +
            (a["bn"] - b["bn"]) ** 2
        )
