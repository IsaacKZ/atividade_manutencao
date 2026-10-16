"""Validação de CPF e operações de cadastro, consulta, edição e exclusão."""

from database import consultar, executar


def normalizar_cpf(cpf):
    """Retira espaços externos, pontos e hífen antes de validar e salvar."""
    return cpf.strip().replace(".", "").replace("-", "")


def validar_cpf(cpf):
    """Confere os 11 dígitos e calcula os dois verificadores do CPF."""
    cpf = normalizar_cpf(cpf)
    if len(cpf) != 11:
        return False

    # A lista explícita impede aceitar símbolos como ² e dígitos Unicode.
    for caractere in cpf:
        if caractere not in "0123456789":
            return False

    if cpf == cpf[0] * 11:
        return False

    # O primeiro verificador usa os 9 primeiros dígitos; o segundo usa 10.
    for quantidade in (9, 10):
        soma = 0
        for posicao in range(quantidade):
            peso = quantidade + 1 - posicao
            soma += int(cpf[posicao]) * peso

        verificador = 11 - (soma % 11)
        if verificador >= 10:
            verificador = 0
        if int(cpf[quantidade]) != verificador:
            return False

    return True


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
    """Lança ValueError para nome vazio, CPF inválido ou CPF duplicado."""
    if not nome.strip():
        raise ValueError("o nome não pode ficar vazio.")
    if not validar_cpf(cpf):
        raise ValueError("CPF inválido. Informe um CPF com 11 dígitos e verificadores corretos.")
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


def pesquisar_clientes(termo):
    """Filtra por parte do nome ou CPF, preservando a ordem da listagem."""
    termo = termo.strip()
    clientes = listar_clientes()
    if not termo:
        return clientes

    nome_procurado = termo.casefold()
    cpf_procurado = normalizar_cpf(termo)
    resultados = []
    for cliente in clientes:
        _, nome, cpf, _, _ = cliente
        nome_confere = nome_procurado in (nome or "").casefold()
        cpf_confere = bool(cpf_procurado) and cpf_procurado in normalizar_cpf(cpf or "")
        if nome_confere or cpf_confere:
            resultados.append(cliente)
    return resultados


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
