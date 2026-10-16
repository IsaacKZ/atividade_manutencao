"""Exercita as melhorias de UX com o programa real e bancos temporários."""

from contextlib import redirect_stdout
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import clientes
import database
import main
from tests.test_entrada_cpf import pty, terminal_cpf, termios


class ExperienciaTest(unittest.TestCase):
    def setUp(self):
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        self.pasta = Path(pasta.name)
        self.banco = self.pasta / "ux.db"
        ajuste = patch.object(database, "DB_PATH", str(self.banco))
        ajuste.start()
        self.addCleanup(ajuste.stop)
        database.inicializar_banco()

    def executar(self, entrada, banco=None, codigo=0):
        resultado = subprocess.run(
            [sys.executable, "-B", str(Path(main.__file__).resolve())],
            input=entrada,
            text=True,
            capture_output=True,
            cwd=self.pasta,
            timeout=10,
            env={**os.environ, "SISTEMA_DB_PATH": str(banco or self.banco)},
        )
        self.assertEqual(resultado.returncode, codigo, resultado.stderr + resultado.stdout)
        self.assertNotIn("Traceback", resultado.stderr)
        return resultado.stdout

    def criar_cliente(self):
        clientes.cadastrar_cliente("Ana", "52998224725", "ana@example.com", "111")

    def test_contatos_indicam_que_podem_ser_pulados(self):
        saida = self.executar("admin\nadmin123\n1\nAna\n52998224725\n\n\n0\n")
        self.assertIn("Email (opcional; Enter para pular):", saida)
        self.assertIn("Telefone (opcional; Enter para pular):", saida)
        self.assertEqual(clientes.listar_clientes()[0][3:], ("", ""))

    def test_pontuacao_isolada_no_cpf_exige_correcao(self):
        self.criar_cliente()
        saida = self.executar(
            "admin\nadmin123\n3\n1\n\n-\n52998224725\n\n\n0\n"
        )
        self.assertIn("CPF inválido.", saida)
        self.assertEqual(clientes.listar_clientes()[0][2:],
                         ("52998224725", "ana@example.com", "111"))

    def test_exclusao_identifica_nome_e_cpf(self):
        self.criar_cliente()
        saida = self.executar("admin\nadmin123\n4\n1\nn\n0\n")
        self.assertIn("Nome: Ana", saida)
        self.assertIn("CPF: 529.982.247-25", saida)
        self.assertEqual(len(clientes.listar_clientes()), 1)

    def test_exclusao_aceita_sim_por_extenso(self):
        self.criar_cliente()
        saida = self.executar("admin\nadmin123\n4\n1\n SIM \n0\n")
        self.assertIn("Cliente excluído com sucesso!", saida)
        self.assertEqual(clientes.listar_clientes(), [])

    def test_confirmacao_invalida_pede_nova_resposta(self):
        self.criar_cliente()
        saida = self.executar("admin\nadmin123\n4\n1\ntalvez\nsim\n0\n")
        self.assertIn("Resposta inválida", saida)
        self.assertEqual(saida.count("Tem certeza que deseja excluir"), 2)
        self.assertEqual(clientes.listar_clientes(), [])

    def test_enter_na_confirmacao_cancela_exclusao(self):
        self.criar_cliente()
        saida = self.executar("admin\nadmin123\n4\n1\n\n0\n")
        self.assertIn("Exclusão cancelada.", saida)
        self.assertEqual(len(clientes.listar_clientes()), 1)

    def test_id_invalido_pode_ser_corrigido_sem_sair_da_edicao(self):
        self.criar_cliente()
        saida = self.executar(
            "admin\nadmin123\n3\nabc\n999\n1\nAna Silva\n\n\n\n0\n"
        )
        self.assertIn("ID numérico", saida)
        self.assertIn("nenhum cliente encontrado com o ID 999", saida)
        self.assertEqual(saida.count("=== MENU ==="), 2)
        self.assertEqual(clientes.listar_clientes()[0][1], "Ana Silva")

    def test_id_invalido_pode_ser_corrigido_na_exclusao(self):
        self.criar_cliente()
        saida = self.executar("admin\nadmin123\n4\nabc\n999\n1\ns\n0\n")
        self.assertIn("ID numérico", saida)
        self.assertIn("nenhum cliente encontrado com o ID 999", saida)
        self.assertEqual(clientes.listar_clientes(), [])

    def test_edicao_sem_mudancas_nao_executa_update(self):
        self.criar_cliente()
        database.executar("CREATE TABLE auditoria (id INTEGER)")
        database.executar("""
            CREATE TRIGGER registrar_edicao AFTER UPDATE ON clientes
            BEGIN INSERT INTO auditoria VALUES (NEW.id); END
        """)
        saida = self.executar("admin\nadmin123\n3\n1\n\n\n\n\n0\n")
        self.assertIn("Nenhuma alteração realizada.", saida)
        self.assertNotIn("Cliente atualizado com sucesso!", saida)
        self.assertEqual(database.consultar("SELECT * FROM auditoria"), [])

    def test_atualizacao_identifica_o_cliente(self):
        self.criar_cliente()
        saida = self.executar("admin\nadmin123\n3\n1\nAna Silva\n\n\n\n0\n")
        self.assertIn("Cliente atualizado com sucesso!", saida)
        self.assertIn("ID: 1 | Nome: Ana Silva", saida)
        self.assertEqual(clientes.listar_clientes()[0][1], "Ana Silva")

    def test_fim_da_entrada_no_cadastro_encerra_sem_gravar(self):
        saida = self.executar("admin\nadmin123\n1\nAna\n")
        self.assertIn("Entrada interrompida", saida)
        self.assertEqual(clientes.listar_clientes(), [])

    def test_fim_da_entrada_no_login_encerra_com_mensagem(self):
        saida = self.executar("")
        self.assertIn("Entrada interrompida", saida)

    def test_ctrl_c_encerra_com_mensagem(self):
        saida = io.StringIO()
        with patch("builtins.input", side_effect=KeyboardInterrupt), redirect_stdout(saida):
            try:
                main.iniciar()
            except KeyboardInterrupt:
                self.fail("Ctrl+C deve ser tratado com uma mensagem ao usuário.")
        self.assertIn("Entrada interrompida", saida.getvalue())

    def test_banco_inacessivel_mostra_orientacao_e_codigo_de_erro(self):
        caminho = self.pasta / "pasta-inexistente" / "banco.db"
        saida = self.executar("", banco=caminho, codigo=1)
        self.assertIn("Não foi possível acessar o banco", saida)
        self.assertIn("permissões", saida)

    def test_erro_ao_gravar_volta_ao_menu_sem_anunciar_sucesso(self):
        database.executar("""
            CREATE TRIGGER bloquear_cadastro BEFORE INSERT ON clientes
            BEGIN SELECT RAISE(ABORT, 'gravação indisponível'); END
        """)
        saida = self.executar("admin\nadmin123\n1\nAna\n52998224725\n\n\n0\n")
        self.assertIn("Não foi possível concluir a operação", saida)
        self.assertNotIn("Cliente cadastrado com sucesso!", saida)
        self.assertEqual(saida.count("=== MENU ==="), 2)
        self.assertEqual(clientes.listar_clientes(), [])

    def test_busca_no_menu_filtra_por_nome(self):
        self.criar_cliente()
        clientes.cadastrar_cliente("Bruno", "11144477735", "bruno@example.com", "222")
        saida = self.executar("admin\nadmin123\n5\nana\n0\n")
        self.assertIn("5 - Buscar clientes", saida)
        self.assertIn("ana@example.com", saida)
        self.assertNotIn("bruno@example.com", saida)

    def test_listagem_no_menu_tem_proxima_e_anterior(self):
        for numero in range(1, 12):
            database.executar(
                "INSERT INTO clientes (nome, cpf) VALUES (?, ?)",
                (f"Cliente {numero:02}", str(numero).zfill(11)),
            )
        saida = self.executar("admin\nadmin123\n2\np\na\n0\n0\n")
        self.assertIn("Página 1 de 2", saida)
        self.assertIn("Página 2 de 2", saida)
        self.assertIn("Cliente 11", saida)

    def test_busca_ajuda_a_escolher_cliente_na_edicao(self):
        self.criar_cliente()
        clientes.cadastrar_cliente("Bruno", "11144477735", "bruno@example.com", "222")
        saida = self.executar(
            "admin\nadmin123\n3\nb\nbruno\n2\nBruno Silva\n\n\n\n0\n"
        )
        self.assertIn("Cliente atualizado com sucesso!", saida)
        self.assertEqual(clientes.listar_clientes()[1][1], "Bruno Silva")

    def programa_no_terminal(self):
        """Aponta o programa real para o banco temporário e confere a restauração."""
        return f"""
import termios
import database
import main
database.DB_PATH = {str(self.banco)!r}
original = termios.tcgetattr(0)
codigo = main.iniciar()
print('RESTAURADO:' + str(original == termios.tcgetattr(0)), flush=True)
raise SystemExit(codigo)
"""

    @unittest.skipUnless(pty is not None and termios is not None, "Plataforma sem PTY POSIX")
    def test_cpf_formatado_durante_cadastro_no_programa_completo(self):
        with terminal_cpf(self.programa_no_terminal(), "Usuário: ".encode()) as terminal:
            terminal.enviar(b"admin\nadmin123\n1\nAna\n")
            terminal.aguardar("CPF (com ou sem pontuação): ".encode())
            terminal.enviar(b"5299")
            terminal.aguardar(b"529.9")
            terminal.enviar(b"8224725")
            terminal.aguardar(b"529.982.247-25")
            terminal.enviar(b"\r")
            terminal.aguardar(b"Email (opcional; Enter para pular): ")
            terminal.enviar(b"\n")
            terminal.aguardar(b"Telefone (opcional; Enter para pular): ")
            terminal.enviar(b"\n0\n")
            terminal.aguardar(b"Saindo...")
            terminal.aguardar(b"RESTAURADO:True")
            self.assertEqual(terminal.processo.wait(timeout=3), 0)
        self.assertEqual(clientes.listar_clientes()[0][1:], ("Ana", "52998224725", "", ""))

    @unittest.skipUnless(pty is not None and termios is not None, "Plataforma sem PTY POSIX")
    def test_interromper_cpf_no_programa_completo_preserva_banco_e_terminal(self):
        for tecla in (b"\x03", b"\x04"):
            with self.subTest(tecla=tecla):
                with terminal_cpf(self.programa_no_terminal(), "Usuário: ".encode()) as terminal:
                    terminal.enviar(b"admin\nadmin123\n1\nAna\n")
                    terminal.aguardar("CPF (com ou sem pontuação): ".encode())
                    terminal.enviar(b"529" + tecla)
                    terminal.aguardar(b"Entrada interrompida")
                    terminal.aguardar(b"RESTAURADO:True")
                    self.assertEqual(terminal.processo.wait(timeout=3), 0)
                self.assertEqual(clientes.listar_clientes(), [])


if __name__ == "__main__":
    unittest.main()
