"""Regras de CPF e preservação dos dados em operações rejeitadas."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import clientes
import database


class ClientesTest(unittest.TestCase):
    def setUp(self):
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        ajuste = patch.object(database, "DB_PATH", str(Path(pasta.name) / "teste.db"))
        ajuste.start()
        self.addCleanup(ajuste.stop)
        database.inicializar_banco()

    def test_aceita_cpfs_com_digitos_verificadores_corretos(self):
        for cpf in ("52998224725", "11144477735", "01234567890"):
            with self.subTest(cpf=cpf):
                self.assertTrue(clientes.validar_cpf(cpf))

    def test_rejeita_sequencias_de_digitos_iguais(self):
        for digito in "0123456789":
            with self.subTest(digito=digito):
                self.assertFalse(clientes.validar_cpf(digito * 11))

    def test_rejeita_cada_digito_verificador_incorreto(self):
        for cpf in ("52998224715", "52998224724", "12345678901"):
            with self.subTest(cpf=cpf):
                self.assertFalse(clientes.validar_cpf(cpf))

    def test_rejeita_formato_e_caracteres_fora_de_zero_a_nove(self):
        for cpf in ("", "123", "529.982.247-24", "5299822472a", "²" * 11, "５２９９８２２４７２５"):
            with self.subTest(cpf=cpf):
                self.assertFalse(clientes.validar_cpf(cpf))

    def test_cadastro_aceita_pontuacao_e_espacos_e_salva_so_digitos(self):
        self.assertTrue(clientes.validar_cpf(" 529.982.247-25 "))
        clientes.cadastrar_cliente("Ana", " 529.982.247-25 ", "", "")
        self.assertEqual(clientes.listar_clientes()[0][2], "52998224725")

    def test_cpf_pontuado_nao_permite_cadastro_duplicado(self):
        clientes.cadastrar_cliente("Ana", "52998224725", "", "")
        with self.assertRaisesRegex(ValueError, "já existe"):
            clientes.cadastrar_cliente("Bia", "529.982.247-25", "", "")
        self.assertEqual(len(clientes.listar_clientes()), 1)

    def test_edicao_aceita_proprio_cpf_pontuado_e_rejeita_o_de_outro(self):
        clientes.cadastrar_cliente("Ana", "52998224725", "", "")
        clientes.cadastrar_cliente("Bia", "11144477735", "", "")
        ident = clientes.listar_clientes()[0][0]
        self.assertTrue(clientes.editar_cliente(ident, "Ana", "529.982.247-25", "", ""))
        self.assertEqual(clientes.listar_clientes()[0][2], "52998224725")
        with self.assertRaises(ValueError):
            clientes.editar_cliente(ident, "Ana", "111.444.777-35", "", "")

    def test_cadastro_rejeita_cpf_sem_verificador_valido(self):
        with self.assertRaises(ValueError):
            clientes.cadastrar_cliente("Ana", "12345678901", "", "")
        self.assertEqual(clientes.listar_clientes(), [])

    def test_edicao_invalida_preserva_todos_os_campos(self):
        clientes.cadastrar_cliente("Ana", "52998224725", "ana@example.com", "111")
        original = clientes.listar_clientes()
        with self.assertRaises(ValueError):
            clientes.editar_cliente(original[0][0], "Outro nome", "12345678901", "outro@example.com", "222")
        self.assertEqual(clientes.listar_clientes(), original)

    def test_edicao_permite_proprio_cpf_mas_rejeita_cpf_alheio(self):
        clientes.cadastrar_cliente("Ana", "52998224725", "", "")
        clientes.cadastrar_cliente("Bia", "11144477735", "", "")
        ident = clientes.listar_clientes()[0][0]
        self.assertTrue(clientes.editar_cliente(ident, "Ana Silva", "52998224725", "", ""))
        with self.assertRaises(ValueError):
            clientes.editar_cliente(ident, "Ana Silva", "11144477735", "", "")
        self.assertEqual(clientes.listar_clientes()[0][2], "52998224725")


if __name__ == "__main__":
    unittest.main()
