from database import consultar


def login(username, senha):
    """Confere usuário e senha."""
    usuarios = consultar(
        "SELECT id FROM usuarios WHERE username = ? AND senha = ?",
        (username, senha),
    )
    return bool(usuarios)
