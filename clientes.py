from database import conectar

def cadastrar_cliente(nome, cpf, email, telefone): # ERRO 1: ENTRADA SEM VALIDAÇÃO
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


def editar_cliente(id_cliente, nome, cpf, email, telefone): # ERRO 2: MESMO SE O ID NÃO EXISTIR, O UPDATE/DELETE DA "SUCESSO"
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute(
        "UPDATE clientes SET nome=?, cpf=?, email=?, telefone=? WHERE id=?",
        (nome, cpf, email, telefone, id_cliente),
    )
    conexao.commit()
    conexao.close()


def excluir_cliente(id_cliente): # ERRO 3: SEM CONFIRMAÇÃO DE EXCLUSÃO - ERRO DE USABILIDADE    
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("DELETE FROM clientes WHERE id=?", (id_cliente,))
    conexao.commit()
    conexao.close()
