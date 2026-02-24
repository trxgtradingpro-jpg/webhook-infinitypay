def test_api_funnel_track_cta_publico(app_module, client, monkeypatch):
    calls = []
    monkeypatch.setattr(app_module, "_origem_confiavel_request", lambda: True)
    monkeypatch.setattr(
        app_module,
        "registrar_evento_funil",
        lambda *args, **kwargs: calls.append({"args": args, "kwargs": kwargs}) or True
    )

    response = client.post(
        "/api/funnel/track",
        json={
            "event_name": "cta_click",
            "cta_id": "hero_ativar",
            "destination": "/checkout/trx-gold",
            "source": "index"
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ok"] is True
    assert payload["tracked"] is True
    assert calls
    assert calls[0]["kwargs"]["stage"] == app_module.FUNNEL_STAGE_CTA_CLICK


def test_api_analytics_funnel_summary_admin(app_module, client, monkeypatch):
    with client.session_transaction() as sess:
        sess["admin"] = True

    monkeypatch.setattr(
        app_module,
        "carregar_eventos_funil_analytics_filtrados",
        lambda **kwargs: [
            {"stage": "visit", "visitor_key": "v1", "created_at": None},
            {"stage": "visit", "visitor_key": "v2", "created_at": None},
            {"stage": "cta_click", "visitor_key": "v1", "created_at": None, "meta": {"cta_id": "hero_ativar"}},
            {"stage": "checkout_submit", "user_key": "u1@example.com", "created_at": None},
            {"stage": "payment_confirmed", "user_key": "u1@example.com", "plano": "trx-gold", "created_at": None},
            {"stage": "activation", "user_key": "u1@example.com", "created_at": None},
            {"stage": "retention", "user_key": "u1@example.com", "created_at": None},
        ]
    )

    response = client.get("/api/analytics/funnel-summary?start=2026-01-01&end=2026-01-31")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["stage_counts"]["visit"] == 2
    assert payload["stage_counts"]["cta_click"] == 1
    assert payload["stage_counts"]["checkout_submit"] == 1
    assert payload["stage_counts"]["payment_confirmed"] == 1
    assert payload["stage_counts"]["activation"] == 1
    assert payload["stage_counts"]["retention"] == 1

    conversion_visit_cta = next(item for item in payload["conversions"] if item["from"] == "visit" and item["to"] == "cta_click")
    assert conversion_visit_cta["rate_percent"] == 50.0


def test_api_analytics_page_track_publico(app_module, client, monkeypatch):
    calls = []
    monkeypatch.setattr(app_module, "_origem_confiavel_request", lambda: True)
    monkeypatch.setattr(
        app_module,
        "obter_contexto_funil",
        lambda: {
            "visitor_key": "v_test",
            "session_key": "s_test",
            "source_path": "/",
            "referrer": "https://example.com",
            "utm_source": "",
            "utm_medium": "",
            "utm_campaign": "",
            "utm_content": "",
            "utm_term": "",
        },
    )
    monkeypatch.setattr(app_module, "obter_email_cliente_logado", lambda: "")
    monkeypatch.setattr(
        app_module,
        "registrar_evento_engajamento_pagina_analytics",
        lambda **kwargs: calls.append(kwargs) or True,
    )

    response = client.post(
        "/api/analytics/page-track",
        json={
            "visit_id": "pv_test_1",
            "path": "/",
            "duration_ms": 35100,
            "active_ms": 28800,
            "read_ms": 19900,
            "max_scroll_percent": 67,
            "is_exit": True,
            "exit_type": "close",
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ok"] is True
    assert payload["tracked"] is True
    assert calls
    call = calls[0]
    assert call["visit_id"] == "pv_test_1"
    assert call["path"] == "/"
    assert call["duration_seconds"] == 35
    assert call["active_seconds"] == 29
    assert call["read_seconds"] == 20
    assert call["max_scroll_percent"] == 67
    assert call["is_index"] is True
    assert call["is_exit"] is True
    assert call["exit_type"] == "close"


def test_montar_analise_engajamento_paginas(app_module):
    eventos = [
        {
            "visit_id": "v1",
            "visitor_key": "v_user_1",
            "session_key": "s1",
            "user_key": "",
            "path": "/",
            "duration_seconds": 90,
            "active_seconds": 70,
            "read_seconds": 55,
            "max_scroll_percent": 82,
            "is_index": True,
            "exit_recorded": False,
            "exit_type": "internal",
        },
        {
            "visit_id": "v2",
            "visitor_key": "v_user_1",
            "session_key": "s1",
            "user_key": "",
            "path": "/checkout/trx-gold",
            "duration_seconds": 40,
            "active_seconds": 30,
            "read_seconds": 0,
            "max_scroll_percent": 48,
            "is_index": False,
            "exit_recorded": True,
            "exit_type": "close",
        },
        {
            "visit_id": "v3",
            "visitor_key": "v_user_2",
            "session_key": "s2",
            "user_key": "",
            "path": "/checkout/trx-gold",
            "duration_seconds": 20,
            "active_seconds": 12,
            "read_seconds": 0,
            "max_scroll_percent": 30,
            "is_index": False,
            "exit_recorded": False,
            "exit_type": "internal",
        },
    ]

    resumo = app_module.montar_analise_engajamento_paginas(eventos)

    assert resumo["total_visits"] == 3
    assert resumo["tracked_pages"] == 2
    assert resumo["total_exits"] == 1
    assert resumo["avg_pages_per_session"] == 1.5

    assert resumo["index"]["visits"] == 1
    assert resumo["index"]["avg_time_seconds"] == 90
    assert resumo["index"]["avg_read_seconds"] == 55

    checkout = next(item for item in resumo["pages"] if item["path"] == "/checkout/trx-gold")
    assert checkout["visits"] == 2
    assert checkout["avg_duration_seconds"] == 30
    assert checkout["exit_count"] == 1
    assert checkout["exit_rate_percent"] == 50.0

    assert resumo["top_exit_pages"][0]["path"] == "/checkout/trx-gold"


def test_api_analytics_summary_inclui_engagement(app_module, client, monkeypatch):
    with client.session_transaction() as sess:
        sess["admin"] = True

    monkeypatch.setattr(
        app_module,
        "montar_relatorio_analytics_completo",
        lambda **kwargs: {
            "totals": {},
            "totals_by_plan": {},
            "daily_revenue": [],
            "daily_orders": [],
            "daily_paid_orders": [],
            "daily_free_orders": [],
            "daily_by_plan": {},
            "period": {},
            "plan_stats": [],
            "funnel": {},
            "channels": {},
            "upgrades": {},
            "engagement": {"total_visits": 42},
            "onboarding": {},
            "retention_cohorts": [],
            "suggestions": [],
        },
    )

    response = client.get("/api/analytics/summary?start=2026-01-01&end=2026-01-31")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["engagement"]["total_visits"] == 42
