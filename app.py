from flask import Flask, request, jsonify, render_template, redirect
import os
import uuid
import json

from compactador import compactar_plano
from email_utils import enviar_email

from database import (
    init_db,
    salvar_order_email,
    buscar_email,
    transacao_ja_processada,
    marcar_processada
)

app = Flask(__name__)

# ======================================================
# INIT
# ======================================================

init_db()
PASTA_SAIDA = "saida"
os.makedirs(PASTA_SAIDA, exist_ok=True)

# ======================================================
# PLANOS
# ======================================================

PLANOS = {
    "trx-bronze-0001": {"nome": "TRX BRONZE", "pasta": "Licencas/TRX BRONZE"},
    "trx-prata-0001":  {"nome": "TRX PRATA",  "pasta": "Licencas/TRX PRATA"},
    "trx-gold-0001":   {"nome": "TRX GOLD",   "pasta": "Licencas/TRX GOLD"},
    "trx-black-0001":  {"nome": "TRX BLACK",  "pasta": "Licencas/TRX BLACK"},
    "trx-teste-0001":  {"nome": "TRX TESTE",  "pasta": "Licencas/TRX BRONZE"},
}

# ======================================================
# LINKS CHECKOUT INFINITEPAY
# ======================================================

CHECKOUT_LINKS = {
    "trx-bronze-0001": "SEU_LINK_AQUI",
    "trx-prata-0001":  "SEU_LINK_AQUI",
    "trx-gold-0001":   "SEU_LINK_AQUI",
    "trx-black-0001":  "SEU_LINK_AQUI",
    "trx-teste-0001":  "SEU_LINK_AQUI",
}

# ======================================================
# CHECKOUT (ANTES DO PAGAMENTO)
# ======================================================

@app.route("/checkout/<plano>")
def checkout(plano):
    if plano not in PLANOS:
        return "Plano inválido", 404
    return render_template("checkout.html", plano=plano)

@app.route("/comprar", methods=["POST"])
def comprar():
    email = request.form.get("email")
    telefone = request.form.get("telefone")
    plano = request.form.get("plano")

    if not email or not telefone or plano not in PLANOS:
        return "Dados inválidos", 400

    # identificador interno nosso (100% controlado)
    ref = f"{plano}-{uuid.uuid4().hex[:10]}"

    salvar_order_email(ref, email)

    print(f"🛒 CHECKOUT CRIADO | ref={ref} | email={email} | telefone={telefone}")

    checkout_base = CHECKOUT_LINKS[plano]
    checkout_url = f"{checkout_base}&reference={ref}"

    return redirect(checkout_url)

# ======================================================
# WEBHOOK INFINITEPAY (BLINDADO)
# ======================================================

@app.route("/webhook/infinitypay", methods=["POST"])
def webhook():
    print("\n================ WEBHOOK RECEBIDO ================")

    # -------- RAW BODY --------
    raw_body = request.data.decode("utf-8", errors="ignore")
    print("🧾 RAW BODY:")
    print(raw_body)

    # -------- JSON --------
    try:
        data = request.get_json(force=True, silent=True)
    except Exception as e:
        print("❌ ERRO AO PARSEAR JSON:", e)
        data = None

    print("📦 JSON PARSEADO:", data)

    if not data:
        print("❌ Payload vazio ou inválido")
        return jsonify({"msg": "Payload inválido"}), 200

    # -------- IDENTIFICADORES POSSÍVEIS --------
    transaction_nsu = (
        data.get("transaction_nsu")
        or data.get("transactionId")
        or data.get("id")
    )

    reference = (
        data.get("reference")
        or data.get("invoice_slug")
        or data.get("order_nsu")
    )

    paid_amount = (
        data.get("paid_amount")
        or data.get("amount")
        or 0
    )

    print("🔑 transaction_nsu:", transaction_nsu)
    print("🔑 reference:", reference)
    print("💰 paid_amount:", paid_amount)

    # -------- VALIDAÇÕES --------
    if not transaction_nsu:
        print("❌ transaction_nsu ausente")
        return jsonify({"msg": "transaction_nsu ausente"}), 200

    if not reference:
        print("❌ reference ausente")
        return jsonify({"msg": "reference ausente"}), 200

    if float(paid_amount) <= 0:
        print("❌ Pagamento não confirmado")
        return jsonify({"msg": "Pagamento não confirmado"}), 200

    if transacao_ja_processada(transaction_nsu):
        print("🔁 Transação já processada")
        return jsonify({"msg": "Já processado"}), 200

    # -------- PLANO --------
    plano_id = reference.rsplit("-", 1)[0]
    print("📦 plano_id:", plano_id)

    if plano_id not in PLANOS:
        print("❌ Plano inválido:", plano_id)
        return jsonify({"msg": "Plano inválido"}), 200

    # -------- EMAIL --------
    email = buscar_email(reference)
    print("📧 EMAIL BUSCADO:", email)

    if not email:
        print("❌ Email não encontrado para:", reference)
        return jsonify({"msg": "Email não encontrado"}), 200

    plano = PLANOS[plano_id]
    arquivo = None

    try:
        print("📦 Gerando arquivo...")
        arquivo, senha = compactar_plano(plano["pasta"], PASTA_SAIDA)

        print("📧 Enviando email...")
        enviar_email(
            destinatario=email,
            nome_plano=plano["nome"],
            arquivo=arquivo,
            senha=senha
        )

        marcar_processada(transaction_nsu)
        print("✅ EMAIL ENVIADO COM SUCESSO")

    except Exception as e:
        print("❌ ERRO CRÍTICO:", str(e))
        return jsonify({"msg": "Erro interno"}), 500

    finally:
        if arquivo and os.path.exists(arquivo):
            os.remove(arquivo)
            print("🧹 Arquivo removido")

    print("================ FIM WEBHOOK ================\n")
    return jsonify({"msg": "OK"}), 200

# ======================================================
# START
# ======================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
