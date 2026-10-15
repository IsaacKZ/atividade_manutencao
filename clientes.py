from contextlib import closing

from database import conectar


def validar_cpf(cpf):
    """Confere os 11 dígitos e calcula os dois verificadores do CPF."""
    if len(cpf) != 11:
        return False

    # isdigit() também aceita símbolos como ²; aqui só aceitamos de 0 a 9.
    for caractere in cpf:
        if caractere < "0" or caractere > "9":
            return False

    if cpf == cpf[0] * 11:
        return False

    # O primeiro verificador usa os 9 primeiros dígitos; o segundo usa 10.
    for quantidade in (9, 10):
        soma = 0
        peso = quantidade + 1
        for posicao in range(quantidade):
            soma = soma + int(cpf[posicao]) * peso
            peso = peso - 1

        verificador = 11 - (soma % 11)
        if verificador >= 10:
            verificador = 0
        if int(cpf[quantidade]) != verificador:
            return False

    return True


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
    """Aplica as mesmas regras no cadastro e na edição, sem gravar dados."""
    if not nome.strip():
        raise ValueError("o nome não pode ficar vazio.")
    if not validar_cpf(cpf):
        raise ValueError("CPF inválido. Informe 11 dígitos, sem pontuação e com verificadores corretos.")
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
