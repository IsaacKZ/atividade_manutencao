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
        self.assertNotIn("Novo nome", saida)
        self.assertEqual(saida.count("=== MENU ==="), 2)
        self.assertEqual(clientes.listar_clientes(), [])

    def test_edicao_com_id_inexistente_nao_pede_novos_dados(self):
        self.criar_usuario_antigo()
        clientes.cadastrar_cliente("Ana", "52998224725", "ana@example.com", "111")
        original = clientes.listar_clientes()
        saida = self.executar("operador\nSenhaTeste123\n3\n999\n0\n0\n")
        self.assertIn("nenhum cliente encontrado com o ID 999", saida)
        self.assertNotIn("Novo nome", saida)
        self.assertNotIn("Novo CPF", saida)
        self.assertNotIn("Novo email", saida)
        self.assertNotIn("Novo telefone", saida)
        self.assertEqual(saida.count("=== MENU ==="), 2)
        self.assertEqual(clientes.listar_clientes(), original)

    def test_exclusao_sem_clientes_nao_pede_id_ou_confirmacao(self):
        self.criar_usuario_antigo()
        saida = self.executar("operador\nSenhaTeste123\n4\n0\n")
        self.assertIn("Nenhum cliente cadastrado.", saida)
        self.assertNotIn("ID do cliente a excluir:", saida)
        self.assertNotIn("Tem certeza", saida)
        self.assertEqual(saida.count("=== MENU ==="), 2)
        self.assertEqual(clientes.listar_clientes(), [])

    def test_exclusao_com_id_inexistente_nao_pede_confirmacao(self):
        self.criar_usuario_antigo()
        clientes.cadastrar_cliente("Ana", "52998224725", "", "")
        original = clientes.listar_clientes()
        saida = self.executar("operador\nSenhaTeste123\n4\n999\n0\n0\n")
        self.assertIn("nenhum cliente encontrado com o ID 999", saida)
        self.assertNotIn("Tem certeza", saida)
        self.assertEqual(saida.count("=== MENU ==="), 2)
        self.assertEqual(clientes.listar_clientes(), original)

    def test_lista_nome_longo_e_campos_nulos_sem_interromper_o_menu(self):
        self.criar_usuario_antigo()
        nome = "Nome de teste maior que a largura antiga da coluna"
        conexao = database.conectar()
        conexao.execute("INSERT INTO clientes (nome, cpf) VALUES (?, ?)", (nome, "52998224725"))
        conexao.commit()
        conexao.close()
        original = clientes.listar_clientes()
        saida = self.executar("operador\nSenhaTeste123\n2\n0\n")
        self.assertIn("ID | Nome | CPF | Email | Telefone", saida)
        self.assertIn(nome + " | 52998224725 |  | ", saida)
        self.assertEqual(clientes.listar_clientes(), original)

    def test_enter_na_edicao_mantem_todos_os_campos(self):
        self.criar_usuario_antigo()
        clientes.cadastrar_cliente("Ana", "52998224725", "ana@example.com", "111")
        original = clientes.listar_clientes()
        saida = self.executar("operador\nSenhaTeste123\n3\n1\n\n\n\n\n0\n")
        self.assertIn("Nenhuma alteração realizada.", saida)
        self.assertIn("ana@example.com", saida)
        self.assertEqual(clientes.listar_clientes(), original)

    def test_edicao_altera_nome_e_preserva_outros_campos_com_enter(self):
        self.criar_usuario_antigo()
        clientes.cadastrar_cliente("Ana", "52998224725", "ana@example.com", "111")
        saida = self.executar("operador\nSenhaTeste123\n3\n1\nAna Silva\n\n\n\n0\n")
        self.assertIn("Cliente atualizado com sucesso!", saida)
        self.assertEqual(clientes.listar_clientes()[0][1:], ("Ana Silva", "52998224725", "ana@example.com", "111"))

    def test_hifen_apaga_contatos_explicitamente_na_edicao(self):
        self.criar_usuario_antigo()
        clientes.cadastrar_cliente("Ana", "52998224725", "ana@example.com", "111")
        saida = self.executar("operador\nSenhaTeste123\n3\n1\n\n\n-\n-\n0\n")
        self.assertIn("Cliente atualizado com sucesso!", saida)
        self.assertEqual(clientes.listar_clientes()[0][1:], ("Ana", "52998224725", "", ""))

    def test_cadastro_preserva_hifen_nos_contatos(self):
        self.criar_usuario_antigo()
        saida = self.executar(
            "operador\nSenhaTeste123\n1\nAna\n52998224725\n-\n-\n0\n"
        )
        self.assertIn("Cliente cadastrado com sucesso!", saida)
        self.assertEqual(clientes.listar_clientes()[0][3:], ("-", "-"))

    def test_enter_na_edicao_preserva_contatos_nulos(self):
        self.criar_usuario_antigo()
        clientes.cadastrar_cliente("Ana", "52998224725", None, None)
        original = clientes.listar_clientes()
        saida = self.executar("operador\nSenhaTeste123\n3\n1\n\n\n\n\n0\n")
        self.assertIn("Novo email [] (Enter mantém; - apaga):", saida)
        self.assertIn("Novo telefone [] (Enter mantém; - apaga):", saida)
        self.assertIn("Nenhuma alteração realizada.", saida)
        self.assertEqual(clientes.listar_clientes(), original)

    def test_edicao_pode_apagar_um_contato_e_manter_o_outro(self):
        self.criar_usuario_antigo()
        clientes.cadastrar_cliente("Ana", "52998224725", "ana@example.com", "111")
        saida = self.executar("operador\nSenhaTeste123\n3\n1\n\n\n - \n   \n0\n")
        self.assertIn("Cliente atualizado com sucesso!", saida)
        self.assertEqual(clientes.listar_clientes()[0][3:], ("", "111"))

    def test_nome_vazio_e_corrigido_antes_de_pedir_cpf(self):
        self.criar_usuario_antigo()
        saida = self.executar("operador\nSenhaTeste123\n1\n\n   \nAna\n52998224725\nemail\n111\n0\n")
        self.assertEqual(saida.count("o nome não pode ficar vazio."), 2)
        self.assertLess(saida.index("o nome não pode ficar vazio."), saida.index("CPF ("))
        self.assertEqual(clientes.listar_clientes()[0][1], "Ana")

    def test_cpf_invalido_e_corrigido_antes_de_email_sem_repetir_nome(self):
        self.criar_usuario_antigo()
        saida = self.executar("operador\nSenhaTeste123\n1\nAna\n123\n529.982.247-25\nemail\n111\n0\n")
        self.assertIn("Cliente cadastrado com sucesso!", saida)
        self.assertLess(saida.index("CPF inválido."), saida.index("Email (opcional"))
        self.assertEqual(saida.count("Nome:"), 1)
        self.assertEqual(clientes.listar_clientes()[0][1:3], ("Ana", "52998224725"))

    def test_cpf_duplicado_pede_outro_cpf_sem_descartar_nome(self):
        self.criar_usuario_antigo()
        clientes.cadastrar_cliente("Ana", "52998224725", "", "")
        saida = self.executar("operador\nSenhaTeste123\n1\nBia\n529.982.247-25\n11144477735\nemail\n222\n0\n")
        self.assertIn("já existe um cliente cadastrado com esse CPF.", saida)
        self.assertEqual(saida.count("Nome:"), 1)
        self.assertEqual(clientes.listar_clientes()[1][1:3], ("Bia", "11144477735"))

    def test_espacos_em_usuario_menu_e_cpf_sao_aceitos_sem_mudar_senha(self):
        self.criar_usuario_antigo("operador", " senha ")
        saida = self.executar(" operador \n senha \n 1 \nAna\n 529.982.247-25 \nemail\n111\n 2 \n 0 \n")
        self.assertIn("Bem-vindo, operador!", saida)
        self.assertNotIn("Opção inválida.", saida)
        self.assertEqual(clientes.listar_clientes()[0][2], "52998224725")

    def test_cpf_duplicado_na_edicao_pode_ser_corrigido_com_enter(self):
        self.criar_usuario_antigo()
        clientes.cadastrar_cliente("Ana", "52998224725", "ana@example.com", "111")
        clientes.cadastrar_cliente("Bia", "11144477735", "bia@example.com", "222")
        original = clientes.listar_clientes()
        saida = self.executar("operador\nSenhaTeste123\n3\n1\n\n111.444.777-35\n\n\n\n0\n")
        self.assertIn("já existe um cliente cadastrado com esse CPF.", saida)
        self.assertIn("Nenhuma alteração realizada.", saida)
        self.assertEqual(clientes.listar_clientes(), original)

    def test_confirmacao_por_extenso_exclui_cliente(self):
        self.criar_usuario_antigo()
        clientes.cadastrar_cliente("Ana", "52998224725", "", "")
        saida = self.executar("operador\nSenhaTeste123\n4\n1\nsim\n0\n")
        self.assertIn("Cliente excluído com sucesso!", saida)
        self.assertEqual(clientes.listar_clientes(), [])


if __name__ == "__main__":
    unittest.main()
