"""Busca, páginas de dez clientes e seleção de um ID no terminal."""

from clientes import listar_clientes, pesquisar_clientes

TAMANHO_PAGINA = 10
PERGUNTA_BUSCA = "Buscar por nome ou CPF (Enter para listar todos): "


def _exibir_pagina(clientes, pagina):
    """Mostra somente os registros da página indicada, começando em zero."""
    if len(clientes) > TAMANHO_PAGINA:
        total = (len(clientes) + TAMANHO_PAGINA - 1) // TAMANHO_PAGINA
        print(f"Página {pagina + 1} de {total}")
    print("ID | Nome | CPF | Email | Telefone")
    inicio = pagina * TAMANHO_PAGINA
    for id_cliente, nome, cpf, email, telefone in clientes[inicio:inicio + TAMANHO_PAGINA]:
        print(id_cliente, nome or "", cpf or "", email or "", telefone or "", sep=" | ")


def _mudar_pagina(comando, pagina, quantidade):
    """Aplica p/a e informa quando não há outra página nessa direção."""
    if comando == "p":
        if (pagina + 1) * TAMANHO_PAGINA < quantidade:
            return pagina + 1
        print("Você já está na última página.")
    elif pagina > 0:
        return pagina - 1
    else:
        print("Você já está na primeira página.")
    return pagina


def paginar_clientes(clientes):
    """Mostra até dez por página e retorna se havia algum registro."""
    if not clientes:
        print("Nenhum cliente cadastrado.")
        return False

    pagina = 0
    while True:
        _exibir_pagina(clientes, pagina)
        if len(clientes) <= TAMANHO_PAGINA:
            return True
        comando = input("p - próxima | a - anterior | 0 ou Enter - voltar: ").strip().casefold()
        if comando in ("0", ""):
            return True
        if comando in ("p", "a"):
            pagina = _mudar_pagina(comando, pagina, len(clientes))
        else:
            print("Comando inválido. Use p, a ou 0 para voltar.")


def buscar_pelo_menu():
    """Pede nome ou CPF e apresenta os resultados em páginas."""
    encontrados = pesquisar_clientes(input(PERGUNTA_BUSCA))
    if not encontrados:
        print("Nenhum cliente encontrado para a busca.")
        return
    paginar_clientes(encontrados)


def selecionar_cliente(acao):
    """Permite buscar, navegar e corrigir o ID antes de editar ou excluir."""
    clientes = listar_clientes()
    if not clientes:
        print("Nenhum cliente cadastrado.")
        return None

    pagina = 0
    while True:
        if clientes:
            _exibir_pagina(clientes, pagina)
        else:
            print("Nenhum cliente encontrado para a busca.")
        print("b - buscar | p - próxima | a - anterior | 0 - voltar")
        entrada = input(f"ID do cliente a {acao}: ").strip().casefold()
        if entrada == "0":
            print("Edição cancelada." if acao == "editar" else "Exclusão cancelada.")
            return None
        if entrada == "b":
            clientes = pesquisar_clientes(input(PERGUNTA_BUSCA))
            pagina = 0
            continue
        if entrada in ("p", "a"):
            pagina = _mudar_pagina(entrada, pagina, len(clientes))
            continue
        if not entrada.isascii() or not entrada.isdecimal():
            print("Erro: informe um ID numérico positivo ou 0 para voltar.")
            continue

        id_cliente = entrada.lstrip("0") or "0"
        for cliente in clientes:
            if str(cliente[0]) == id_cliente:
                return cliente
        print(f"Erro: nenhum cliente encontrado com o ID {id_cliente}.")
