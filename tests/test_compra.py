def test_compra_plano_pago_redireciona_checkout(app_module, client, monkeypatch):
    funnel_calls = []
    agendamentos = []

    monkeypatch.setattr(app_module, "validar_csrf_token", lambda token: True)
    monkeypatch.setattr(app_module, "listar_pedidos_pagos_por_email", lambda email, limite=1: [])
    monkeypatch.setattr(app_module, "resolver_afiliado_para_compra", lambda **kwargs: (None, {}))
    monkeypatch.setattr(app_module, "salvar_order", lambda **kwargs: None)
    monkeypatch.setattr(app_module, "criar_checkout_dinamico", lambda **kwargs: "https://checkout.example/mock")
    monkeypatch.setattr(
        app_module,
        "agendar_alerta_email_novo_cadastro",
        lambda order_id, delay_minutes=None: agendamentos.append({"order_id": order_id, "delay_minutes": delay_minutes}) or True
    )
    monkeypatch.setattr(
        app_module,
        "registrar_evento_funil",
        lambda *args, **kwargs: funnel_calls.append({"args": args, "kwargs": kwargs}) or True
    )

    response = client.post(
        "/comprar",
        data={
            "csrf_token": "ok",
            "nome": "Gui Trader",
            "email": "gui@example.com",
            "telefone": "11999999999",
            "plano": "trx-gold",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "https://checkout.example/mock"
    assert funnel_calls, "esperava registrar evento de funil no submit do checkout"
    assert funnel_calls[0]["kwargs"]["stage"] == app_module.FUNNEL_STAGE_CHECKOUT_SUBMIT
    assert agendamentos, "esperava agendar alerta de novo cadastro"
    assert agendamentos[0]["delay_minutes"] == app_module.TRX_NEW_SIGNUP_NOTIFY_DELAY_MINUTES


def test_compra_get_redireciona_home(client):
    response = client.get("/comprar", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


def test_compra_gratis_reaproveita_pedido_recente(app_module, client, monkeypatch):
    controle = {"salvou": 0, "email": 0, "agendamento": 0}

    monkeypatch.setattr(app_module, "validar_csrf_token", lambda token: True)
    monkeypatch.setattr(
        app_module,
        "buscar_order_recente_por_cadastro",
        lambda **kwargs: {"order_id": "order-existente-1", "plano": "trx-gratis", "status": "PAGO"},
    )
    monkeypatch.setattr(
        app_module,
        "salvar_order",
        lambda **kwargs: controle.__setitem__("salvou", controle["salvou"] + 1),
    )
    monkeypatch.setattr(
        app_module,
        "enviar_email",
        lambda **kwargs: controle.__setitem__("email", controle["email"] + 1),
    )
    monkeypatch.setattr(
        app_module,
        "agendar_alerta_email_novo_cadastro",
        lambda *args, **kwargs: controle.__setitem__("agendamento", controle["agendamento"] + 1) or True,
    )

    response = client.post(
        "/comprar",
        data={
            "csrf_token": "ok",
            "nome": "Gui Trader",
            "email": "gui@example.com",
            "telefone": "11999999999",
            "plano": "trx-gratis",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].startswith("/sucesso/order-existente-1?t=")
    assert controle["salvou"] == 0
    assert controle["email"] == 0
    assert controle["agendamento"] == 0
