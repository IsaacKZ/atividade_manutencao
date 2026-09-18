from database import conectar # IMPORTA DO OUTRO ARQUIVO PYTHON, PARA FACILITAR MANUTENÇÃO


def validar_cpf(cpf):
    return cpf.isdigit() and len(cpf) == 11


def cpf_ja_cadastrado(cpf):
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("SELECT 1 FROM clientes WHERE cpf = ?", (cpf,))
    existe = cursor.fetchone() is not None
    conexao.close()
    return existe


def cliente_existe(id_cliente):
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("SELECT 1 FROM clientes WHERE id = ?", (id_cliente,))
    existe = cursor.fetchone() is not None
    conexao.close()
    return existe


def cadastrar_cliente(nome, cpf, email, telefone):
    if not nome.strip():
        raise ValueError("o nome não pode ficar vazio.")
    if not validar_cpf(cpf):
        raise ValueError("CPF inválido. Informe 11 dígitos numéricos.")
    if cpf_ja_cadastrado(cpf):
        raise ValueError("já existe um cliente cadastrado com esse CPF.")

    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute(
        "INSERT INTO clientes (nome, cpf, email, telefone) VALUES (?, ?, ?, ?)",
        (nome, cpf, email, telefone),
    )
    conexao.commit()
    conexao.close()


def listar_clientes():
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("SELECT id, nome, cpf, email, telefone FROM clientes")
    clientes = cursor.fetchall()
    conexao.close()
    return clientes


def editar_cliente(id_cliente, nome, cpf, email, telefone):
    if not cliente_existe(id_cliente):
        return False

    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute(
        "UPDATE clientes SET nome=?, cpf=?, email=?, telefone=? WHERE id=?",
        (nome, cpf, email, telefone, id_cliente),
    )
    conexao.commit()
    conexao.close()
    return True


def excluir_cliente(id_cliente):
    if not cliente_existe(id_cliente):
        return False

    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("DELETE FROM clientes WHERE id=?", (id_cliente,))
    conexao.commit()
    conexao.close()
    return True