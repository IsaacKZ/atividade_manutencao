import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import database
from auth import login
from clientes import cadastrar_cliente, editar_cliente, excluir_cliente, listar_clientes


class SistemaTest(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.addCleanup(self.pasta.cleanup)
        ajuste = patch.object(database, "DB_PATH", str(Path(self.pasta.name) / "sistema.db"))
        ajuste.start()
        self.addCleanup(ajuste.stop)
        database.inicializar_banco()

    def cadastrar(self, cpf="12345678901"):
        cadastrar_cliente("Ana", cpf, "ana@example.com", "11999999999")
        return listar_clientes()[-1][0]

    def executar_menu(self, entradas):
        resultado = subprocess.run(
            [sys.executable, "-B", str(Path(__file__).with_name("main.py"))],
            input="admin\nadmin123\n" + entradas,
            text=True, capture_output=True, cwd=self.pasta.name,
            timeout=10, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        return resultado.stdout

    def test_listar_nao_pede_edicao(self):
        self.cadastrar()
        saida = self.executar_menu("2\n0\n")
        self.assertNotIn("ID do cliente a editar", saida)
        self.assertEqual(saida.count("ana@example.com"), 1)

    def test_editar_diretamente_pelo_menu(self):
        cliente = self.cadastrar()
        saida = self.executar_menu(f"3\n{cliente}\nMaria\n12345678901\nmaria@example.com\n123\n0\n")
        self.assertIn("Cliente atualizado com sucesso!", saida)
        self.assertEqual(listar_clientes()[0][1:], ("Maria", "12345678901", "maria@example.com", "123"))

    def test_edicao_rejeita_nome_vazio(self):
        cliente = self.cadastrar()
        with self.assertRaises(ValueError):
            editar_cliente(cliente, "   ", "12345678901", "", "")
        self.assertEqual(listar_clientes()[0][1], "Ana")

    def test_edicao_rejeita_cpf_invalido(self):
        cliente = self.cadastrar()
        with self.assertRaises(ValueError):
            editar_cliente(cliente, "Ana", "123", "", "")
        self.assertEqual(listar_clientes()[0][2], "12345678901")

    def test_edicao_rejeita_cpf_de_outro_cliente(self):
        cliente = self.cadastrar()
        self.cadastrar("98765432100")
        with self.assertRaises(ValueError):
            editar_cliente(cliente, "Ana", "98765432100", "", "")
        self.assertEqual(listar_clientes()[0][2], "12345678901")

    def test_edicao_permite_manter_proprio_cpf(self):
        cliente = self.cadastrar()
        self.assertTrue(editar_cliente(cliente, "Maria", "12345678901", "", ""))

    def test_menu_trata_edicao_invalida(self):
        cliente = self.cadastrar()
        saida = self.executar_menu(f"3\n{cliente}\nAna\n123\nemail\n123\n0\n")
        self.assertIn("Erro ao editar cliente:", saida)
        self.assertEqual(listar_clientes()[0][2], "12345678901")

    def test_login_e_inicializacao_repetida(self):
        database.inicializar_banco()
        self.assertTrue(login("admin", "admin123"))
        self.assertFalse(login("admin", "errada"))

    def test_cadastro_valida_dados(self):
        self.cadastrar()
        for nome, cpf in [("", "98765432100"), ("Ana", "123"), ("Ana", "12345678901")]:
            with self.subTest(nome=nome, cpf=cpf), self.assertRaises(ValueError):
                cadastrar_cliente(nome, cpf, "", "")
        self.assertEqual(len(listar_clientes()), 1)

    def test_ids_inexistentes(self):
        self.assertFalse(editar_cliente("999", "Ana", "12345678901", "", ""))
        self.assertFalse(excluir_cliente("999"))
        saida = self.executar_menu("3\n999\nAna\n12345678901\nemail\n123\n4\n999\ns\n0\n")
        self.assertEqual(saida.count("nenhum cliente encontrado"), 2)

    def test_exclusao_cancelada_e_confirmada(self):
        cliente = self.cadastrar()
        self.assertIn("Exclusão cancelada.", self.executar_menu(f"4\n{cliente}\nn\n0\n"))
        self.assertEqual(len(listar_clientes()), 1)
        self.assertIn("Cliente excluído com sucesso!", self.executar_menu(f"4\n{cliente}\ns\n0\n"))
        self.assertEqual(listar_clientes(), [])

    def test_cadastro_pelo_menu(self):
        saida = self.executar_menu("1\nAna\n12345678901\nana@example.com\n123\n2\n0\n")
        self.assertIn("Cliente cadastrado com sucesso!", saida)
        self.assertEqual(len(listar_clientes()), 1)


if __name__ == "__main__":
    unittest.main()
