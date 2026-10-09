from contextlib import closing

from database import conectar


def login(username, senha):
    with closing(conectar()) as conexao:
        usuario = conexao.execute(
            "SELECT id FROM usuarios WHERE username = ? AND senha = ?",
            (username, senha),
        ).fetchone()
        return usuario is not None
