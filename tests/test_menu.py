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

    def test_primeiro_acesso_cria_conta_escolhida_pelo_usuario(self):
        saida = self.executar("operador\nSenhaTeste123\nSenhaTeste123\noperador\nSenhaTeste123\n0\n")
        self.assertIn("Conta criada com sucesso!", saida)
        self.assertIn("Bem-vindo, operador!", saida)
        with database.conectar() as conexao:
            usuarios = conexao.execute("SELECT username, senha FROM usuarios").fetchall()
        self.assertEqual(len(usuarios), 1)
        self.assertEqual(usuarios[0][0], "operador")
        self.assertNotEqual(usuarios[0][1], "SenhaTeste123")

    def test_primeiro_acesso_rejeita_confirmacao_diferente(self):
        saida = self.executar("operador\nSenhaTeste123\nDiferente123\noperador\nSenhaTeste123\nSenhaTeste123\noperador\nSenhaTeste123\n0\n")
        self.assertIn("As senhas não conferem.", saida)
        self.assertEqual(saida.count("Conta criada com sucesso!"), 1)

    def test_primeiro_acesso_rejeita_senha_padrao_antiga(self):
        saida = self.executar("admin\nadmin123\nadmin123\nadmin\nSenhaNova123\nSenhaNova123\nadmin\nSenhaNova123\n0\n")
        self.assertIn("Escolha uma senha diferente da antiga senha padrão.", saida)
        self.assertIn("Bem-vindo, admin!", saida)

    def test_conta_padrao_antiga_exige_troca_antes_do_menu(self):
        self.criar_usuario_antigo("admin", "admin123")
        saida = self.executar("admin\nadmin123\nSenhaNova123\nSenhaNova123\n0\n")
        self.assertIn("Senha alterada com sucesso!", saida)
        self.assertLess(saida.index("Senha alterada com sucesso!"), saida.index("=== MENU ==="))
        nova_saida = self.executar("admin\nadmin123\nadmin\nSenhaNova123\n0\n")
        self.assertIn("Usuário ou senha inválidos.", nova_saida)
        self.assertIn("Bem-vindo, admin!", nova_saida)

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
