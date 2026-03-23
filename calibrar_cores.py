import json
from sensor_cor import SensorCor

ARQUIVO = "cores_calibradas.json"

sensor = SensorCor(integration_time=100, gain=4)

try:
    # Carrega os dados existentes para não apagar o que já foi calibrado
    with open(ARQUIVO, "r", encoding="utf-8") as f:
        dados = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    dados = {}

print("=== CALIBRACAO DE CORES ===")
print("Mantenha sempre a mesma distancia entre o objeto e o sensor.")
print("Evite luz ambiente variando durante a calibracao.\n")
print("Digite 'sair' a qualquer momento para finalizar e salvar.\n")

while True:
    cor = input("Digite o NOME da cor (ex: rosa, vermelho_escuro) ou 'sair': ").strip().lower()
    if cor == 'sair':
        break
    if not cor:
        continue

    input(f"Coloque a cor [{cor}] na frente do sensor e pressione ENTER... ")

    leitura = sensor.ler_media(amostras=20, intervalo=0.05)
    normalizado = sensor.normalizar_rgb(leitura)

    dados[cor] = {
        "raw": leitura,
        "norm": normalizado
    }

    print(f"Cor [{cor}] salva:")
    print(f"  bruto = {leitura}")
    print(f"  norm  = {normalizado}\n")

with open(ARQUIVO, "w", encoding="utf-8") as f:
    json.dump(dados, f, indent=4, ensure_ascii=False)

print(f"Calibracao salva em {ARQUIVO}")
