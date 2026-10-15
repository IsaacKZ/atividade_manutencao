import os
import sqlite3

# O banco padrão fica na pasta do projeto, mesmo ao iniciar de outra pasta.
PASTA_PROJETO = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.abspath(
    os.environ.get("SISTEMA_DB_PATH") or os.path.join(PASTA_PROJETO, "sistema.db")
)


def conectar():
    """Abre o banco configurado, sem depender da pasta atual."""
    return sqlite3.connect(DB_PATH)


def inicializar_banco():
    """Cria as tabelas e o login inicial, sem apagar os dados existentes."""
    conexao = conectar()
    try:
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

        cursor = conexao.execute("SELECT COUNT(*) FROM usuarios")
        if cursor.fetchone()[0] == 0:
            conexao.execute(
                "INSERT INTO usuarios (username, senha) VALUES (?, ?)",
                ("admin", "admin123"),
            )
        conexao.commit()
    finally:
        conexao.close()
