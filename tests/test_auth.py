"""Login simples: consulta os dados sem modificar usuários ou senhas."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import auth
import database


class AutenticacaoTest(unittest.TestCase):
    def setUp(self):
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        ajuste = patch.object(database, "DB_PATH", str(Path(pasta.name) / "teste.db"))
        ajuste.start()
        self.addCleanup(ajuste.stop)
        database.inicializar_banco()

    def cadastrar_para_teste(self, usuario, senha):
        conexao = database.conectar()
        conexao.execute("INSERT INTO usuarios (username, senha) VALUES (?, ?)", (usuario, senha))
        conexao.commit()
        conexao.close()

    def usuarios(self):
        conexao = database.conectar()
        resultado = conexao.execute("SELECT id, username, senha FROM usuarios ORDER BY id").fetchall()
        conexao.close()
        return resultado

    def test_login_padrao_funciona_em_banco_novo(self):
        self.assertTrue(auth.login("admin", "admin123"))

    def test_login_correto_nao_modifica_a_senha(self):
        self.cadastrar_para_teste("teste", "1")
        antes = self.usuarios()
        self.assertTrue(auth.login("teste", "1"))
        self.assertTrue(auth.login("teste", "1"))
        self.assertEqual(self.usuarios(), antes)

    def test_login_incorreto_nao_modifica_usuarios(self):
        self.cadastrar_para_teste("teste", "123")
        antes = self.usuarios()
        self.assertFalse(auth.login("teste", "errada"))
        self.assertEqual(self.usuarios(), antes)

    def test_usuario_inexistente_e_texto_sql_nao_autenticam(self):
        self.assertFalse(auth.login("ausente", "123"))
        self.assertFalse(auth.login("' OR 1=1 --", "123"))

    def test_senha_com_acentos_e_maiusculas_e_comparada_exatamente(self):
        self.cadastrar_para_teste("teste", "Olá")
        self.assertTrue(auth.login("teste", "Olá"))
        self.assertFalse(auth.login("teste", "olá"))


if __name__ == "__main__":
    unittest.main()
