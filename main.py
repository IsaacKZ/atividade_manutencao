"""Telas de terminal: login, preenchimento dos dados e menu de clientes."""

import sqlite3

from auth import login
from clientes import (
    cadastrar_cliente,
    editar_cliente,
    excluir_cliente,
    listar_clientes,
    normalizar_cpf,
    validar_dados_cliente,
)
from consulta_clientes import paginar_clientes, selecionar_cliente
from database import inicializar_banco
from entrada_cpf import formatar_cpf, ler_cpf


def tela_login():
    """Pede o usuário e a senha para entrar no menu."""
    print("=== LOGIN ===")
    username = input("Usuário: ").strip()
    senha = input("Senha: ")
    if login(username, senha):
        print(f"\nBem-vindo, {username}!\n")
        return True
    print("\nUsuário ou senha inválidos.\n")
    return False


def exibir_clientes():
    """Lista em páginas de dez e informa se havia clientes."""
    return paginar_clientes(listar_clientes())


def ler_contato(campo, valor_atual="", edicao=False):
    """Lê contato opcional: email exige @ e telefone aceita até 11 dígitos.

    Na edição, Enter mantém e - apaga. A pontuação não conta no limite do telefone.
    """
    pergunta = f"{campo} (opcional; Enter para pular): "
    if edicao:
        pergunta = f"Novo {campo.lower()} [{valor_atual or ''}] (Enter mantém; - apaga): "
    while True:
        valor = input(pergunta).strip()
        if edicao and valor == "":
            return valor_atual
        if edicao and valor == "-":
            return ""
        if campo == "Email" and valor and "@" not in valor:
            print("Email inválido: inclua @ ou deixe o campo vazio.")
            continue
        if campo == "Telefone" and sum(caractere.isdigit() for caractere in valor) > 11:
            print("Telefone inválido: informe no máximo 11 dígitos.")
            continue
        return valor


def ler_dados_cliente(cliente=None):
    """Retorna (nome, cpf, email, telefone), repetindo só os campos inválidos."""
    edicao = cliente is not None
    id_cliente, nome_atual, cpf_atual, email_atual, telefone_atual = (
        cliente or (None, "", "", "", "")
    )
    if edicao:
        print("Enter mantém o valor atual. Digite - para apagar email ou telefone.")

    pergunta_nome = f"Novo nome [{nome_atual or ''}]: " if edicao else "Nome: "
    while True:
        nome = input(pergunta_nome).strip()
        if not nome and edicao:
            nome = nome_atual or ""
        if nome.strip():
            break
        print("Erro: o nome não pode ficar vazio.")

    pergunta_cpf = "CPF (com ou sem pontuação): "
    if edicao:
        pergunta_cpf = f"Novo CPF [{formatar_cpf(cpf_atual or '')}] (Enter mantém): "
    while True:
        entrada = ler_cpf(pergunta_cpf).strip()
        # Só Enter ou espaços mantêm o CPF atual na edição.
        if edicao and not entrada:
            cpf = cpf_atual or ""
        else:
            cpf = normalizar_cpf(entrada)
        try:
            validar_dados_cliente(nome, cpf, id_cliente)
            break
        except ValueError as erro:
            print(f"Erro: {erro}")

    email = ler_contato("Email", email_atual, edicao)
    telefone = ler_contato("Telefone", telefone_atual, edicao)
    return nome, cpf, email, telefone


def cadastrar_pelo_menu():
    """Solicita os dados e informa o resultado do cadastro."""
    nome, cpf, email, telefone = ler_dados_cliente()
    try:
        cadastrar_cliente(nome, cpf, email, telefone)
        print(f"Cliente cadastrado com sucesso! ({nome})")
    except ValueError as erro:
        print(f"Erro ao cadastrar cliente: {erro}")


def editar_pelo_menu():
    """Permite corrigir o ID; grava somente se os dados mudarem."""
    cliente = selecionar_cliente("editar")
    if cliente is None:
        return
    id_cliente = cliente[0]
    nome, cpf, email, telefone = ler_dados_cliente(cliente)
    if (nome, cpf, email, telefone) == cliente[1:]:
        print(f"Nenhuma alteração realizada. ID: {id_cliente} | Nome: {nome}")
        return
    try:
        if editar_cliente(id_cliente, nome, cpf, email, telefone):
            print(f"Cliente atualizado com sucesso! ID: {id_cliente} | Nome: {nome}")
        else:
            print(f"Erro: nenhum cliente encontrado com o ID {id_cliente}.")
    except ValueError as erro:
        print(f"Erro ao editar cliente: {erro}")


def excluir_pelo_menu():
    """Identifica o cliente e exige s/sim; Enter ou n/não cancelam."""
    cliente = selecionar_cliente("excluir")
    if cliente is None:
        return
    id_cliente, nome, cpf, email, telefone = cliente
    print(f"Cliente selecionado: ID: {id_cliente} | Nome: {nome or ''} | CPF: {formatar_cpf(cpf or '')}")
    while True:
        confirmacao = input(
            f"Tem certeza que deseja excluir o cliente {id_cliente}? "
            "(s/sim para excluir; n/não ou Enter para cancelar): "
        ).strip().lower()
        if confirmacao in ("n", "não", "nao", ""):
            print("Exclusão cancelada.")
            return
        if confirmacao in ("s", "sim"):
            break
        print("Resposta inválida. Digite s/sim para excluir ou n/não para cancelar.")
    if excluir_cliente(id_cliente):
        print("Cliente excluído com sucesso!")
    else:
        print(f"Erro: nenhum cliente encontrado com o ID {id_cliente}.")


def menu_principal():
    """Repete as opções de clientes até o usuário escolher 0."""
    while True:
        print("""
=== MENU ===
1 - Cadastrar cliente
2 - Listar clientes
3 - Editar cliente
4 - Excluir cliente
0 - Sair""")
        opcao = input("Escolha uma opção: ").strip()

        try:
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
        except sqlite3.Error:
            print("Não foi possível concluir a operação no banco. "
                  "Verifique o arquivo, as permissões e tente novamente.")


def iniciar():
    """Inicia o programa; trata interrupções e retorna 1 se o banco não abrir."""
    try:
        inicializar_banco()
        while not tela_login():
            pass
        menu_principal()
    except (EOFError, KeyboardInterrupt):
        print("\nEntrada interrompida. Encerrando o programa.")
    except sqlite3.Error:
        print("Não foi possível acessar o banco de dados. "
              "Verifique o caminho e as permissões do arquivo.")
        return 1


if __name__ == "__main__":
    raise SystemExit(iniciar())
