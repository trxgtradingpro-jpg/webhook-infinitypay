from datetime import datetime, timezone


def test_montar_expiracao_pedido_usa_data_txt_mais_recente(app_module, monkeypatch, tmp_path):
    (tmp_path / "27-03-2026.txt").write_text("", encoding="utf-8")
    (tmp_path / "15-04-2026.txt").write_text("", encoding="utf-8")
    monkeypatch.setattr(app_module, "PLANOS_PASTA_ARQUIVOS", str(tmp_path))

    order = {
        "plano": "trx-gold",
        "created_at": datetime(2026, 2, 20, 12, 0, tzinfo=timezone.utc),
    }
    exp = app_module.montar_expiracao_pedido(order)

    assert exp is not None
    assert exp["expira_em"].year == 2026
    assert exp["expira_em"].month == 4
    assert exp["expira_em"].day == 15
    assert exp["expira_em"].hour == 23
    assert exp["expira_em"].minute == 59
    assert exp["expira_em"].second == 59


def test_montar_expiracao_pedido_fallback_sem_txt(app_module, monkeypatch):
    monkeypatch.setattr(app_module, "PLANOS_PASTA_ARQUIVOS", "nao-existe")
    order = {
        "plano": "trx-gold",
        "created_at": datetime(2026, 1, 1, 10, 0, 0),
    }
    exp = app_module.montar_expiracao_pedido(order)

    assert exp is not None
    assert exp["expira_em"] == datetime(2026, 1, 31, 10, 0, 0)


def test_resolver_origem_arquivo_plano_prioriza_psf(app_module, monkeypatch, tmp_path):
    arquivo = tmp_path / "TRX GOLD.psf"
    arquivo.write_text("conteudo", encoding="utf-8")
    monkeypatch.setattr(app_module, "PLANOS_PASTA_ARQUIVOS", str(tmp_path))

    origem = app_module.resolver_origem_arquivo_plano("trx-gold")
    assert origem == str(arquivo)


def test_resolver_origem_arquivo_plano_black_aceita_brack(app_module, monkeypatch, tmp_path):
    arquivo = tmp_path / "TRX BRACK.psf"
    arquivo.write_text("conteudo", encoding="utf-8")
    monkeypatch.setattr(app_module, "PLANOS_PASTA_ARQUIVOS", str(tmp_path))

    origem = app_module.resolver_origem_arquivo_plano("trx-black")
    assert origem == str(arquivo)
