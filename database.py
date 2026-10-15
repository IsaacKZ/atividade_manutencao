from contextlib import closing
import os
from pathlib import Path
import sqlite3

# O mesmo arquivo é usado mesmo ao iniciar o programa em outra pasta.
DB_PATH = str(
    Path(os.environ.get("SISTEMA_DB_PATH") or Path(__file__).with_name("sistema.db"))
    .resolve()
)


def conectar():
    """Abre o banco configurado, sem depender da pasta atual."""
    return sqlite3.connect(DB_PATH)


def inicializar_banco():
    """Cria as tabelas sem apagar dados ou cadastrar uma senha padrão."""
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

        conexao.commit()
