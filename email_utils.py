import base64
import os
import unicodedata

import requests

print("EMAIL_UTILS CARREGADO")

GOOGLE_EMAIL_WEBHOOK = os.environ.get(
    "GOOGLE_EMAIL_WEBHOOK",
    "https://script.google.com/macros/s/AKfycbzqsLLYy7IfyEIYAyXD7yx8K9A5ojbNeOVyTVSEqLr6Y0dp3I5RgdgYjmeT7UYItkjuXw/exec",
).strip()
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "https://www.trxpro.com.br").strip().rstrip("/")
EMAIL_BANNER_PATH = (os.environ.get("EMAIL_BANNER_PATH") or "/assets/banner-email.jpg").strip() or "/assets/banner-email.jpg"
if not EMAIL_BANNER_PATH.startswith("/"):
    EMAIL_BANNER_PATH = "/" + EMAIL_BANNER_PATH


def _enviar_payload_email(payload):
    if not GOOGLE_EMAIL_WEBHOOK:
        raise RuntimeError("GOOGLE_EMAIL_WEBHOOK nao configurado.")

    response = requests.post(
        GOOGLE_EMAIL_WEBHOOK,
        json=payload,
        timeout=60,
    )
    if response.status_code != 200:
        raise RuntimeError(f"Falha no envio de email. Status={response.status_code} Body={response.text}")


def _arquivo_para_base64(caminho_arquivo):
    if not os.path.exists(caminho_arquivo):
        raise FileNotFoundError(f"Arquivo nao encontrado: {caminho_arquivo}")

    with open(caminho_arquivo, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _email_banner_url():
    base = (PUBLIC_BASE_URL or "https://www.trxpro.com.br").strip().rstrip("/")
    return f"{base}{EMAIL_BANNER_PATH}"


def _email_banner_html():
    url = _email_banner_url()
    return (
        f'<div style="padding:0;margin:0 0 14px;">'
        f'<img src="{url}" alt="TRX PRO" '
        f'style="display:block;width:100%;max-width:620px;height:auto;border:0;outline:none;text-decoration:none;">'
        f'</div>'
    )


def enviar_email_com_anexo(destinatario, assunto, mensagem, caminho_arquivo, html=None):
    arquivo_base64 = _arquivo_para_base64(caminho_arquivo)
    payload = {
        "email": destinatario,
        "assunto": assunto,
        "mensagem": mensagem,
        "filename": os.path.basename(caminho_arquivo),
        "file_base64": arquivo_base64,
    }
    if html:
        payload["html"] = html
    _enviar_payload_email(payload)


def enviar_email_simples(destinatario, assunto, mensagem, html=None):
    payload = {
        "email": destinatario,
        "assunto": assunto,
        "mensagem": mensagem,
    }
    if html:
        payload["html"] = html
    try:
        _enviar_payload_email(payload)
    except RuntimeError as exc:
        erro = str(exc)
        # Fallback para scripts do Google Apps Script que exigem sempre arquivo.
        if "newBlob" not in erro:
            raise

        fallback_payload = dict(payload)
        fallback_payload["filename"] = "mensagem.txt"
        conteudo = (mensagem or "Mensagem TRX PRO").encode("utf-8")
        fallback_payload["file_base64"] = base64.b64encode(conteudo).decode("utf-8")
        _enviar_payload_email(fallback_payload)


def _corrigir_texto_quebrado(texto):
    valor = (texto or "").strip()
    if not valor:
        return ""

    for _ in range(2):
        if "Ã" not in valor and "Â" not in valor:
            break
        try:
            valor = valor.encode("latin1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            break

    return valor


def _normalizar_nome_plano(nome_plano):
    nome = _corrigir_texto_quebrado(nome_plano)
    if not nome:
        return "TRX PRO"

    sem_acento = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode("ascii")
    return sem_acento.strip() or "TRX PRO"


def enviar_email(destinatario, nome_plano, arquivo, senha, nome_cliente=None):
    nome_plano_fmt = _normalizar_nome_plano(nome_plano)
    nome_cliente_fmt = (nome_cliente or "").strip()
    saudacao = f"Ola, {nome_cliente_fmt}" if nome_cliente_fmt else "Ola"

    mensagem = f"""{saudacao}

Obrigado pela sua compra!

Pagamento confirmado com sucesso.

Plano adquirido: {nome_plano_fmt}
Senha do arquivo: {senha}

(ASSISTA AGORA)
Tutorial de como baixar, descompactar e instalar o robo:
https://youtu.be/u3GWhwR8bcQ?si=3mb8yraHc_KKruFF

IMPORTANTE - ENTRE NA COMUNIDADE OFICIAL
Para receber avisos, atualizacoes e suporte, entre no grupo abaixo:
https://chat.whatsapp.com/KPcaKf6OsaQHG2cUPAU1CE

O arquivo do seu plano esta em anexo neste email.

Importante:
- Guarde sua senha
- Nao compartilhe o arquivo

Suporte:
Email: trxtradingpro@gmail.com
WhatsApp: +55 11 94043-1906
WhatsApp 2: +55 11 98175-9207

Bom uso
"""
    assunto = f"Seu plano {nome_plano_fmt} - Acesso Liberado"
    banner_html = _email_banner_html()
    html = f"""
    <div style="font-family:Arial,Helvetica,sans-serif;background:#060b16;padding:24px;">
      <div style="max-width:620px;margin:0 auto;background:#0d1629;border:1px solid #203354;border-radius:14px;overflow:hidden;">
        {banner_html}
        <div style="padding:18px 20px;background:linear-gradient(90deg,#16a34a,#0ea5e9);color:#04111d;font-weight:800;font-size:18px;">
          Acesso Liberado - {nome_plano_fmt}
        </div>
        <div style="padding:22px 20px;color:#eaf2ff;line-height:1.55;">
          <p style="margin:0 0 12px;">{saudacao}!</p>
          <p style="margin:0 0 12px;">Pagamento confirmado com sucesso.</p>
          <div style="margin:14px 0;padding:14px;border:1px solid #27436c;border-radius:12px;background:#0a1323;">
            <div style="margin-bottom:8px;"><strong>Plano adquirido:</strong> {nome_plano_fmt}</div>
            <div><strong>Senha do arquivo:</strong> {senha}</div>
          </div>
          <p style="margin:0 0 12px;"><strong>Tutorial:</strong> https://youtu.be/u3GWhwR8bcQ?si=3mb8yraHc_KKruFF</p>
          <p style="margin:0 0 12px;"><strong>Comunidade oficial:</strong> https://chat.whatsapp.com/KPcaKf6OsaQHG2cUPAU1CE</p>
          <p style="margin:0 0 12px;">O arquivo do seu plano esta em anexo neste e-mail.</p>
          <p style="margin:0;color:#9eb2d4;font-size:12px;">
            Importante: guarde sua senha e nao compartilhe o arquivo.
          </p>
        </div>
      </div>
    </div>
    """
    enviar_email_com_anexo(
        destinatario=destinatario,
        assunto=assunto,
        mensagem=mensagem,
        caminho_arquivo=arquivo,
        html=html,
    )
