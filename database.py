from contextlib import closing
import os
import sqlite3

PASTA_PROJETO = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.abspath(
    os.environ.get("SISTEMA_DB_PATH") or os.path.join(PASTA_PROJETO, "sistema.db")
)


def conectar():
    """Abre o banco de dados."""
    return sqlite3.connect(DB_PATH)


def consultar(sql, parametros=()):
    """Consulta o banco de dados."""
    with closing(conectar()) as conexao:
        return conexao.execute(sql, parametros).fetchall()


def executar(sql, parametros=()):
    """Executa uma alteração no banco."""
    with closing(conectar()) as conexao:
        resultado = conexao.execute(sql, parametros)
        conexao.commit()
        return resultado.rowcount


def inicializar_banco():
    """Cria as tabelas e o usuário inicial."""
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

        conexao.execute("""
            INSERT INTO usuarios (username, senha)
            SELECT ?, ?
            WHERE NOT EXISTS (SELECT 1 FROM usuarios)
        """, ("admin", "admin123"))
        conexao.commit()
