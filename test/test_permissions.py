from app.utils.auth import check_perm

def test_check_perm_false_when_missing(monkeypatch):
    # Simula DF vazio: a função retorna False
    assert check_perm("naoexiste", "can_news") is False
