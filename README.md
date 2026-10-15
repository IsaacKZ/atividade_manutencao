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

## Testes

```bash
python3 -B -m unittest discover -v
```

Os testes usam bancos temporários, sem alterar os dados do projeto.

Veja as [correções](CORRECOES.md) e os [limites conhecidos](REVISAO.md).
