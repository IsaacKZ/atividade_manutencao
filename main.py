from database import inicializar_banco
from auth import login
from clientes import cadastrar_cliente, listar_clientes, editar_cliente, excluir_cliente


def tela_login():
    print("=== LOGIN ===")
    username = input("Usuário: ")
    senha = input("Senha: ")
    if login(username, senha):
        print(f"\nBem-vindo, {username}!\n")
        return True
    print("\nUsuário ou senha inválidos.\n")
    return False


LARGURA_ID = 4
LARGURA_NOME = 20
LARGURA_CPF = 15
LARGURA_EMAIL = 25
LARGURA_TELEFONE = 15


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
            nome = input("Nome: ")
            cpf = input("CPF: ")
            email = input("Email: ")
            telefone = input("Telefone: ")
            try:
                cadastrar_cliente(nome, cpf, email, telefone)
                print("Cliente cadastrado com sucesso!")
            except ValueError as erro:
                print(f"Erro ao cadastrar cliente: {erro}")

        elif opcao == "2":
            exibir_clientes()

        elif opcao == "3":
            exibir_clientes()
            id_cliente = input("ID do cliente a editar: ")
            nome = input("Novo nome: ")
            cpf = input("Novo CPF: ")
            email = input("Novo email: ")
            telefone = input("Novo telefone: ")
            if editar_cliente(id_cliente, nome, cpf, email, telefone):
                print("Cliente atualizado com sucesso!")
            else:
                print(f"Erro: nenhum cliente encontrado com o ID {id_cliente}.")

        elif opcao == "4":
            exibir_clientes()
            id_cliente = input("ID do cliente a excluir: ")
            confirmacao = input(f"Tem certeza que deseja excluir o cliente {id_cliente}? (s/n): ")
            if confirmacao.strip().lower() != "s":
                print("Exclusão cancelada.")
            elif excluir_cliente(id_cliente):
                print("Cliente excluído com sucesso!")
            else:
                print(f"Erro: nenhum cliente encontrado com o ID {id_cliente}.")

        elif opcao == "0":
            print("Saindo...")
            break

        else:
            print("Opção inválida.")


if __name__ == "__main__":
    inicializar_banco()
    while not tela_login():
        pass
    menu_principal()