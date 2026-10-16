import codecs
import os
import select
import sys

try:
    import termios
    import tty
except ImportError:
    termios = tty = None


def formatar_cpf(valor: str) -> str:
    """Formata o CPF para exibição."""
    digitos = ""
    for posicao, caractere in enumerate(valor):
        if caractere in "0123456789":
            digitos += caractere
        elif (
            posicao == 0 or valor[posicao - 1] not in "0123456789"
            or {3: ".", 6: ".", 9: "-"}.get(len(digitos)) != caractere
        ):
            return valor
    if len(digitos) > 11:
        return valor
    partes = (digitos[:3], digitos[3:6], digitos[6:9])
    cpf = ".".join(parte for parte in partes if parte)
    if len(digitos) > 9:
        cpf += "-" + digitos[9:]
    return cpf + (valor[-1] if valor.endswith((".", "-")) else "")


def _configuracao_terminal():
    """Obtém as configurações do terminal."""
    if termios is None or not sys.stdin.isatty() or not sys.stdout.isatty():
        return None
    if os.environ.get("TERM") == "dumb":
        return None
    try:
        descritor = sys.stdin.fileno()
        return descritor, termios.tcgetattr(descritor)
    except (AttributeError, OSError, ValueError, termios.error):
        return None


def _ler_escape(descritor):
    """Lê uma tecla especial."""
    if not select.select([descritor], [], [], 0.05)[0]:
        return b""
    inicio = os.read(descritor, 1)
    if inicio not in (b"[", b"O"):
        return inicio
    sequencia = b"\x1b" + inicio
    while select.select([descritor], [], [], 0.05)[0]:
        caractere = os.read(descritor, 1)
        if not caractere or caractere < b" ":
            return caractere
        sequencia += caractere
        if b"@" <= caractere <= b"~":
            return b""
    return sequencia


def _mostrar(pergunta, valor):
    """Exibe o CPF digitado."""
    visivel = "".join(
        caractere if caractere.isprintable() else repr(caractere)[1:-1]
        for caractere in formatar_cpf(valor)
    )
    sys.stdout.write("\r" + pergunta + visivel + "\x1b[K")
    sys.stdout.flush()


def _ler_com_mascara(pergunta, descritor):
    """Lê o CPF com máscara."""
    valor = ""
    decodificar = codecs.getincrementaldecoder(sys.stdin.encoding or "utf-8")("replace")
    sys.stdout.write(pergunta)
    sys.stdout.flush()
    try:
        while True:
            dado = os.read(descritor, 1)
            if dado == b"\x1b":
                dado = _ler_escape(descritor)
                if not dado:
                    continue
            if not dado or dado == b"\x04":
                raise EOFError
            if dado == b"\x03":
                raise KeyboardInterrupt
            for caractere in decodificar.decode(dado):
                if caractere in ("\r", "\n"):
                    return valor
                if caractere in ("\x7f", "\b"):
                    valor = valor[:-1]
                elif caractere == "\x15":
                    valor = ""
                else:
                    valor += caractere
                _mostrar(pergunta, valor)
    finally:
        sys.stdout.write("\r\n")
        sys.stdout.flush()


def ler_cpf(pergunta: str) -> str:
    """Lê o CPF do terminal."""
    configuracao = _configuracao_terminal()
    if configuracao is None:
        return input(pergunta)
    descritor, modo_original = configuracao
    try:
        tty.setraw(descritor, when=termios.TCSANOW)
        return _ler_com_mascara(pergunta, descritor)
    finally:
        termios.tcsetattr(descritor, termios.TCSADRAIN, modo_original)
