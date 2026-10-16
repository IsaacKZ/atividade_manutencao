from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import os
from pathlib import Path
import subprocess
import sqlite3
import sys
import tempfile
from threading import Barrier
import unittest
from unittest.mock import patch

import database


class BancoTest(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.addCleanup(self.pasta.cleanup)
        self.caminho = Path(self.pasta.name) / "teste.db"
        ajuste = patch.object(database, "DB_PATH", str(self.caminho))
        ajuste.start()
        self.addCleanup(ajuste.stop)

    def test_inicializacao_cria_login_padrao_em_banco_novo(self):
        database.inicializar_banco()
        with closing(database.conectar()) as conexao:
            usuarios = conexao.execute("SELECT username, senha FROM usuarios").fetchall()
            clientes = conexao.execute("SELECT * FROM clientes").fetchall()
        self.assertEqual(usuarios, [("admin", "admin123")])
        self.assertEqual(clientes, [])

    def test_inicializacao_repetida_preserva_usuarios_e_clientes(self):
        database.inicializar_banco()
        with closing(database.conectar()) as conexao:
            conexao.execute(
                "INSERT INTO usuarios (username, senha) VALUES (?, ?)",
                ("existente", "senha antiga"),
            )
            conexao.execute(
                "INSERT INTO clientes (nome, cpf, email, telefone) VALUES (?, ?, ?, ?)",
                ("Ana", "12345678901", "ana@example.com", "11999999999"),
            )
            conexao.commit()
            usuarios_antes = conexao.execute("SELECT * FROM usuarios").fetchall()
            clientes_antes = conexao.execute("SELECT * FROM clientes").fetchall()

        database.inicializar_banco()
        database.inicializar_banco()

        with closing(database.conectar()) as conexao:
            self.assertEqual(
                conexao.execute("SELECT * FROM usuarios").fetchall(), usuarios_antes
            )
            self.assertEqual(
                conexao.execute("SELECT * FROM clientes").fetchall(), clientes_antes
            )

    def test_inicializacao_preserva_usuario_existente_sem_criar_admin(self):
        database.inicializar_banco()
        database.executar("DELETE FROM usuarios")
        database.executar(
            "INSERT INTO usuarios (username, senha) VALUES (?, ?)", ("operador", "senha existente")
        )
        usuarios = database.consultar("SELECT * FROM usuarios")
        database.inicializar_banco()
        database.inicializar_banco()
        self.assertEqual(database.consultar("SELECT * FROM usuarios"), usuarios)

    def test_inicializacoes_concorrentes_nao_duplicam_conta_padrao(self):
        database.inicializar_banco()
        database.executar("DELETE FROM usuarios")
        barreira = Barrier(2)
        chegadas = []
        erros_sincronizacao = []

        def sincronizar_insercao(sql):
            # Pausa antes da gravação para expor a disputa entre as duas conexões.
            if sql.lstrip().upper().startswith("INSERT INTO USUARIOS"):
                chegadas.append(True)
                try:
                    barreira.wait(timeout=3)
                except Exception as erro:
                    erros_sincronizacao.append(erro)

        def conectar_sincronizado():
            conexao = sqlite3.connect(self.caminho)
            conexao.set_trace_callback(sincronizar_insercao)
            return conexao

        with patch.object(database, "conectar", conectar_sincronizado):
            with ThreadPoolExecutor(max_workers=2) as executores:
                tarefas = [executores.submit(database.inicializar_banco) for _ in range(2)]
                erros = [tarefa.exception(timeout=10) for tarefa in tarefas]
        self.assertEqual(len(chegadas), 2)
        self.assertEqual(erros_sincronizacao, [])
        self.assertEqual(erros, [None, None])
        self.assertEqual(database.consultar("SELECT username, senha FROM usuarios"),
                         [("admin", "admin123")])

    def test_primeira_inicializacao_concorrente_em_banco_novo(self):
        self.assertFalse(self.caminho.exists())
        barreira = Barrier(8)

        def iniciar_junto():
            barreira.wait(timeout=5)
            database.inicializar_banco()

        with ThreadPoolExecutor(max_workers=8) as executores:
            tarefas = [executores.submit(iniciar_junto) for _ in range(8)]
            erros = [tarefa.exception(timeout=10) for tarefa in tarefas]
        self.assertEqual(erros, [None] * 8)
        self.assertEqual(database.consultar("SELECT username, senha FROM usuarios"),
                         [("admin", "admin123")])
        self.assertEqual(database.consultar("SELECT * FROM clientes"), [])

    def executar_em_outra_pasta(self, codigo, caminho_override=None):
        ambiente = dict(os.environ)
        ambiente.pop("SISTEMA_DB_PATH", None)
        ambiente["PYTHONPATH"] = str(Path(database.__file__).resolve().parent)
        ambiente["PYTHONDONTWRITEBYTECODE"] = "1"
        if caminho_override is not None:
            ambiente["SISTEMA_DB_PATH"] = caminho_override
        resultado = subprocess.run(
            [sys.executable, "-B", "-c", codigo],
            cwd=self.pasta.name,
            env=ambiente,
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        return resultado.stdout.strip()

    def test_caminho_padrao_independe_da_pasta_atual(self):
        resultado = self.executar_em_outra_pasta("import database; print(database.DB_PATH)")
        esperado = Path(database.__file__).resolve().with_name("sistema.db")
        self.assertEqual(Path(resultado), esperado)
        self.assertFalse(self.caminho.exists())

    def test_override_absoluto_cria_banco_temporario(self):
        resultado = self.executar_em_outra_pasta(
            "import database; database.inicializar_banco(); print(database.DB_PATH)",
            str(self.caminho),
        )
        self.assertEqual(Path(resultado), self.caminho)
        self.assertTrue(self.caminho.exists())

    def test_override_relativo_e_resolvido_antes_de_mudar_de_pasta(self):
        outra_pasta = Path(self.pasta.name) / "outra"
        outra_pasta.mkdir()
        codigo = (
            "import database, os; "
            "os.chdir('outra'); "
            "database.inicializar_banco(); "
            "print(database.DB_PATH)"
        )
        resultado = self.executar_em_outra_pasta(codigo, "teste.db")
        self.assertEqual(Path(resultado), self.caminho)
        self.assertTrue(self.caminho.exists())
        self.assertFalse((outra_pasta / "teste.db").exists())


if __name__ == "__main__":
    unittest.main()
