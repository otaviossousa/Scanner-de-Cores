import json
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

def classificar_cor(leitura_norm):
    if not referencias:
        return None, None, 0

    melhor_cor = None
    menor_distancia = None

    for cor, dados in referencias.items():
        ref = dados["norm"]
        distancia = sensor.distancia(leitura_norm, ref)

        if menor_distancia is None or distancia < menor_distancia:
            menor_distancia = distancia
            melhor_cor = cor

    confianca = 0 if menor_distancia is None else max(0, 100 - (menor_distancia * 300))
    return melhor_cor, menor_distancia, confianca

def estimar_hex(leitura_norm):
    # Encontra o maior valor para esticar as proporções até 255 (simulando brilho em telas)
    max_val = max(leitura_norm["rn"], leitura_norm["gn"], leitura_norm["bn"])
    if max_val == 0:
        return "#000000"

    r = int((leitura_norm["rn"] / max_val) * 255)
    g = int((leitura_norm["gn"] / max_val) * 255)
    b = int((leitura_norm["bn"] / max_val) * 255)

    return f"#{r:02x}{g:02x}{b:02x}"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/cor")
def api_cor():
    # 5 amostras com intervalo de 20ms tornam a resposta rápida (aprox. 0.1s de espera)
    leitura = sensor.ler_media(amostras=5, intervalo=0.02)
    leitura_norm = sensor.normalizar_rgb(leitura)
    cor, distancia, confianca = classificar_cor(leitura_norm)

    if cor is None:
        return jsonify({"erro": "Nenhuma cor calibrada no arquivo."}), 400

    return jsonify({
        "cor": cor,
        "distancia": round(distancia, 4),
        "confianca": round(confianca, 2),
        "leitura_norm": leitura_norm,
        "hex_estimado": estimar_hex(leitura_norm)
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
