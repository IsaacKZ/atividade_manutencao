from database import consultar, executar


def normalizar_cpf(cpf):
    """Retira espaços externos, pontos e hífen antes de validar e salvar."""
    return cpf.strip().replace(".", "").replace("-", "")


def validar_cpf(cpf):
    """Confere os 11 dígitos e calcula os dois verificadores do CPF."""
    cpf = normalizar_cpf(cpf)
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
    cpf = normalizar_cpf(cpf)
    if id_cliente is None:
        clientes = consultar("SELECT id FROM clientes WHERE cpf = ?", (cpf,))
    else:
        # Na edição, o cliente pode manter o próprio CPF.
        clientes = consultar(
            "SELECT id FROM clientes WHERE cpf = ? AND id != ?", (cpf, id_cliente)
        )
    return len(clientes) > 0


def cliente_existe(id_cliente):
    clientes = consultar("SELECT id FROM clientes WHERE id = ?", (id_cliente,))
    return len(clientes) > 0


def buscar_cliente(id_cliente):
    """Devolve os dados atuais para preencher a edição."""
    clientes = consultar(
        "SELECT id, nome, cpf, email, telefone FROM clientes WHERE id = ?", (id_cliente,)
    )
    if clientes:
        return clientes[0]
    return None


def validar_dados_cliente(nome, cpf, id_cliente=None):
    """Aplica as mesmas regras no cadastro e na edição, sem gravar dados."""
    if not nome.strip():
        raise ValueError("o nome não pode ficar vazio.")
    if not validar_cpf(cpf):
        raise ValueError("CPF inválido. Informe um CPF com 11 dígitos e verificadores corretos.")
    if cpf_ja_cadastrado(cpf, id_cliente):
        raise ValueError("já existe um cliente cadastrado com esse CPF.")


def cadastrar_cliente(nome, cpf, email, telefone):
    cpf = normalizar_cpf(cpf)
    validar_dados_cliente(nome, cpf)

    executar(
        "INSERT INTO clientes (nome, cpf, email, telefone) VALUES (?, ?, ?, ?)",
        (nome, cpf, email, telefone),
    )


def listar_clientes():
    return consultar("SELECT id, nome, cpf, email, telefone FROM clientes")


def editar_cliente(id_cliente, nome, cpf, email, telefone):
    if not cliente_existe(id_cliente):
        return False
    cpf = normalizar_cpf(cpf)
    validar_dados_cliente(nome, cpf, id_cliente)

    alterados = executar(
        "UPDATE clientes SET nome=?, cpf=?, email=?, telefone=? WHERE id=?",
        (nome, cpf, email, telefone, id_cliente),
    )
    return alterados > 0


def excluir_cliente(id_cliente):
    excluidos = executar("DELETE FROM clientes WHERE id = ?", (id_cliente,))
    return excluidos > 0
