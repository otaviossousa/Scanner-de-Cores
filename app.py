import json
import math
from flask import Flask, jsonify, render_template
from sensor_cor import SensorCor

app = Flask(__name__)
sensor = SensorCor(integration_time=100, gain=4)
ARQUIVO = "cores_calibradas.json"

def carregar_referencias():
    try:
        with open(ARQUIVO, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

referencias = carregar_referencias()

# Dicionário Universal para adivinhar cores sem precisar de calibração
CORES_UNIVERSAIS = {
    "Vermelho": (255, 0, 0),
    "Verde": (0, 255, 0),
    "Azul": (0, 0, 255),
    "Amarelo": (255, 255, 0),
    "Ciano": (0, 255, 255),
    "Rosa / Magenta": (255, 0, 255),
    "Roxo": (128, 0, 128),
    "Laranja": (255, 128, 0),
    "Branco": (255, 255, 255),
    "Preto": (0, 0, 0)
}

def estimar_rgb(leitura_norm):
    max_val = max(leitura_norm["rn"], leitura_norm["gn"], leitura_norm["bn"])
    if max_val == 0:
        return 0, 0, 0
    r = int((leitura_norm["rn"] / max_val) * 255)
    g = int((leitura_norm["gn"] / max_val) * 255)
    b = int((leitura_norm["bn"] / max_val) * 255)
    return r, g, b

def classificar_cor(leitura_norm):
    melhor_cor = None
    menor_distancia = None

    if referencias:
        for cor, dados in referencias.items():
            ref = dados["norm"]
            distancia = sensor.distancia(leitura_norm, ref)

            if menor_distancia is None or distancia < menor_distancia:
                menor_distancia = distancia
                melhor_cor = cor

    confianca = 0 if menor_distancia is None else max(0, 100 - (menor_distancia * 300))

    r, g, b = estimar_rgb(leitura_norm)
    hex_estimado = f"#{r:02x}{g:02x}{b:02x}"

    # Se não há calibração ou a confiança é muito baixa, tenta o Dicionário Universal
    if melhor_cor is None or confianca < 30:
        menor_dist_univ = float('inf')
        cor_univ = "Desconhecida"
        for nome, (cr, cg, cb) in CORES_UNIVERSAIS.items():
            dist = math.sqrt((r - cr)**2 + (g - cg)**2 + (b - cb)**2)
            if dist < menor_dist_univ:
                menor_dist_univ = dist
                cor_univ = nome

        melhor_cor = f"{cor_univ} (Auto)"
        # Calcula uma confiança aproximada (0 a 100) baseada na distância do RGB 0-255
        confianca = max(0, 100 - (menor_dist_univ / 3))
        if menor_distancia is None:
            menor_distancia = 0

    return melhor_cor, menor_distancia, confianca, hex_estimado

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/cor")
def api_cor():
    # 5 amostras com intervalo de 20ms tornam a resposta rápida (aprox. 0.1s de espera)
    leitura = sensor.ler_media(amostras=5, intervalo=0.02)
    leitura_norm = sensor.normalizar_rgb(leitura)
    cor, distancia, confianca, hex_estimado = classificar_cor(leitura_norm)

    return jsonify({
        "cor": cor,
        "distancia": round(distancia, 4),
        "confianca": round(confianca, 2),
        "leitura_norm": leitura_norm,
        "hex_estimado": hex_estimado
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
