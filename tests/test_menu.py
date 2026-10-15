"""Exercita o programa real com entrada de terminal e SQLite isolado."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import clientes
import database


class MenuTest(unittest.TestCase):
    def setUp(self):
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        self.pasta = Path(pasta.name)
        self.banco = self.pasta / "teste.db"
        ajuste = patch.object(database, "DB_PATH", str(self.banco))
        ajuste.start()
        self.addCleanup(ajuste.stop)
        database.inicializar_banco()
        with database.conectar() as conexao:
            conexao.execute("DELETE FROM usuarios")

    def executar(self, entrada):
        ambiente = dict(os.environ)
        ambiente["SISTEMA_DB_PATH"] = str(self.banco)
        resultado = subprocess.run(
            [sys.executable, "-B", str(Path(__file__).resolve().parents[1] / "main.py")],
            input=entrada, text=True, capture_output=True, cwd=self.pasta,
            env=ambiente, timeout=15,
        )
        self.assertEqual(resultado.returncode, 0, resultado.stderr + resultado.stdout)
        return resultado.stdout

    def criar_usuario_antigo(self, nome="operador", senha="SenhaTeste123"):
        with database.conectar() as conexao:
            conexao.execute("INSERT INTO usuarios (username, senha) VALUES (?, ?)", (nome, senha))

    def test_banco_novo_abre_login_sem_cadastro_ou_troca_de_senha(self):
        saida = self.executar("admin\nadmin123\n0\n")
        self.assertIn("Bem-vindo, admin!", saida)
        self.assertNotIn("CRIAR PRIMEIRA CONTA", saida)
        self.assertNotIn("Confirme", saida)
        self.assertNotIn("Nova senha", saida)
        self.assertIn("Saindo...", saida)

    def test_senha_curta_existente_continua_funcionando(self):
        self.criar_usuario_antigo("teste", "1")
        saida = self.executar("teste\n1\n0\n")
        self.assertIn("Bem-vindo, teste!", saida)
        self.assertNotIn("Nova senha", saida)

    def test_edicao_nao_reutiliza_id_de_exclusao_cancelada(self):
        self.criar_usuario_antigo()
        clientes.cadastrar_cliente("Ana", "52998224725", "ana@example.com", "111")
        clientes.cadastrar_cliente("Bia", "11144477735", "bia@example.com", "222")
        a, b = clientes.listar_clientes()
        saida = self.executar(
            f"operador\nSenhaTeste123\n2\n4\n{b[0]}\nn\n3\n{a[0]}\nAna Silva\n52998224725\nnova@example.com\n333\n0\n"
        )
        self.assertIn("Exclusão cancelada.", saida)
        self.assertIn("Cliente atualizado com sucesso!", saida)
        registros = clientes.listar_clientes()
        self.assertEqual(registros[0][1], "Ana Silva")
        self.assertEqual(registros[1], b)

    def test_login_incorreto_nao_impede_login_valido_seguinte(self):
        self.criar_usuario_antigo()
        saida = self.executar("operador\nerrada\noperador\nSenhaTeste123\n0\n")
        self.assertIn("Usuário ou senha inválidos.", saida)
        self.assertIn("Bem-vindo, operador!", saida)

    def test_edicao_sem_clientes_volta_ao_menu_sem_perguntas(self):
        self.criar_usuario_antigo()
        saida = self.executar("operador\nSenhaTeste123\n3\n0\n")
        self.assertIn("Nenhum cliente cadastrado.", saida)
        self.assertNotIn("ID do cliente a editar:", saida)
        self.assertNotIn("Novo nome:", saida)
        self.assertEqual(saida.count("=== MENU ==="), 2)
        self.assertEqual(clientes.listar_clientes(), [])

    def test_edicao_com_id_inexistente_nao_pede_novos_dados(self):
        self.criar_usuario_antigo()
        clientes.cadastrar_cliente("Ana", "52998224725", "ana@example.com", "111")
        original = clientes.listar_clientes()
        saida = self.executar("operador\nSenhaTeste123\n3\n999\n0\n")
        self.assertIn("nenhum cliente encontrado com o ID 999", saida)
        self.assertNotIn("Novo nome:", saida)
        self.assertNotIn("Novo CPF:", saida)
        self.assertNotIn("Novo email:", saida)
        self.assertNotIn("Novo telefone:", saida)
        self.assertEqual(saida.count("=== MENU ==="), 2)
        self.assertEqual(clientes.listar_clientes(), original)


if __name__ == "__main__":
    unittest.main()
