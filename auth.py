from database import consultar


def login(username, senha):
    """Confere usuário e senha diretamente, sem alterar o banco."""
    usuarios = consultar(
        "SELECT id FROM usuarios WHERE username = ? AND senha = ?",
        (username, senha),
    )
    return len(usuarios) > 0
