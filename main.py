from auth import login
from clientes import (
    cadastrar_cliente,
    cliente_existe,
    editar_cliente,
    excluir_cliente,
    listar_clientes,
)
from database import inicializar_banco

def tela_login():
    """Pede o usuário e a senha para entrar no menu."""
    print("=== LOGIN ===")
    username = input("Usuário: ")
    senha = input("Senha: ")
    if login(username, senha):
        print(f"\nBem-vindo, {username}!\n")
        return True
    print("\nUsuário ou senha inválidos.\n")
    return False


def exibir_clientes():
    """Lista uma vez e informa se há clientes para continuar uma ação."""
    clientes = listar_clientes()
    if not clientes:
        print("Nenhum cliente cadastrado.")
        return False

    print("ID | Nome | CPF | Email | Telefone")
    for id_cliente, nome, cpf, email, telefone in clientes:
        print(id_cliente, nome or "", cpf or "", email or "", telefone or "", sep=" | ")
    return True


def ler_dados_cliente(edicao=False):
    nome = input("Novo nome: " if edicao else "Nome: ")
    cpf = input("Novo CPF: " if edicao else "CPF: ")
    email = input("Novo email: " if edicao else "Email: ")
    telefone = input("Novo telefone: " if edicao else "Telefone: ")
    return nome, cpf, email, telefone


def cadastrar_pelo_menu():
    nome, cpf, email, telefone = ler_dados_cliente()
    try:
        cadastrar_cliente(nome, cpf, email, telefone)
        print("Cliente cadastrado com sucesso!")
    except ValueError as erro:
        print(f"Erro ao cadastrar cliente: {erro}")


def editar_pelo_menu():
    """Só solicita novos dados se houver clientes e o ID informado existir."""
    if not exibir_clientes():
        return
    id_cliente = input("ID do cliente a editar: ")
    if not cliente_existe(id_cliente):
        print(f"Erro: nenhum cliente encontrado com o ID {id_cliente}.")
        return
    nome, cpf, email, telefone = ler_dados_cliente(edicao=True)
    try:
        if editar_cliente(id_cliente, nome, cpf, email, telefone):
            print("Cliente atualizado com sucesso!")
        else:
            print(f"Erro: nenhum cliente encontrado com o ID {id_cliente}.")
    except ValueError as erro:
        print(f"Erro ao editar cliente: {erro}")


def excluir_pelo_menu():
    if not exibir_clientes():
        return
    id_cliente = input("ID do cliente a excluir: ")
    if not cliente_existe(id_cliente):
        print(f"Erro: nenhum cliente encontrado com o ID {id_cliente}.")
        return
    confirmacao = input(
        f"Tem certeza que deseja excluir o cliente {id_cliente}? (s/n): "
    )
    if confirmacao.strip().lower() != "s":
        print("Exclusão cancelada.")
    elif excluir_cliente(id_cliente):
        print("Cliente excluído com sucesso!")
    else:
        print(f"Erro: nenhum cliente encontrado com o ID {id_cliente}.")


def menu_principal():
    while True:
        print("\n=== MENU ===")
        print("1 - Cadastrar cliente")
        print("2 - Listar clientes")
        print("3 - Editar cliente")
        print("4 - Excluir cliente")
        print("0 - Sair")
        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            cadastrar_pelo_menu()
        elif opcao == "2":
            exibir_clientes()
        elif opcao == "3":
            editar_pelo_menu()
        elif opcao == "4":
            excluir_pelo_menu()
        elif opcao == "0":
            print("Saindo...")
            break
        else:
            print("Opção inválida.")


def iniciar():
    """Prepara o banco e apresenta o login e o menu."""
    inicializar_banco()
    while not tela_login():
        pass
    menu_principal()


if __name__ == "__main__":
    iniciar()
