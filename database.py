from contextlib import closing
import sqlite3

DB_PATH = "sistema.db"


def conectar():
    return sqlite3.connect(DB_PATH)


def inicializar_banco():
    with closing(conectar()) as conexao:
        conexao.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                senha TEXT NOT NULL
            )
        """)

        conexao.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT,
                cpf TEXT,
                email TEXT,
                telefone TEXT
            )
        """)

        quantidade_usuarios = conexao.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
        if quantidade_usuarios == 0:
            conexao.execute(
                "INSERT INTO usuarios (username, senha) VALUES (?, ?)",
                ("admin", "admin123"),
            )

        conexao.commit()
