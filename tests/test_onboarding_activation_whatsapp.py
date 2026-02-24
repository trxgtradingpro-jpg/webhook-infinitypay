from datetime import datetime
from urllib.parse import parse_qs, urlparse


def _texto_link(url):
    parsed = urlparse(url)
    return parse_qs(parsed.query).get("text", [""])[0]


def test_mensagem_ativacao_nao_iniciado(app_module, monkeypatch):
    monkeypatch.setattr(app_module, "saudacao_whatsapp_periodo", lambda: "Bom dia")
    payload = {
        "nome": "Guilherme",
        "plano": "trx-gold",
        "done_count": 0,
        "total_steps": 5,
        "steps": [
            {"key": "email_accessed", "label": "Consegui acessar o e-mail enviado", "checked": False},
            {"key": "tool_downloaded", "label": "Ja baixei a ferramenta", "checked": False},
            {"key": "zip_extracted", "label": "Ja descompactei com a senha", "checked": False},
            {"key": "tool_installed", "label": "Ja instalei a ferramenta", "checked": False},
            {"key": "robot_activated", "label": "Ja consegui ativar o robo", "checked": False},
        ],
    }

    msg = app_module.montar_mensagem_whatsapp_ativacao(payload)
    assert msg.startswith("Bom dia, Guilherme!")
    assert "Vamos comecar pela etapa 1/5" in msg
    assert "Abra seu e-mail e procure" in msg
    assert "https://www.youtube.com/watch?v=u3GWhwR8bcQ&t=111s" in msg


def test_mensagem_ativacao_etapa_em_progresso(app_module, monkeypatch):
    monkeypatch.setattr(app_module, "saudacao_whatsapp_periodo", lambda: "Boa tarde")
    payload = {
        "nome": "Guilherme",
        "plano": "trx-gold",
        "done_count": 1,
        "total_steps": 5,
        "steps": [
            {"key": "email_accessed", "label": "Consegui acessar o e-mail enviado", "checked": True},
            {"key": "tool_downloaded", "label": "Ja baixei a ferramenta", "checked": False},
            {"key": "zip_extracted", "label": "Ja descompactei com a senha", "checked": False},
            {"key": "tool_installed", "label": "Ja instalei a ferramenta", "checked": False},
            {"key": "robot_activated", "label": "Ja consegui ativar o robo", "checked": False},
        ],
    }

    msg = app_module.montar_mensagem_whatsapp_ativacao(payload)
    assert msg.startswith("Boa tarde, Guilherme!")
    assert "etapa 2/5" in msg
    assert "Ja baixei a ferramenta" in msg
    assert "Este ponto mostra onde clicar para fazer o download correto" in msg
    assert "https://www.youtube.com/watch?v=u3GWhwR8bcQ&t=150s" in msg
    assert "https://example.com/login" in msg


def test_mensagem_ativacao_concluido(app_module, monkeypatch):
    monkeypatch.setattr(app_module, "saudacao_whatsapp_periodo", lambda: "Boa noite")
    payload = {
        "nome": "Guilherme",
        "plano": "trx-gold",
        "done_count": 5,
        "total_steps": 5,
        "steps": [
            {"key": "email_accessed", "label": "Consegui acessar o e-mail enviado", "checked": True},
            {"key": "tool_downloaded", "label": "Ja baixei a ferramenta", "checked": True},
            {"key": "zip_extracted", "label": "Ja descompactei com a senha", "checked": True},
            {"key": "tool_installed", "label": "Ja instalei a ferramenta", "checked": True},
            {"key": "robot_activated", "label": "Ja consegui ativar o robo", "checked": True},
        ],
    }

    msg = app_module.montar_mensagem_whatsapp_ativacao(payload)
    assert msg.startswith("Boa noite, Guilherme!")
    assert "TRX GOLD" in msg
    assert "conclu" in msg.lower()


def test_link_whatsapp_ativacao_payload(app_module, monkeypatch):
    monkeypatch.setattr(app_module, "saudacao_whatsapp_periodo", lambda: "Bom dia")
    payload = {
        "nome": "Guilherme",
        "telefone": "11999998888",
        "plano": "trx-gold",
        "done_count": 1,
        "total_steps": 5,
        "steps": [
            {"key": "email_accessed", "label": "Consegui acessar o e-mail enviado", "checked": True},
            {"key": "tool_downloaded", "label": "Ja baixei a ferramenta", "checked": False},
        ],
    }

    link = app_module.gerar_link_whatsapp_ativacao(payload)
    assert link is not None
    assert link.startswith("https://wa.me/5511999998888?text=")
    texto = _texto_link(link)
    assert "etapa 2/5" in texto
    assert "https://www.youtube.com/watch?v=u3GWhwR8bcQ&t=150s" in texto


def test_mensagem_ativacao_tem_video_no_tempo_certo_em_cada_etapa(app_module, monkeypatch):
    monkeypatch.setattr(app_module, "saudacao_whatsapp_periodo", lambda: "Bom dia")

    steps_base = [
        {"key": "email_accessed", "label": "Consegui acessar o e-mail enviado", "checked": False},
        {"key": "tool_downloaded", "label": "Ja baixei a ferramenta", "checked": False},
        {"key": "zip_extracted", "label": "Ja descompactei com a senha", "checked": False},
        {"key": "tool_installed", "label": "Ja instalei a ferramenta", "checked": False},
        {"key": "robot_activated", "label": "Ja consegui ativar o robo", "checked": False},
    ]
    cenarios = [
        (0, "https://www.youtube.com/watch?v=u3GWhwR8bcQ&t=111s"),
        (1, "https://www.youtube.com/watch?v=u3GWhwR8bcQ&t=150s"),
        (2, "https://www.youtube.com/watch?v=u3GWhwR8bcQ&t=155s"),
        (3, "https://www.youtube.com/watch?v=u3GWhwR8bcQ&t=238s"),
        (4, "https://www.youtube.com/watch?v=u3GWhwR8bcQ&t=283s"),
    ]

    for done_count, expected_video in cenarios:
        steps = []
        for idx, item in enumerate(steps_base):
            steps.append({**item, "checked": idx < done_count})
        payload = {
            "nome": "Guilherme",
            "plano": "trx-gold",
            "done_count": done_count,
            "total_steps": 5,
            "steps": steps,
        }

        msg = app_module.montar_mensagem_whatsapp_ativacao(payload)
        assert expected_video in msg


def test_resumo_onboarding_oculta_icone_quando_ja_enviado_na_mesma_etapa(app_module, monkeypatch):
    monkeypatch.setattr(app_module, "gerar_link_whatsapp_ativacao", lambda payload: "https://wa.me/5511999998888?text=ok")
    monkeypatch.setattr(app_module, "montar_mensagem_whatsapp_ativacao", lambda payload: "mensagem de teste")

    linha = {
        "email": "cliente@example.com",
        "account_name": "Cliente Teste",
        "account_phone": "11999998888",
        "email_accessed": True,
        "tool_downloaded": False,
        "zip_extracted": False,
        "tool_installed": False,
        "robot_activated": False,
        "activation_whatsapp_last_stage": "tool_downloaded",
        "activation_whatsapp_last_sent_at": datetime(2026, 2, 24, 12, 0, 0),
        "last_order_name": "Cliente Teste",
        "last_order_phone": "11999998888",
        "last_order_plan": "trx-gratis",
        "last_order_status": "PAGO",
        "paid_orders": 1,
        "total_orders": 1,
    }

    with app_module.app.test_request_context("/admin/dashboard"):
        resumo = app_module.montar_resumo_onboarding_admin([linha])

    item = resumo["items"][0]
    assert item["activation_whatsapp_sent_current_stage"] is True
    assert item["activation_whatsapp_route"] is None


def test_resumo_onboarding_mostra_icone_quando_ainda_nao_enviado(app_module, monkeypatch):
    monkeypatch.setattr(app_module, "gerar_link_whatsapp_ativacao", lambda payload: "https://wa.me/5511999998888?text=ok")
    monkeypatch.setattr(app_module, "montar_mensagem_whatsapp_ativacao", lambda payload: "mensagem de teste")

    linha = {
        "email": "cliente@example.com",
        "account_name": "Cliente Teste",
        "account_phone": "11999998888",
        "email_accessed": True,
        "tool_downloaded": False,
        "zip_extracted": False,
        "tool_installed": False,
        "robot_activated": False,
        "activation_whatsapp_last_stage": "not_started",
        "activation_whatsapp_last_sent_at": datetime(2026, 2, 24, 12, 0, 0),
        "last_order_name": "Cliente Teste",
        "last_order_phone": "11999998888",
        "last_order_plan": "trx-gratis",
        "last_order_status": "PAGO",
        "paid_orders": 1,
        "total_orders": 1,
    }

    with app_module.app.test_request_context("/admin/dashboard"):
        resumo = app_module.montar_resumo_onboarding_admin([linha])

    item = resumo["items"][0]
    assert item["activation_whatsapp_sent_current_stage"] is False
    assert item["activation_whatsapp_route"] is not None
    assert "/admin/onboarding/whatsapp" in item["activation_whatsapp_route"]
    assert "stage=tool_downloaded" in item["activation_whatsapp_route"]


def test_resumo_onboarding_mostra_icone_marcar_concluido(app_module, monkeypatch):
    monkeypatch.setattr(app_module, "gerar_link_whatsapp_ativacao", lambda payload: "https://wa.me/5511999998888?text=ok")
    monkeypatch.setattr(app_module, "montar_mensagem_whatsapp_ativacao", lambda payload: "mensagem de teste")

    linha = {
        "email": "cliente@example.com",
        "account_name": "Cliente Teste",
        "account_phone": "11999998888",
        "email_accessed": True,
        "tool_downloaded": False,
        "zip_extracted": False,
        "tool_installed": False,
        "robot_activated": False,
        "activation_whatsapp_last_stage": "not_started",
        "activation_whatsapp_last_sent_at": datetime(2026, 2, 24, 12, 0, 0),
        "last_order_name": "Cliente Teste",
        "last_order_phone": "11999998888",
        "last_order_plan": "trx-gratis",
        "last_order_status": "PAGO",
        "paid_orders": 1,
        "total_orders": 1,
    }

    with app_module.app.test_request_context("/admin/dashboard"):
        resumo = app_module.montar_resumo_onboarding_admin([linha])

    item = resumo["items"][0]
    assert item["status"] == "Em progresso"
    assert item["activation_mark_done_route"] is not None
    assert "/admin/onboarding/concluir" in item["activation_mark_done_route"]


def test_resumo_onboarding_oculta_icone_marcar_concluido_quando_finalizado(app_module, monkeypatch):
    monkeypatch.setattr(app_module, "gerar_link_whatsapp_ativacao", lambda payload: "https://wa.me/5511999998888?text=ok")
    monkeypatch.setattr(app_module, "montar_mensagem_whatsapp_ativacao", lambda payload: "mensagem de teste")

    linha = {
        "email": "cliente@example.com",
        "account_name": "Cliente Teste",
        "account_phone": "11999998888",
        "email_accessed": True,
        "tool_downloaded": True,
        "zip_extracted": True,
        "tool_installed": True,
        "robot_activated": True,
        "activation_whatsapp_last_stage": "concluded",
        "activation_whatsapp_last_sent_at": datetime(2026, 2, 24, 12, 0, 0),
        "last_order_name": "Cliente Teste",
        "last_order_phone": "11999998888",
        "last_order_plan": "trx-gratis",
        "last_order_status": "PAGO",
        "paid_orders": 1,
        "total_orders": 1,
    }

    with app_module.app.test_request_context("/admin/dashboard"):
        resumo = app_module.montar_resumo_onboarding_admin([linha])

    item = resumo["items"][0]
    assert item["status"] == "Concluido"
    assert item["activation_mark_done_route"] is None


def test_admin_onboarding_whatsapp_registra_e_redireciona(app_module, client, monkeypatch):
    payload = {
        "email": "cliente@example.com",
        "nome": "Cliente",
        "telefone": "11999998888",
        "plano": "trx-gratis",
        "done_count": 0,
        "total_steps": 5,
        "steps": [{"key": "email_accessed", "label": "Consegui acessar o e-mail enviado", "checked": False}],
        "activation_whatsapp_last_stage": "",
        "activation_whatsapp_last_sent_at": None,
        "activation_whatsapp_send_count": 0,
    }

    call = {}
    monkeypatch.setattr(app_module, "validar_csrf_token", lambda token: token == "ok")
    monkeypatch.setattr(
        app_module,
        "montar_payload_whatsapp_ativacao_por_email",
        lambda email: dict(payload) if email == "cliente@example.com" else None,
    )
    monkeypatch.setattr(app_module, "montar_stage_token_onboarding", lambda _payload: "not_started")
    monkeypatch.setattr(app_module, "gerar_link_whatsapp_ativacao", lambda _payload: "https://wa.me/5511999998888?text=ok")
    monkeypatch.setattr(
        app_module,
        "registrar_envio_whatsapp_ativacao",
        lambda email, stage: call.update({"email": email, "stage": stage}) or True,
    )

    with client.session_transaction() as sess:
        sess["admin"] = True
        sess["_csrf_token"] = "ok"

    response = client.get(
        "/admin/onboarding/whatsapp?email=cliente@example.com&stage=not_started&csrf_token=ok",
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "https://wa.me/5511999998888?text=ok"
    assert call == {"email": "cliente@example.com", "stage": "not_started"}


def test_admin_onboarding_concluir_marca_todas_as_etapas(app_module, client, monkeypatch):
    call = {}

    monkeypatch.setattr(app_module, "validar_csrf_token", lambda token: token == "ok")

    def _salvar(email, payload):
        call["email"] = email
        call["payload"] = dict(payload)
        return dict(payload)

    monkeypatch.setattr(app_module, "salvar_onboarding_progresso_cliente", _salvar)

    with client.session_transaction() as sess:
        sess["admin"] = True
        sess["_csrf_token"] = "ok"

    response = client.get(
        "/admin/onboarding/concluir?email=cliente@example.com&csrf_token=ok",
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "/admin/dashboard?ok=1" in response.headers["Location"]
    assert call["email"] == "cliente@example.com"

    expected_steps = {step for step, _ in app_module.ONBOARDING_PROGRESS_STEPS}
    assert set(call["payload"].keys()) == expected_steps
    assert all(call["payload"][step] is True for step in expected_steps)
