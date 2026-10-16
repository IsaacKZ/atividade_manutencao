"""Paginação e seleção no terminal, com entrada simulada e dados reais."""

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import clientes
import consulta_clientes
import database


class ConsultaClientesTest(unittest.TestCase):
    def setUp(self):
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        ajuste = patch.object(database, "DB_PATH", str(Path(pasta.name) / "teste.db"))
        ajuste.start()
        self.addCleanup(ajuste.stop)
        database.inicializar_banco()

    def adicionar_clientes(self, quantidade):
        for numero in range(1, quantidade + 1):
            database.executar(
                "INSERT INTO clientes (nome, cpf, email, telefone) VALUES (?, ?, ?, ?)",
                (f"Pessoa {numero:02}", f"{numero:011}", None, None),
            )
        return clientes.listar_clientes()

    def executar(self, funcao, entradas=(), *argumentos):
        respostas = iter(entradas)
        saida = StringIO()

        def responder(pergunta):
            print(pergunta, end="")
            try:
                return next(respostas)
            except StopIteration:
                self.fail(f"Pergunta inesperada: {pergunta}")

        with patch("builtins.input", responder), redirect_stdout(saida):
            resultado = funcao(*argumentos)
        return resultado, saida.getvalue()

    def test_lista_vazia_informa_e_retorna_false_sem_pedir_entrada(self):
        resultado, saida = self.executar(consulta_clientes.paginar_clientes, (), [])
        self.assertFalse(resultado)
        self.assertIn("Nenhum cliente cadastrado.", saida)

    def test_ate_dez_registros_exibe_todos_sem_pedir_comando(self):
        registros = self.adicionar_clientes(10)
        resultado, saida = self.executar(consulta_clientes.paginar_clientes, (), registros)
        self.assertTrue(resultado)
        self.assertIn("ID | Nome | CPF | Email | Telefone", saida)
        self.assertIn("10 | Pessoa 10 | 00000000010 |  | ", saida)
        self.assertNotIn("None", saida)

    def test_onze_registros_exibe_apenas_dez_na_primeira_pagina(self):
        registros = self.adicionar_clientes(11)
        resultado, saida = self.executar(consulta_clientes.paginar_clientes, ["0"], registros)
        self.assertTrue(resultado)
        self.assertIn("Página 1 de 2", saida)
        self.assertIn("Pessoa 10", saida)
        self.assertNotIn("Pessoa 11", saida)

    def test_enter_volta_da_listagem_com_mais_de_dez(self):
        registros = self.adicionar_clientes(11)
        resultado, saida = self.executar(consulta_clientes.paginar_clientes, [""], registros)
        self.assertTrue(resultado)
        self.assertNotIn("Pessoa 11", saida)

    def test_vinte_e_um_registros_permite_avancar_e_voltar(self):
        registros = self.adicionar_clientes(21)
        resultado, saida = self.executar(
            consulta_clientes.paginar_clientes, ["p", "p", "a", "0"], registros
        )
        self.assertTrue(resultado)
        self.assertIn("Página 3 de 3", saida)
        self.assertIn("21 | Pessoa 21", saida)
        self.assertEqual(saida.count("Página 2 de 3"), 2)

    def test_comando_invalido_e_limites_nao_encerram_paginacao(self):
        registros = self.adicionar_clientes(11)
        resultado, saida = self.executar(
            consulta_clientes.paginar_clientes, ["a", "xyz", "p", "p", "0"], registros
        )
        self.assertTrue(resultado)
        self.assertIn("primeira página", saida)
        self.assertIn("última página", saida)
        self.assertIn("Comando inválido", saida)
        self.assertIn("11 | Pessoa 11", saida)

    def test_busca_pelo_menu_filtra_registros_por_nome(self):
        self.adicionar_clientes(11)
        resultado, saida = self.executar(consulta_clientes.buscar_pelo_menu, ["Pessoa 11"])
        self.assertIsNone(resultado)
        self.assertIn("Buscar por nome ou CPF (Enter para listar todos): ", saida)
        self.assertIn("11 | Pessoa 11", saida)
        self.assertNotIn("1 | Pessoa 01", saida)

    def test_busca_pelo_menu_vazia_lista_todos_e_sem_resultado_informa(self):
        self.adicionar_clientes(2)
        _, saida = self.executar(consulta_clientes.buscar_pelo_menu, [""])
        self.assertIn("Pessoa 01", saida)
        self.assertIn("Pessoa 02", saida)
        _, saida = self.executar(consulta_clientes.buscar_pelo_menu, ["ausente"])
        self.assertIn("Nenhum cliente encontrado", saida)
        self.assertNotIn("Pessoa 01", saida)

    def test_selecao_sem_cadastro_retorna_none_sem_perguntar(self):
        for acao in ("editar", "excluir"):
            with self.subTest(acao=acao):
                resultado, saida = self.executar(consulta_clientes.selecionar_cliente, (), acao)
                self.assertIsNone(resultado)
                self.assertIn("Nenhum cliente cadastrado.", saida)
                self.assertNotIn("ID do cliente", saida)

    def test_id_invalido_ou_inexistente_permite_corrigir_sem_sair(self):
        registros = self.adicionar_clientes(1)
        for acao in ("editar", "excluir"):
            with self.subTest(acao=acao):
                resultado, saida = self.executar(
                    consulta_clientes.selecionar_cliente,
                    ["abc", "", "-1", "²", "999", "1"], acao,
                )
                self.assertEqual(resultado, registros[0])
                self.assertEqual(saida.count("ID numérico"), 4)
                self.assertIn("Erro: nenhum cliente encontrado com o ID 999.", saida)
                self.assertIn(f"ID do cliente a {acao}: ", saida)
        self.assertEqual(clientes.listar_clientes(), registros)

    def test_zero_cancela_selecao(self):
        self.adicionar_clientes(1)
        for acao, mensagem in (("editar", "Edição cancelada."), ("excluir", "Exclusão cancelada.")):
            with self.subTest(acao=acao):
                resultado, saida = self.executar(consulta_clientes.selecionar_cliente, ["0"], acao)
                self.assertIsNone(resultado)
                self.assertIn(mensagem, saida)

    def test_id_numerico_muito_longo_permite_corrigir(self):
        registros = self.adicionar_clientes(1)
        id_inexistente = "9" * 5000
        resultado, saida = self.executar(
            consulta_clientes.selecionar_cliente, [id_inexistente, "001"], "editar"
        )
        self.assertEqual(resultado, registros[0])
        self.assertIn(f"Erro: nenhum cliente encontrado com o ID {id_inexistente}.", saida)

    def test_selecao_paginas_e_busca_reinicia_na_primeira_pagina(self):
        registros = self.adicionar_clientes(21)
        resultado, saida = self.executar(
            consulta_clientes.selecionar_cliente, ["p", "p", "b", "Pessoa 01", "1"], "editar"
        )
        self.assertEqual(resultado, registros[0])
        self.assertIn("Página 3 de 3", saida)
        self.assertIn("21 | Pessoa 21", saida)
        depois_da_busca = saida.split("Buscar por nome ou CPF (Enter para listar todos): ", 1)[1]
        self.assertIn("1 | Pessoa 01", depois_da_busca)
        self.assertNotIn("21 | Pessoa 21", depois_da_busca)

    def test_selecao_aceita_id_de_outra_pagina_da_consulta_atual(self):
        registros = self.adicionar_clientes(21)
        resultado, saida = self.executar(consulta_clientes.selecionar_cliente, ["21"], "editar")
        self.assertEqual(resultado, registros[20])
        self.assertNotIn("21 | Pessoa 21", saida)

    def test_selecao_rejeita_id_fora_do_filtro_e_busca_vazia_limpa_filtro(self):
        registros = self.adicionar_clientes(2)
        resultado, saida = self.executar(
            consulta_clientes.selecionar_cliente,
            ["b", "Pessoa 02", "1", "b", "", "1"], "excluir",
        )
        self.assertEqual(resultado, registros[0])
        self.assertIn("Erro: nenhum cliente encontrado com o ID 1.", saida)
        self.assertEqual(clientes.listar_clientes(), registros)

    def test_busca_sem_resultados_na_selecao_permite_buscar_novamente(self):
        registros = self.adicionar_clientes(1)
        resultado, saida = self.executar(
            consulta_clientes.selecionar_cliente,
            ["b", "ausente", "b", "Pessoa 01", "1"], "editar",
        )
        self.assertEqual(resultado, registros[0])
        self.assertIn("Nenhum cliente encontrado", saida)

    def test_busca_sem_resultados_na_selecao_permite_voltar(self):
        self.adicionar_clientes(1)
        resultado, saida = self.executar(
            consulta_clientes.selecionar_cliente, ["b", "ausente", "0"], "editar"
        )
        self.assertIsNone(resultado)
        self.assertIn("Edição cancelada.", saida)

    def test_selecao_limites_e_comando_invalido_preservam_consulta(self):
        registros = self.adicionar_clientes(11)
        resultado, saida = self.executar(
            consulta_clientes.selecionar_cliente, ["a", "p", "p", "z", "11"], "editar"
        )
        self.assertEqual(resultado, registros[10])
        self.assertIn("primeira página", saida)
        self.assertIn("última página", saida)
        self.assertIn("ID numérico", saida)


if __name__ == "__main__":
    unittest.main()
