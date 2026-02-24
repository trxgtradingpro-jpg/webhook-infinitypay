import os
import random
import string
import subprocess


def gerar_senha(tamanho=16):
    chars = string.ascii_letters + string.digits + "!@#$%&*"
    return "".join(random.choice(chars) for _ in range(tamanho))


def compactar_plano(caminho_origem, pasta_saida):
    caminho_origem = os.path.normpath(caminho_origem or "")
    if not caminho_origem or not os.path.exists(caminho_origem):
        raise FileNotFoundError(f"Origem do plano nao encontrada: {caminho_origem}")

    senha = gerar_senha()
    nome = os.path.basename(caminho_origem)
    if os.path.isfile(caminho_origem):
        nome = os.path.splitext(nome)[0]
    if not nome:
        nome = "plano"

    zip_saida = os.path.join(pasta_saida, f"{nome}.zip")

    os.makedirs(pasta_saida, exist_ok=True)
    if os.path.exists(zip_saida):
        os.remove(zip_saida)

    if os.path.isfile(caminho_origem):
        comando = ["zip", "-j", "-P", senha, zip_saida, caminho_origem]
    else:
        comando = ["zip", "-r", "-P", senha, zip_saida, caminho_origem]

    resultado = subprocess.run(comando, capture_output=True, text=True)
    if resultado.returncode != 0:
        erro = (resultado.stderr or resultado.stdout or "").strip()
        raise RuntimeError(f"Falha ao compactar plano: {erro}")

    return zip_saida, senha
