import os
import resend

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
FROM_EMAIL = "onboarding@resend.dev"

resend.api_key = RESEND_API_KEY

def enviar_email(destinatario, nome_plano, arquivo, senha):
    with open(arquivo, "rb") as f:
        conteudo = f.read()

    resend.Emails.send({
        "from": FROM_EMAIL,
        "to": destinatario,
        "subject": f"Seu plano {nome_plano} – Acesso Liberado",
        "html": f"""
        <h2>Pagamento confirmado!</h2>
        <p><strong>Plano:</strong> {nome_plano}</p>
        <p><strong>Senha do arquivo:</strong> {senha}</p>
        <p>Arquivo em anexo.</p>
        """,
        "attachments": [
            {
                "filename": os.path.basename(arquivo),
                "content": conteudo
            }
        ]
    })
