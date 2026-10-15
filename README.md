# Cadastro de clientes

Programa local em Python para cadastrar, listar, editar e excluir clientes.
Usa SQLite e não precisa instalar bibliotecas.

## Executar

Na pasta do projeto:

```bash
python3 -B main.py
```

Em um banco novo, entre com usuário **admin** e senha **admin123**.
O arquivo `sistema.db` guarda os dados na pasta do projeto.

Para usar outro banco, informe um caminho absoluto:

```bash
SISTEMA_DB_PATH=/tmp/teste.db python3 -B main.py
```

## Preencher os dados

- CPF pode ser digitado com ou sem pontos e hífen; o banco guarda só os dígitos.
- Nome e CPF são conferidos antes das perguntas seguintes. Se houver erro,
  basta corrigir o campo, sem recomeçar o cadastro ou a edição.
- Na edição, Enter mantém o valor mostrado. Para apagar email ou telefone,
  digite `-` no campo.
- Espaços externos no usuário, na opção do menu e no CPF são ignorados.

## Testes

```bash
python3 -B -m unittest discover -v
```

Os testes usam bancos temporários, sem alterar os dados do projeto.

Veja as [correções](CORRECOES.md) e os [limites conhecidos](REVISAO.md).
