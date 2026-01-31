import os
import base64
import resend

# ================= CONFIG =================
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
FROM_EMAIL = "onboarding@resend.dev"
# =========================================

resend.api_key = RESEND_API_KEY


def enviar_email(destinatario, nome_plano, arquivo, senha):
    # Lê o arquivo e converte para BASE64 STRING
    with open(arquivo, "rb") as f:
        arquivo_base64 = base64.b64encode(f.read()).decode("ascii")

    resend.Emails.send({
        "from": FROM_EMAIL,
        "to": [destinatario],
        "subject": f"Seu plano {nome_plano} – Acesso Liberado",
        "html": (
            f"<h2>Pagamento confirmado</h2>"
            f"<p><strong>Plano:</strong> {nome_plano}</p>"
            f"<p><strong>Senha do arquivo:</strong> {senha}</p>"
            f"<p>Arquivo em anexo.</p>"
        ),
        "attachments": [
            {
                "filename": os.path.basename(arquivo),
                "content": arquivo_base64,
                "content_type": "application/zip"
            }
        ]
    })
