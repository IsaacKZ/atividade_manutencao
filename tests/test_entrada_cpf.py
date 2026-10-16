"""Máscara de CPF, entradas preservadas e leitura em um terminal real."""

from contextlib import contextmanager, redirect_stdout
import importlib
import io
import os
from pathlib import Path
import select
import subprocess
import sys
import time
import unittest
from unittest.mock import patch

try:
    import pty
    import termios
except ImportError:
    pty = termios = None


class FormatarCPFTest(unittest.TestCase):
    def test_modulo_de_entrada_expoe_a_mascara(self):
        self.assertIsNotNone(importlib.util.find_spec("entrada_cpf"))
        entrada = importlib.import_module("entrada_cpf")
        self.assertEqual(entrada.formatar_cpf("52998224725"), "529.982.247-25")

    def test_formata_cada_etapa_sem_pontuacao_sobrando(self):
        from entrada_cpf import formatar_cpf

        etapas = (
            "", "5", "52", "529", "529.9", "529.98", "529.982",
            "529.982.2", "529.982.24", "529.982.247", "529.982.247-2",
            "529.982.247-25",
        )
        for tamanho, esperado in enumerate(etapas):
            with self.subTest(tamanho=tamanho):
                self.assertEqual(formatar_cpf("52998224725"[:tamanho]), esperado)

    def test_preserva_cpf_ja_formatado_e_zeros_iniciais(self):
        from entrada_cpf import formatar_cpf

        for valor in ("529.9", "529.982.247-25", "012.345.678-90"):
            with self.subTest(valor=valor):
                self.assertEqual(formatar_cpf(valor), valor)
        self.assertEqual(formatar_cpf("01234567890"), "012.345.678-90")

    def test_completa_a_mascara_quando_so_parte_da_pontuacao_foi_digitada(self):
        from entrada_cpf import formatar_cpf

        for valor in ("529.98224725", "529982.24725", "529982247-25"):
            with self.subTest(valor=valor):
                self.assertEqual(formatar_cpf(valor), "529.982.247-25")
        self.assertEqual(formatar_cpf("529."), "529.")

    def test_nao_remove_caracteres_invalidos_nem_trunca_excesso(self):
        from entrada_cpf import formatar_cpf

        for valor in (
            "-", "...", "52998224725a", "529982247250", "529.982.247-250",
            "52..998224725", " 52998224725 ", "５２９９８２２４７２５", "²" * 11,
        ):
            with self.subTest(valor=valor):
                self.assertEqual(formatar_cpf(valor), valor)


class EntradaSemTerminalTest(unittest.TestCase):
    def test_pipe_usa_input_e_preserva_a_entrada_original(self):
        from entrada_cpf import ler_cpf

        for valor in ("", "-", "...", "52998224725", "529.982.247-25", " erro "):
            with self.subTest(valor=valor):
                saida = io.StringIO()
                with patch("sys.stdin", io.StringIO(valor + "\n")), redirect_stdout(saida):
                    self.assertEqual(ler_cpf("CPF: "), valor)
                self.assertEqual(saida.getvalue(), "CPF: ")

    def test_fim_do_pipe_propaga_eof(self):
        from entrada_cpf import ler_cpf

        with patch("sys.stdin", io.StringIO()), redirect_stdout(io.StringIO()):
            with self.assertRaises(EOFError):
                ler_cpf("CPF: ")


PROGRAMA_PTY = """
import termios
from entrada_cpf import ler_cpf
original = termios.tcgetattr(0)
try:
    valor = ler_cpf('CPF: ')
except (KeyboardInterrupt, EOFError) as erro:
    print('EXCECAO:' + type(erro).__name__, flush=True)
else:
    print('VALOR:' + repr(valor), flush=True)
print('RESTAURADO:' + str(original == termios.tcgetattr(0)), flush=True)
"""


class TerminalDeTeste:
    """Executa uma leitura isolada com prazo e limpeza mesmo se o teste falhar."""

    def __init__(self, descritor, processo):
        self.descritor = descritor
        self.processo = processo
        self.saida = b""

    def enviar(self, valor):
        os.write(self.descritor, valor)

    def aguardar(self, trecho, prazo=3):
        fim = time.monotonic() + prazo
        while trecho not in self.saida:
            restante = fim - time.monotonic()
            if restante <= 0 or not select.select([self.descritor], [], [], restante)[0]:
                raise AssertionError(f"Não apareceu {trecho!r}; saída: {self.saida!r}")
            try:
                recebido = os.read(self.descritor, 65536)
            except OSError as erro:
                raise AssertionError(f"Terminal encerrado; saída: {self.saida!r}") from erro
            if not recebido:
                raise AssertionError(f"Terminal sem dados; saída: {self.saida!r}")
            self.saida += recebido
        return self.saida


@contextmanager
def terminal_cpf(programa=PROGRAMA_PTY, pronto=b"CPF: "):
    """Abre o PTY e encerra o processo filho ao sair do teste."""
    mestre, escravo = pty.openpty()
    processo = None
    try:
        ambiente = dict(os.environ, TERM="xterm", PYTHONIOENCODING="utf-8")
        processo = subprocess.Popen(
            [sys.executable, "-B", "-c", programa],
            cwd=Path(__file__).resolve().parents[1], env=ambiente,
            stdin=escravo, stdout=escravo, stderr=escravo,
        )
        os.close(escravo)
        escravo = None
        terminal = TerminalDeTeste(mestre, processo)
        terminal.aguardar(pronto)
        yield terminal
    finally:
        if processo is not None:
            if processo.poll() is None:
                processo.kill()
            processo.wait(timeout=3)
        os.close(mestre)
        if escravo is not None:
            os.close(escravo)


@unittest.skipUnless(pty is not None and termios is not None, "Plataforma sem PTY POSIX")
class EntradaTerminalTest(unittest.TestCase):
    def test_mascara_aparece_antes_do_enter_e_restaura_terminal(self):
        with terminal_cpf() as terminal:
            terminal.enviar(b"5299")
            terminal.aguardar(b"529.9")
            self.assertIsNone(terminal.processo.poll())
            atributos = termios.tcgetattr(terminal.descritor)
            self.assertFalse(atributos[3] & termios.ICANON)
            self.assertFalse(atributos[3] & termios.ECHO)
            terminal.enviar(b"8224725\r")
            terminal.aguardar(b"VALOR:'52998224725'")
            terminal.aguardar(b"RESTAURADO:True")
            self.assertEqual(terminal.processo.wait(timeout=3), 0)

    def test_cola_com_ou_sem_pontuacao(self):
        for valor in (b"52998224725", b"529.982.247-25"):
            with self.subTest(valor=valor), terminal_cpf() as terminal:
                terminal.enviar(valor)
                terminal.aguardar(b"529.982.247-25")
                terminal.enviar(b"\r")
                terminal.aguardar(b"VALOR:" + repr(valor.decode()).encode())
                terminal.aguardar(b"RESTAURADO:True")

    def test_backspace_apaga_ultimo_caractere_e_ctrl_u_limpa(self):
        with terminal_cpf() as terminal:
            terminal.enviar(b"5299\x7f8")
            terminal.aguardar(b"529.8")
            terminal.enviar(b"\x1552998224725\r")
            terminal.aguardar(b"VALOR:'52998224725'")
            terminal.aguardar(b"RESTAURADO:True")

    def test_pontuacao_isolada_nao_vira_enter(self):
        for valor in (b"", b"-", b"..."):
            with self.subTest(valor=valor), terminal_cpf() as terminal:
                terminal.enviar(valor + b"\r")
                terminal.aguardar(b"VALOR:" + repr(valor.decode()).encode())
                terminal.aguardar(b"RESTAURADO:True")

    def test_letras_unicode_e_excesso_nao_sao_filtrados(self):
        for valor in ("52998224725a", "529982247250", "52998224725é", "５２９"):
            with self.subTest(valor=valor), terminal_cpf() as terminal:
                terminal.enviar(valor.encode() + b"\r")
                terminal.aguardar(("VALOR:" + repr(valor)).encode())
                terminal.aguardar(b"RESTAURADO:True")

    def test_tab_e_letra_apos_escape_nao_transformam_entrada_invalida_em_cpf(self):
        for dados, esperado in (
            (b"52998224725\t", "52998224725\t"),
            (b"52998224725\x1ba", "52998224725a"),
            (b"52998224725\xc3", "52998224725\ufffd"),
            ("52998224725\u200b".encode(), "52998224725\u200b"),
            (b"5299822472\x1b5", "52998224725"),
        ):
            with self.subTest(dados=dados), terminal_cpf() as terminal:
                terminal.enviar(dados + b"\r")
                terminal.aguardar(("VALOR:" + repr(esperado)).encode())
                terminal.aguardar(b"RESTAURADO:True")

    def test_setas_e_marcadores_de_colagem_nao_viram_dados(self):
        with terminal_cpf() as terminal:
            terminal.enviar(b"\x1b[A\x1b[B\x1b[C\x1b[D\x1b[200~52998224725\x1b[201~\r")
            terminal.aguardar(b"VALOR:'52998224725'")
            terminal.aguardar(b"RESTAURADO:True")

    def test_ctrl_c_e_ctrl_d_propagam_e_restauram_terminal(self):
        for tecla, excecao in (
            (b"\x03", b"KeyboardInterrupt"), (b"\x04", b"EOFError"),
            (b"\x1b[\x03", b"KeyboardInterrupt"), (b"\x1b[\x04", b"EOFError"),
        ):
            with self.subTest(tecla=tecla), terminal_cpf() as terminal:
                terminal.enviar(b"529" + tecla)
                terminal.aguardar(b"EXCECAO:" + excecao)
                terminal.aguardar(b"RESTAURADO:True")

    def test_mudanca_de_modo_preserva_cpf_que_ja_chegou_ao_terminal(self):
        programa = """
import select
import termios
import tty
setraw_original = tty.setraw
def aguardar_fila(descritor, when=termios.TCSAFLUSH):
    print('FILA:', flush=True)
    assert select.select([descritor], [], [], 3)[0]
    setraw_original(descritor, when)
tty.setraw = aguardar_fila
""" + PROGRAMA_PTY
        with terminal_cpf(programa, b"FILA:") as terminal:
            terminal.enviar(b"52998224725\n")
            terminal.aguardar(b"VALOR:'52998224725'")
            terminal.aguardar(b"RESTAURADO:True")


if __name__ == "__main__":
    unittest.main()
