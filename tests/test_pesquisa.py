"""Pesquisa real por nome e CPF, mantendo a ordem e os dados do SQLite."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import clientes
import database


class PesquisaClientesTest(unittest.TestCase):
    def setUp(self):
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        ajuste = patch.object(database, "DB_PATH", str(Path(pasta.name) / "teste.db"))
        ajuste.start()
        self.addCleanup(ajuste.stop)
        database.inicializar_banco()
        registros = [
            ("João Silva", "52998224725", "joao@example.com", "111"),
            ("MARIA João", "111.444.777-35", "", ""),
            ("Ana % Silva", "01234567890", None, None),
            ("Bia_Silva", "12345678909", "", ""),
            (None, None, None, None),
        ]
        for registro in registros:
            database.executar(
                "INSERT INTO clientes (nome, cpf, email, telefone) VALUES (?, ?, ?, ?)",
                registro,
            )
        self.originais = clientes.listar_clientes()

    def test_nome_parcial_ignora_caixa_inclusive_letras_acentuadas(self):
        self.assertEqual(clientes.pesquisar_clientes(" JOÃO "), self.originais[:2])
        self.assertEqual(clientes.pesquisar_clientes("maria"), [self.originais[1]])

    def test_cpf_completo_ou_parcial_aceita_mascara_na_busca_e_no_banco(self):
        for termo, esperado in (
            ("529.982.247-25", self.originais[0]),
            ("982247", self.originais[0]),
            ("982.247", self.originais[0]),
            ("11144477735", self.originais[1]),
            ("444.777", self.originais[1]),
        ):
            with self.subTest(termo=termo):
                self.assertEqual(clientes.pesquisar_clientes(termo), [esperado])

    def test_busca_vazia_retorna_todos_inclusive_campos_nulos(self):
        for termo in ("", "   "):
            with self.subTest(termo=termo):
                self.assertEqual(clientes.pesquisar_clientes(termo), self.originais)

    def test_busca_sem_resultado_retorna_lista_vazia_sem_alterar_dados(self):
        self.assertEqual(clientes.pesquisar_clientes("não cadastrado"), [])
        self.assertEqual(clientes.listar_clientes(), self.originais)

    def test_porcentagem_e_sublinhado_sao_partes_literais_do_nome(self):
        self.assertEqual(clientes.pesquisar_clientes("%"), [self.originais[2]])
        self.assertEqual(clientes.pesquisar_clientes("_"), [self.originais[3]])

    def test_so_pontuacao_de_cpf_nao_encontra_todos(self):
        self.assertEqual(clientes.pesquisar_clientes(".-"), [])


if __name__ == "__main__":
    unittest.main()
