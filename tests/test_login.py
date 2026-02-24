from werkzeug.security import generate_password_hash


def test_cliente_login_sucesso(app_module, client, monkeypatch):
    senha = "SenhaForte@123"
    email = "cliente@example.com"
    conta = {
        "email": email,
        "password_hash": generate_password_hash(senha),
        "first_access_required": False,
    }

    monkeypatch.setattr(app_module, "validar_csrf_token", lambda token: True)
    monkeypatch.setattr(app_module, "buscar_conta_cliente_por_email", lambda e: conta if e == email else None)
    monkeypatch.setattr(app_module, "conta_cliente_requer_configuracao_senha", lambda c: False)
    monkeypatch.setattr(app_module, "atualizar_ultimo_login_conta_cliente", lambda e: True)
    monkeypatch.setattr(app_module, "limpar_remember_token_cliente", lambda e: True)

    response = client.post(
        "/login",
        data={
            "csrf_token": "ok",
            "email": email,
            "senha": senha,
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/minha-conta")


def test_cliente_login_csrf_invalido(app_module, client, monkeypatch):
    monkeypatch.setattr(app_module, "validar_csrf_token", lambda token: False)
    response = client.post(
        "/login",
        data={"csrf_token": "bad", "email": "x@y.com", "senha": "123"},
        follow_redirects=False,
    )
    assert response.status_code == 403


def test_cliente_login_sucesso_por_telefone(app_module, client, monkeypatch):
    senha = "SenhaForte@123"
    email = "cliente@example.com"
    conta = {
        "email": email,
        "password_hash": generate_password_hash(senha),
        "first_access_required": False,
    }

    monkeypatch.setattr(app_module, "validar_csrf_token", lambda token: True)
    monkeypatch.setattr(
        app_module,
        "buscar_ultimo_pedido_pago_por_telefone",
        lambda telefone: {"email": email} if telefone == "11999999999" else None,
    )
    monkeypatch.setattr(app_module, "buscar_conta_cliente_por_email", lambda e: conta if e == email else None)
    monkeypatch.setattr(app_module, "conta_cliente_requer_configuracao_senha", lambda c: False)
    monkeypatch.setattr(app_module, "atualizar_ultimo_login_conta_cliente", lambda e: True)
    monkeypatch.setattr(app_module, "limpar_remember_token_cliente", lambda e: True)

    response = client.post(
        "/login",
        data={
            "csrf_token": "ok",
            "login_id": "(11) 99999-9999",
            "senha": senha,
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/minha-conta")


def test_cliente_login_primeiro_acesso_com_senha_temporaria(app_module, client, monkeypatch):
    senha_temporaria = "Temp@Senha123"
    email = "cliente@example.com"
    conta = {
        "email": email,
        "password_hash": generate_password_hash(senha_temporaria),
        "first_access_required": True,
    }

    monkeypatch.setattr(app_module, "validar_csrf_token", lambda token: True)
    monkeypatch.setattr(app_module, "buscar_conta_cliente_por_email", lambda e: conta if e == email else None)
    monkeypatch.setattr(app_module, "conta_cliente_requer_configuracao_senha", lambda c: True)
    monkeypatch.setattr(app_module, "limpar_codigo_cliente", lambda e: True)

    response = client.post(
        "/login",
        data={
            "csrf_token": "ok",
            "login_id": email,
            "senha": senha_temporaria,
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login/primeiro-acesso")

    with client.session_transaction() as sess:
        assert sess[app_module.CLIENT_PENDING_EMAIL_KEY] == email


def test_cliente_login_primeiro_acesso_senha_temporaria_invalida(app_module, client, monkeypatch):
    senha_temporaria = "Temp@Senha123"
    email = "cliente@example.com"
    conta = {
        "email": email,
        "password_hash": generate_password_hash(senha_temporaria),
        "first_access_required": True,
    }

    monkeypatch.setattr(app_module, "validar_csrf_token", lambda token: True)
    monkeypatch.setattr(app_module, "buscar_conta_cliente_por_email", lambda e: conta if e == email else None)
    monkeypatch.setattr(app_module, "conta_cliente_requer_configuracao_senha", lambda c: True)

    response = client.post(
        "/login",
        data={
            "csrf_token": "ok",
            "login_id": email,
            "senha": "errada@123",
        },
        follow_redirects=False,
    )

    assert response.status_code == 200
    assert b"E-mail ou senha invalidos." in response.data


def test_cliente_confirmar_codigo_redireciona_para_login_senha_temporaria(client):
    response = client.get(
        "/login/confirmar-codigo?email=cliente@example.com",
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/login?info=use_senha_temporaria&login_id=cliente%40example.com"

