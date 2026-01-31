import os
import base64
import resend
import urllib.parse

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
FROM_EMAIL = "suporte@trx-email.pages.dev"  # seu domínio verificado
WHATSAPP_NUMERO = "5511999999999"  # SEU número com DDI + DDD

resend.api_key = RESEND_API_KEY


def enviar_email(destinatario, nome_plano, arquivo, senha):
    # Converte arquivo para base64
    with open(arquivo, "rb") as f:
        arquivo_base64 = base64.b64encode(f.read()).decode("ascii")

    # Mensagem padrão do WhatsApp
    mensagem_whatsapp = (
        f"Olá! Acabei de comprar o plano {nome_plano} "
        f"e gostaria de suporte 😊"
    )

    mensagem_codificada = urllib.parse.quote(mensagem_whatsapp)

    link_whatsapp = (
        f"https://wa.me/{WHATSAPP_NUMERO}?text={mensagem_codificada}"
    )

    resend.Emails.send({
        "from": FROM_EMAIL,
        "to": [destinatario],
        "subject": f"Seu plano {nome_plano} – Acesso Liberado",
        "html": f"""
        <h2>Pagamento confirmado 🎉</h2>

        <p><strong>Plano:</strong> {nome_plano}</p>
        <p><strong>Senha do arquivo:</strong> {senha}</p>

        <p>Se precisar de ajuda, fale conosco no WhatsApp:</p>

        <p>
          <a href="{link_whatsapp}"
             style="background:#25D366;color:white;
                    padding:12px 18px;
                    text-decoration:none;
                    border-radius:6px;
                    font-weight:bold;">
            📲 Falar no WhatsApp
          </a>
        </p>

        <p>Arquivo em anexo.</p>
        """,
        "attachments": [
            {
                "filename": os.path.basename(arquivo),
                "content": arquivo_base64,
                "content_type": "application/zip"
            }
        ]
    })
