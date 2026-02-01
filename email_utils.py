import requests

GOOGLE_EMAIL_WEBHOOK = "https://script.google.com/macros/s/AKfycbzH164PLVUzyRasj2GE_fMyCTXVeUznbixlWXZSf7cnZPFX6FYuv0UhA82oYeelIzjU/exec"

def enviar_email(destinatario, nome_plano, senha):
    payload = {
        "email": destinatario,
        "assunto": f"Seu plano {nome_plano} – Acesso Liberado",
        "mensagem": f"""
Olá,

Seu pagamento foi confirmado com sucesso!

Plano: {nome_plano}
Senha do arquivo: {senha}

Bom uso!
"""
    }

    response = requests.post(GOOGLE_EMAIL_WEBHOOK, json=payload)
    response.raise_for_status()
