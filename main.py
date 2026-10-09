from auth import login
from clientes import (
    cadastrar_cliente,
    editar_cliente,
    excluir_cliente,
    listar_clientes,
)
from database import inicializar_banco

LARGURA_ID = 4
LARGURA_NOME = 20
LARGURA_CPF = 15
LARGURA_EMAIL = 25
LARGURA_TELEFONE = 15


def tela_login():
    print("=== LOGIN ===")
    username = input("Usuário: ")
    senha = input("Senha: ")
    if login(username, senha):
        print(f"\nBem-vindo, {username}!\n")
        return True
    print("\nUsuário ou senha inválidos.\n")
    return False


def formatar_linha(id_cliente, nome, cpf, email, telefone):
    return (
        f"{id_cliente:<{LARGURA_ID}}"
        f"{nome:<{LARGURA_NOME}}"
        f"{cpf:<{LARGURA_CPF}}"
        f"{email:<{LARGURA_EMAIL}}"
        f"{telefone:<{LARGURA_TELEFONE}}"
    )


def exibir_clientes():
    clientes = listar_clientes()
    if not clientes:
        print("Nenhum cliente cadastrado.")
        return

    print(formatar_linha("ID", "Nome", "CPF", "Email", "Telefone"))
    for id_cliente, nome, cpf, email, telefone in clientes:
        print(formatar_linha(id_cliente, nome, cpf, email, telefone))


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
    exibir_clientes()
    id_cliente = input("ID do cliente a editar: ")
    nome, cpf, email, telefone = ler_dados_cliente(edicao=True)
    try:
        if editar_cliente(id_cliente, nome, cpf, email, telefone):
            print("Cliente atualizado com sucesso!")
        else:
            print(f"Erro: nenhum cliente encontrado com o ID {id_cliente}.")
    except ValueError as erro:
        print(f"Erro ao editar cliente: {erro}")


def excluir_pelo_menu():
    exibir_clientes()
    id_cliente = input("ID do cliente a excluir: ")
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
    inicializar_banco()
    while not tela_login():
        pass
    menu_principal()


if __name__ == "__main__":
    iniciar()
