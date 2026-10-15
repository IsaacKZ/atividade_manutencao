from database import conectar


def login(username, senha):
    """Confere usuário e senha diretamente, sem alterar o banco."""
    conexao = conectar()
    try:
        cursor = conexao.cursor()
        cursor.execute(
            "SELECT id FROM usuarios WHERE username = ? AND senha = ?",
            (username, senha),
        )
        usuario = cursor.fetchone()
        return usuario is not None
    finally:
        conexao.close()
