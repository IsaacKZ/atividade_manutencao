"""Acesso ao SQLite e criação das tabelas, sem dependências externas."""

from contextlib import closing
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


def consultar(sql, parametros=()):
    """Executa uma consulta e devolve uma lista de linhas."""
    with closing(conectar()) as conexao:
        return conexao.execute(sql, parametros).fetchall()


def executar(sql, parametros=()):
    """Grava uma alteração e devolve a quantidade de linhas afetadas."""
    with closing(conectar()) as conexao:
        resultado = conexao.execute(sql, parametros)
        conexao.commit()
        return resultado.rowcount


def inicializar_banco():
    """Cria as tabelas e o login inicial, sem apagar os dados existentes."""
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

        # Conferir e inserir no mesmo comando evita a disputa entre inicializações.
        conexao.execute("""
            INSERT INTO usuarios (username, senha)
            SELECT ?, ?
            WHERE NOT EXISTS (SELECT 1 FROM usuarios)
        """, ("admin", "admin123"))
        conexao.commit()
