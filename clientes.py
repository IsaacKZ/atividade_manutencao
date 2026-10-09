from contextlib import closing

from database import conectar


def validar_cpf(cpf):
    return cpf.isdigit() and len(cpf) == 11


def cpf_ja_cadastrado(cpf, id_cliente=None):
    with closing(conectar()) as conexao:
        if id_cliente is None:
            resultado = conexao.execute(
                "SELECT 1 FROM clientes WHERE cpf = ?", (cpf,)
            )
        else:
            # Na edição, o cliente pode manter o próprio CPF.
            resultado = conexao.execute(
                "SELECT 1 FROM clientes WHERE cpf = ? AND id != ?",
                (cpf, id_cliente),
            )
        return resultado.fetchone() is not None


def cliente_existe(id_cliente):
    with closing(conectar()) as conexao:
        resultado = conexao.execute(
            "SELECT 1 FROM clientes WHERE id = ?", (id_cliente,)
        )
        return resultado.fetchone() is not None


def validar_dados_cliente(nome, cpf, id_cliente=None):
    if not nome.strip():
        raise ValueError("o nome não pode ficar vazio.")
    if not validar_cpf(cpf):
        raise ValueError("CPF inválido. Informe 11 dígitos numéricos.")
    if cpf_ja_cadastrado(cpf, id_cliente):
        raise ValueError("já existe um cliente cadastrado com esse CPF.")


def cadastrar_cliente(nome, cpf, email, telefone):
    validar_dados_cliente(nome, cpf)

    with closing(conectar()) as conexao:
        conexao.execute(
            "INSERT INTO clientes (nome, cpf, email, telefone) VALUES (?, ?, ?, ?)",
            (nome, cpf, email, telefone),
        )
        conexao.commit()


def listar_clientes():
    with closing(conectar()) as conexao:
        return conexao.execute(
            "SELECT id, nome, cpf, email, telefone FROM clientes"
        ).fetchall()


def editar_cliente(id_cliente, nome, cpf, email, telefone):
    if not cliente_existe(id_cliente):
        return False
    validar_dados_cliente(nome, cpf, id_cliente)

    with closing(conectar()) as conexao:
        conexao.execute(
            "UPDATE clientes SET nome=?, cpf=?, email=?, telefone=? WHERE id=?",
            (nome, cpf, email, telefone, id_cliente),
        )
        conexao.commit()
    return True


def excluir_cliente(id_cliente):
    if not cliente_existe(id_cliente):
        return False

    with closing(conectar()) as conexao:
        conexao.execute("DELETE FROM clientes WHERE id=?", (id_cliente,))
        conexao.commit()
    return True
