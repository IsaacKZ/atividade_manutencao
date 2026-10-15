from contextlib import closing
import hashlib
import hmac
import secrets
import sqlite3

from database import conectar

ITERACOES = 600000
PREFIXO_HASH = "pbkdf2_sha256$"


def _validar_nova_senha(senha):
    """Evita senhas vazias, curtas ou iguais à antiga senha padrão."""
    if not senha.strip():
        raise ValueError("Senha é obrigatória.")
    if len(senha) < 8:
        raise ValueError("A senha deve ter pelo menos 8 caracteres.")
    if senha == "admin123":
        raise ValueError("Escolha uma senha diferente da antiga senha padrão.")


def _criar_hash(senha):
    """Protege a senha com PBKDF2 e um salt aleatório para cada cadastro."""
    salt = secrets.token_bytes(16)
    resumo = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), salt, ITERACOES)
    return f"{PREFIXO_HASH}{ITERACOES}${salt.hex()}${resumo.hex()}"


def _senha_confere(senha, senha_salva):
    """Confere hashes atuais ou senhas antigas ainda não migradas."""
    if not senha_salva.startswith(PREFIXO_HASH):
        return hmac.compare_digest(senha.encode("utf-8"), senha_salva.encode("utf-8"))

    try:
        algoritmo, iteracoes, salt, resumo_salvo = senha_salva.split("$")
        if algoritmo != "pbkdf2_sha256" or iteracoes != str(ITERACOES):
            return False
        salt = bytes.fromhex(salt)
        resumo_salvo = bytes.fromhex(resumo_salvo)
        if len(salt) != 16 or len(resumo_salvo) != 32:
            return False
    except ValueError:
        return False

    resumo = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), salt, ITERACOES)
    return hmac.compare_digest(resumo, resumo_salvo)


def existe_usuario():
    """Indica se já há uma conta para usar no login."""
    with closing(conectar()) as conexao:
        return conexao.execute("SELECT 1 FROM usuarios LIMIT 1").fetchone() is not None


def cadastrar_usuario(username, senha):
    """Cadastra uma conta com senha protegida e nome de usuário único."""
    username = username.strip()
    if not username:
        raise ValueError("Nome de usuário é obrigatório.")
    _validar_nova_senha(senha)

    with closing(conectar()) as conexao:
        try:
            conexao.execute(
                "INSERT INTO usuarios (username, senha) VALUES (?, ?)",
                (username, _criar_hash(senha)),
            )
            conexao.commit()
        except sqlite3.IntegrityError:
            raise ValueError("Nome de usuário já cadastrado.") from None


def login(username, senha):
    """Autentica e migra a senha antiga somente após um login correto."""
    with closing(conectar()) as conexao:
        usuario = conexao.execute(
            "SELECT senha FROM usuarios WHERE username = ?", (username,)
        ).fetchone()
        if usuario is None or not _senha_confere(senha, usuario[0]):
            return False

        if not usuario[0].startswith(PREFIXO_HASH):
            conexao.execute(
                "UPDATE usuarios SET senha = ? WHERE username = ? AND senha = ?",
                (_criar_hash(senha), username, usuario[0]),
            )
            conexao.commit()
        return True


def trocar_senha(username, senha_atual, nova_senha):
    """Troca a senha somente quando a senha atual confere."""
    _validar_nova_senha(nova_senha)
    with closing(conectar()) as conexao:
        usuario = conexao.execute(
            "SELECT senha FROM usuarios WHERE username = ?", (username,)
        ).fetchone()
        if usuario is None or not _senha_confere(senha_atual, usuario[0]):
            return False

        atualizacao = conexao.execute(
            "UPDATE usuarios SET senha = ? WHERE username = ? AND senha = ?",
            (_criar_hash(nova_senha), username, usuario[0]),
        )
        conexao.commit()
        return atualizacao.rowcount > 0
