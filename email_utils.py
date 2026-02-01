import base64
import requests
import os

GOOGLE_EMAIL_WEBHOOK = "https://script.google.com/macros/s/AKfycbzqsLLYy7IfyEIYAyXD7yx8K9A5ojbNeOVyTVSEqLr6Y0dp3I5RgdgYjmeT7UYItkjuXw/exec"

def enviar_email(destinatario, nome_plano, arquivo, senha):
    with open(arquivo, "rb") as f:
        arquivo_base64 = base64.b64encode(f.read()).decode("utf-8")

    payload = {
        "email": destinatario,
        "assunto": f"Seu plano {nome_plano} – Acesso Liberado",
        "mensagem": f"""Olá 

Obrigado pela sua compra!

✅ Pagamento confirmado com sucesso.

 📦Plano adquirido: {nome_plano}
 🔐Senha do arquivo: {senha}
 
 (IMPORTANTE) entre na comunidade abaixo para informações:
 
 O arquivo do seu plano está em anexo logo abaixo neste email.

⚠️ Importante:
– Guarde sua senha
– Não compartilhe o arquivo

Qualquer dúvida, é só responder este email entre em contato com o suporte:
Email: trxtradingpro@gmail.com

WhatsApp +55 11 98175-9207
WhatsApp2 +55 11 94043-1906


Bom uso 
"""
,
        "filename": os.path.basename(arquivo),
        "file_base64": arquivo_base64
    }

    requests.post(GOOGLE_EMAIL_WEBHOOK, json=payload, timeout=60)



