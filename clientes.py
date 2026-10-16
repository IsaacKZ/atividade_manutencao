"""Cadastro, consulta, edição e exclusão de clientes."""

from database import consultar, executar


def normalizar_cpf(cpf):
    """Retira espaços externos, pontos e hífen antes de salvar."""
    return cpf.strip().replace(".", "").replace("-", "")


def cpf_ja_cadastrado(cpf, id_cliente=None):
    """Compara CPFs normalizados, ignorando o próprio ID durante a edição."""
    cpf = normalizar_cpf(cpf)
    if id_cliente is None:
        clientes = consultar("SELECT cpf FROM clientes")
    else:
        # Na edição, o cliente pode manter o próprio CPF.
        clientes = consultar("SELECT cpf FROM clientes WHERE id != ?", (id_cliente,))
    for (cpf_salvo,) in clientes:
        if cpf_salvo is not None and normalizar_cpf(cpf_salvo) == cpf:
            return True
    return False


def cliente_existe(id_cliente):
    """Retorna True se há um cliente com o ID informado."""
    clientes = consultar("SELECT id FROM clientes WHERE id = ?", (id_cliente,))
    return bool(clientes)


def buscar_cliente(id_cliente):
    """Retorna (id, nome, cpf, email, telefone), ou None se o ID não existir."""
    clientes = consultar(
        "SELECT id, nome, cpf, email, telefone FROM clientes WHERE id = ?", (id_cliente,)
    )
    if clientes:
        return clientes[0]
    return None


def validar_dados_cliente(nome, cpf, id_cliente=None):
    """Exige nome e CPF preenchidos e impede CPF duplicado."""
    if not nome.strip():
        raise ValueError("o nome não pode ficar vazio.")
    if not normalizar_cpf(cpf):
        raise ValueError("o CPF não pode ficar vazio.")
    if cpf_ja_cadastrado(cpf, id_cliente):
        raise ValueError("já existe um cliente cadastrado com esse CPF.")


def cadastrar_cliente(nome, cpf, email, telefone):
    """Valida e salva o cliente com CPF sem pontuação; não retorna um valor."""
    cpf = normalizar_cpf(cpf)
    validar_dados_cliente(nome, cpf)

    executar(
        "INSERT INTO clientes (nome, cpf, email, telefone) VALUES (?, ?, ?, ?)",
        (nome, cpf, email, telefone),
    )


def listar_clientes():
    """Retorna uma lista de tuplas (id, nome, cpf, email, telefone)."""
    return consultar("SELECT id, nome, cpf, email, telefone FROM clientes")


def editar_cliente(id_cliente, nome, cpf, email, telefone):
    """Valida e atualiza o cliente; retorna False se o ID não existir."""
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
    """Exclui pelo ID e retorna True somente se um registro for removido."""
    excluidos = executar("DELETE FROM clientes WHERE id = ?", (id_cliente,))
    return excluidos > 0
