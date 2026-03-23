import json
import math
import time
from sensor_cor import SensorCor

ARQUIVO = "cores_calibradas.json"

try:
    sensor = SensorCor(integration_time=100, gain=4)
except Exception as e:
    print("="*50)
    print(f"ERRO FATAL: Não foi possível inicializar o sensor de cor.")
    print(f"Verifique a conexão do hardware (pinos SCL, SDA, VCC, GND).")
    print(f"Detalhes do erro: {e}")
    print("="*50)
    exit()

try:
    with open(ARQUIVO, "r", encoding="utf-8") as f:
        referencias = json.load(f)
except Exception:
    referencias = {}

# Dicionário Universal e funções de classificação (copiado de app.py para teste)
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

    if isinstance(referencias, dict):
        for cor, dados in referencias.items():
            if not isinstance(dados, dict):
                continue
            ref = dados.get("norm")
            if not isinstance(ref, dict):
                continue
            try:
                ref_seguro = {
                    "rn": float(ref["rn"]),
                    "gn": float(ref["gn"]),
                    "bn": float(ref["bn"])
                }
                if math.isnan(ref_seguro["rn"]) or math.isnan(ref_seguro["gn"]) or math.isnan(ref_seguro["bn"]):
                    continue
            except (KeyError, ValueError, TypeError):
                continue
            distancia = sensor.distancia(leitura_norm, ref_seguro)
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


print("=== IDENTIFICADOR DE CORES (MODO DE TESTE) ===")
print("Pressione Ctrl+C para sair.\n")

while True:
    try:
        leitura = sensor.ler_media(amostras=10, intervalo=0.05)
        leitura_norm = sensor.normalizar_rgb(leitura)

        cor, distancia, confianca, hex_val = classificar_cor(leitura_norm)

        print(f"Leitura Norm.: rn={leitura_norm['rn']:.3f}, gn={leitura_norm['gn']:.3f}, bn={leitura_norm['bn']:.3f}")
        print(f"Cor Detectada: {cor}")
        print(f"HEX Estimado:  {hex_val}")
        print(f"Confianca: {confianca:.2f}%")
        # A distância só é relevante para cores calibradas, não para as "Auto"
        if "(Auto)" not in cor:
            print(f"Distancia: {distancia:.4f}")
    except Exception as e:
        print(f"!!! ERRO AO LER O SENSOR: {e}")
        print("Verifique a conexão do hardware. Nova tentativa em 5 segundos...")
        time.sleep(5)
    print("-" * 40)
