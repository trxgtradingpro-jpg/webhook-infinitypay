from flask import Flask, request, jsonify
from compactador import compactar_plano
from email_utils import enviar_email
import os
import json

app = Flask(__name__)

# ================= PLANOS =================
PLANOS = {
    "chk_abc123": {"nome": "TRX BRONZE", "pasta": "Licencas/TRX BRONZE"}
}
# ==========================================

PASTA_SAIDA = "saida"
ARQUIVO_PROCESSADOS = "processados.json"


def pagamento_ja_processado(pagamento_id):
    if not os.path.exists(ARQUIVO_PROCESSADOS):
        return False

    with open(ARQUIVO_PROCESSADOS, "r", encoding="utf-8") as f:
        processados = json.load(f)

    return pagamento_id in processados


def marcar_pagamento_processado(pagamento_id):
    if os.path.exists(ARQUIVO_PROCESSADOS):
        with open(ARQUIVO_PROCESSADOS, "r", encoding="utf-8") as f:
            processados = json.load(f)
    else:
        processados = []

    processados.append(pagamento_id)

    with open(ARQUIVO_PROCESSADOS, "w", encoding="utf-8") as f:
        json.dump(processados, f)


@app.route("/webhook/infinitypay", methods=["POST"])
def webhook():
    data = request.get_json(force=True, silent=True)

    if not data:
        return jsonify({"error": "Payload inválido"}), 400

    # Confirma pagamento
    if data.get("status") != "paid":
        return jsonify({"msg": "Pagamento não aprovado"}), 200

    # ID único do pagamento (fallback seguro)
    pagamento_id = data.get("id") or data.get("transaction_id")

    if pagamento_id and pagamento_ja_processado(pagamento_id):
        return jsonify({"msg": "Pagamento já processado"}), 200

    plano_id = data.get("product_id")
    cliente = data.get("customer", {})
    email = cliente.get("email")

    if not email:
        return jsonify({"error": "Email não encontrado"}), 400

    if plano_id not in PLANOS:
        return jsonify({"error": "Plano não reconhecido"}), 400

    plano = PLANOS[plano_id]

    if not os.path.exists(plano["pasta"]):
        return jsonify({"error": "Pasta do plano não encontrada"}), 500

    # Gera ZIP + senha
    arquivo, senha = compactar_plano(plano["pasta"], PASTA_SAIDA)

    # Envia email
    enviar_email(
        destinatario=email,
        nome_plano=plano["nome"],
        arquivo=arquivo,
        senha=senha
    )

    # Marca pagamento como processado
    if pagamento_id:
        marcar_pagamento_processado(pagamento_id)

    # Remove o ZIP após envio
    try:
        os.remove(arquivo)
    except Exception:
        pass

    return jsonify({"msg": "Plano enviado com sucesso"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    os.makedirs(PASTA_SAIDA, exist_ok=True)
    app.run(host="0.0.0.0", port=port)
