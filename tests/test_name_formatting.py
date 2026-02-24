def test_normalizar_nome_title_case_com_particulas(app_module):
    nome = app_module.normalizar_nome("gUILHERME gOMES da sILVA")
    assert nome == "Guilherme Gomes da Silva"


def test_normalizar_nome_remove_espacos_extras(app_module):
    nome = app_module.normalizar_nome("  joao   dA   coSta  e  sOuZa ")
    assert nome == "Joao da Costa e Souza"


def test_normalizar_nome_preserva_hifen_e_romano(app_module):
    nome = app_module.normalizar_nome("maria-das dores paulo ii")
    assert nome == "Maria-Das Dores Paulo II"
