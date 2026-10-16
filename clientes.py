from database import consultar, executar


def normalizar_cpf(cpf):
    """Normaliza a apresentação do CPF."""
    return cpf.strip().replace(".", "").replace("-", "")


def validar_cpf(cpf):
    """Confere se o CPF tem 11 dígitos."""
    cpf = normalizar_cpf(cpf)
    return len(cpf) == 11 and cpf.isascii() and cpf.isdigit()


def cpf_ja_cadastrado(cpf, id_cliente=None):
    """Confere se o CPF já pertence a outro cliente."""
    cpf = normalizar_cpf(cpf)
    if id_cliente is None:
        clientes = consultar("SELECT cpf FROM clientes")
    else:
        clientes = consultar("SELECT cpf FROM clientes WHERE id != ?", (id_cliente,))
    for (cpf_salvo,) in clientes:
        if cpf_salvo is not None and normalizar_cpf(cpf_salvo) == cpf:
            return True
    return False


def cliente_existe(id_cliente):
    """Confere se o cliente existe."""
    clientes = consultar("SELECT id FROM clientes WHERE id = ?", (id_cliente,))
    return bool(clientes)


def buscar_cliente(id_cliente):
    """Busca um cliente pelo ID."""
    clientes = consultar(
        "SELECT id, nome, cpf, email, telefone FROM clientes WHERE id = ?", (id_cliente,)
    )
    if clientes:
        return clientes[0]
    return None


def validar_dados_cliente(nome, cpf, id_cliente=None):
    """Confere os campos obrigatórios e a duplicidade do CPF."""
    if not nome.strip():
        raise ValueError("o nome não pode ficar vazio.")
    if not validar_cpf(cpf):
        raise ValueError("o CPF deve conter 11 dígitos.")
    if cpf_ja_cadastrado(cpf, id_cliente):
        raise ValueError("já existe um cliente cadastrado com esse CPF.")


def cadastrar_cliente(nome, cpf, email, telefone):
    """Cadastra um cliente."""
    cpf = normalizar_cpf(cpf)
    validar_dados_cliente(nome, cpf)

    executar(
        "INSERT INTO clientes (nome, cpf, email, telefone) VALUES (?, ?, ?, ?)",
        (nome, cpf, email, telefone),
    )


def listar_clientes():
    """Lista os clientes."""
    return consultar("SELECT id, nome, cpf, email, telefone FROM clientes")


def editar_cliente(id_cliente, nome, cpf, email, telefone):
    """Atualiza os dados de um cliente."""
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
    """Exclui um cliente pelo ID."""
    excluidos = executar("DELETE FROM clientes WHERE id = ?", (id_cliente,))
    return excluidos > 0
