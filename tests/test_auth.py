from contextlib import closing
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import auth
import database


class AutenticacaoTest(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.addCleanup(self.pasta.cleanup)
        ajuste = patch.object(
            database, "DB_PATH", str(Path(self.pasta.name) / "teste.db")
        )
        ajuste.start()
        self.addCleanup(ajuste.stop)
        database.inicializar_banco()

    def inserir_usuario_antigo(self, username="antigo", senha="senha antiga"):
        with closing(database.conectar()) as conexao:
            conexao.execute(
                "INSERT INTO usuarios (username, senha) VALUES (?, ?)",
                (username, senha),
            )
            conexao.commit()

    def senha_salva(self, username="antigo"):
        with closing(database.conectar()) as conexao:
            return conexao.execute(
                "SELECT senha FROM usuarios WHERE username = ?", (username,)
            ).fetchone()[0]

    def cadastrar(self, username, senha):
        self.assertTrue(
            callable(getattr(auth, "cadastrar_usuario", None)),
            "O cadastro de usuário precisa estar disponível.",
        )
        return auth.cadastrar_usuario(username, senha)

    def trocar(self, username, senha_atual, nova_senha):
        self.assertTrue(
            callable(getattr(auth, "trocar_senha", None)),
            "A troca de senha precisa estar disponível.",
        )
        return auth.trocar_senha(username, senha_atual, nova_senha)

    def verificar_hash(self, valor, senha):
        partes = valor.split("$")
        self.assertEqual(len(partes), 4, "A senha deve ser salva como hash com salt.")
        algoritmo, iteracoes, salt, resumo = partes
        self.assertEqual(algoritmo, "pbkdf2_sha256")
        self.assertEqual(iteracoes, "600000")
        self.assertEqual(len(bytes.fromhex(salt)), 16)
        esperado = hashlib.pbkdf2_hmac(
            "sha256", senha.encode("utf-8"), bytes.fromhex(salt), 600000
        ).hex()
        self.assertEqual(resumo, esperado)

    def test_login_antigo_migra_senha_sem_trocar_id(self):
        self.inserir_usuario_antigo(senha="Senha com acentuação")
        with closing(database.conectar()) as conexao:
            usuario_antes = conexao.execute("SELECT id, username FROM usuarios").fetchone()
        self.assertTrue(auth.login("antigo", "Senha com acentuação"))
        self.verificar_hash(self.senha_salva(), "Senha com acentuação")
        with closing(database.conectar()) as conexao:
            self.assertEqual(
                conexao.execute("SELECT id, username FROM usuarios").fetchone(),
                usuario_antes,
            )

    def test_login_incorreto_nao_migra_senha_antiga(self):
        self.inserir_usuario_antigo()
        self.assertFalse(auth.login("antigo", "incorreta"))
        self.assertEqual(self.senha_salva(), "senha antiga")

    def test_login_depois_da_migracao_preserva_hash(self):
        self.inserir_usuario_antigo()
        self.assertTrue(auth.login("antigo", "senha antiga"))
        primeiro_hash = self.senha_salva()
        self.verificar_hash(primeiro_hash, "senha antiga")
        self.assertTrue(auth.login("antigo", "senha antiga"))
        self.assertEqual(self.senha_salva(), primeiro_hash)
        self.assertFalse(auth.login("antigo", "incorreta"))
        self.assertEqual(self.senha_salva(), primeiro_hash)

    def test_senhas_iguais_recebem_salts_independentes(self):
        self.inserir_usuario_antigo("primeiro", "senha antiga")
        self.inserir_usuario_antigo("segundo", "senha antiga")
        self.assertTrue(auth.login("primeiro", "senha antiga"))
        self.assertTrue(auth.login("segundo", "senha antiga"))
        primeiro_hash = self.senha_salva("primeiro")
        segundo_hash = self.senha_salva("segundo")
        self.verificar_hash(primeiro_hash, "senha antiga")
        self.verificar_hash(segundo_hash, "senha antiga")
        self.assertNotEqual(primeiro_hash.split("$")[2], segundo_hash.split("$")[2])

    def test_hash_nao_pode_ser_usado_como_senha(self):
        salt = bytes(range(16))
        resumo = hashlib.pbkdf2_hmac("sha256", b"senha segura", salt, 600000).hex()
        valor = "pbkdf2_sha256$600000$" + salt.hex() + "$" + resumo
        self.inserir_usuario_antigo(senha=valor)
        self.assertTrue(auth.login("antigo", "senha segura"))
        self.assertFalse(auth.login("antigo", valor))
        self.assertEqual(self.senha_salva(), valor)

    def test_hash_invalido_e_rejeitado_sem_alteracao(self):
        valor = "pbkdf2_sha256$600000$salt-invalido$resumo-invalido"
        self.inserir_usuario_antigo(senha=valor)
        self.assertFalse(auth.login("antigo", valor))
        self.assertFalse(auth.login("antigo", "senha segura"))
        self.assertEqual(self.senha_salva(), valor)

    def test_usuario_inexistente_e_tentativa_sql_nao_autenticam(self):
        self.inserir_usuario_antigo()
        self.assertFalse(auth.login("ausente", "senha antiga"))
        self.assertFalse(auth.login("' OR 1=1 --", "senha antiga"))

    def test_cadastro_salva_hash_e_permite_login(self):
        self.cadastrar("  novo  ", "senha segura")
        self.verificar_hash(self.senha_salva("novo"), "senha segura")
        self.assertTrue(auth.login("novo", "senha segura"))
        self.assertFalse(auth.login("novo", "incorreta"))

    def test_cadastro_rejeita_username_vazio(self):
        for username in ("", "   "):
            with self.subTest(username=username), self.assertRaises(ValueError):
                self.cadastrar(username, "senha segura")
        with closing(database.conectar()) as conexao:
            self.assertEqual(conexao.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0], 0)

    def test_cadastro_rejeita_senha_vazia_ou_curta(self):
        for senha in ("", "        ", "1234567"):
            with self.subTest(senha=senha), self.assertRaises(ValueError):
                self.cadastrar("novo", senha)
        with closing(database.conectar()) as conexao:
            self.assertEqual(conexao.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0], 0)

    def test_cadastro_rejeita_antiga_senha_padrao(self):
        with self.assertRaisesRegex(
            ValueError, "Escolha uma senha diferente da antiga senha padrão."
        ):
            self.cadastrar("novo", "admin123")

    def test_cadastro_rejeita_duplicado_sem_alterar_senha(self):
        self.cadastrar("novo", "senha segura")
        hash_antes = self.senha_salva("novo")
        with self.assertRaises(ValueError):
            self.cadastrar(" novo ", "outra senha segura")
        self.assertEqual(self.senha_salva("novo"), hash_antes)

    def test_cadastro_usa_salts_independentes(self):
        self.cadastrar("primeiro", "senha segura")
        self.cadastrar("segundo", "senha segura")
        primeiro_hash = self.senha_salva("primeiro")
        segundo_hash = self.senha_salva("segundo")
        self.verificar_hash(primeiro_hash, "senha segura")
        self.verificar_hash(segundo_hash, "senha segura")
        self.assertNotEqual(primeiro_hash.split("$")[2], segundo_hash.split("$")[2])

    def test_existe_usuario_identifica_banco_vazio_e_preenchido(self):
        self.assertTrue(
            callable(getattr(auth, "existe_usuario", None)),
            "A consulta de existência de usuário precisa estar disponível.",
        )
        self.assertFalse(auth.existe_usuario())
        self.inserir_usuario_antigo()
        self.assertTrue(auth.existe_usuario())

    def test_troca_de_senha_atualiza_hash_e_login(self):
        self.cadastrar("novo", "senha segura")
        hash_antes = self.senha_salva("novo")
        self.assertTrue(self.trocar("novo", "senha segura", "12345678"))
        hash_depois = self.senha_salva("novo")
        self.verificar_hash(hash_depois, "12345678")
        self.assertNotEqual(hash_antes.split("$")[2], hash_depois.split("$")[2])
        self.assertFalse(auth.login("novo", "senha segura"))
        self.assertTrue(auth.login("novo", "12345678"))

    def test_troca_de_senha_antiga_nao_exige_login_previo(self):
        self.inserir_usuario_antigo("admin", "admin123")
        self.assertTrue(self.trocar("admin", "admin123", "nova senha segura"))
        self.verificar_hash(self.senha_salva("admin"), "nova senha segura")
        self.assertFalse(auth.login("admin", "admin123"))
        self.assertTrue(auth.login("admin", "nova senha segura"))

    def test_troca_com_senha_atual_incorreta_nao_altera_dados(self):
        self.inserir_usuario_antigo()
        self.assertFalse(self.trocar("antigo", "incorreta", "nova senha segura"))
        self.assertEqual(self.senha_salva(), "senha antiga")

    def test_troca_de_usuario_inexistente_retorna_falso(self):
        self.assertFalse(self.trocar("ausente", "senha antiga", "nova senha segura"))

    def test_troca_rejeita_senha_vazia_ou_curta_sem_migrar(self):
        self.inserir_usuario_antigo()
        for senha in ("", "        ", "1234567"):
            with self.subTest(senha=senha), self.assertRaises(ValueError):
                self.trocar("antigo", "senha antiga", senha)
            self.assertEqual(self.senha_salva(), "senha antiga")

    def test_troca_rejeita_antiga_senha_padrao_sem_alteracao(self):
        self.inserir_usuario_antigo("admin", "admin123")
        with self.assertRaisesRegex(
            ValueError, "Escolha uma senha diferente da antiga senha padrão."
        ):
            self.trocar("admin", "admin123", "admin123")
        self.assertEqual(self.senha_salva("admin"), "admin123")


if __name__ == "__main__":
    unittest.main()
