from urllib.parse import parse_qs, urlparse


def _texto_whatsapp(url):
    parsed = urlparse(url)
    return parse_qs(parsed.query).get("text", [""])[0]


def test_gera_link_whatsapp_pendente_plano_pago_usa_template_conversao(app_module, monkeypatch):
    monkeypatch.setattr(app_module, "WHATSAPP_MENSAGEM", "PADRAO {nome} {plano}")
    monkeypatch.setattr(
        app_module,
        "WHATSAPP_PENDENTE_PAGO_TEMPLATE",
        "CONVERSAO {nome} {plano} {valor} {site}",
    )

    order = {
        "nome": "Gui",
        "telefone": "11999998888",
        "plano": "trx-gold",
        "status": "PENDENTE",
    }
    link = app_module.gerar_link_whatsapp(order)

    assert link is not None
    assert link.startswith("https://wa.me/5511999998888?text=")
    texto = _texto_whatsapp(link)
    assert texto == "CONVERSAO Gui TRX GOLD R$ 497,00 https://example.com"


def test_gera_link_whatsapp_plano_gratis_nao_usa_template_conversao(app_module, monkeypatch):
    monkeypatch.setattr(app_module, "WHATSAPP_MENSAGEM", "PADRAO {nome} {plano}")
    monkeypatch.setattr(
        app_module,
        "WHATSAPP_PENDENTE_PAGO_TEMPLATE",
        "CONVERSAO {nome} {plano} {valor} {site}",
    )

    order = {
        "nome": "Gui",
        "telefone": "11999998888",
        "plano": "trx-gratis",
        "status": "PENDENTE",
    }
    link = app_module.gerar_link_whatsapp(order)

    assert link is not None
    texto = _texto_whatsapp(link)
    assert texto == "PADRAO Gui TRX GRATIS"
