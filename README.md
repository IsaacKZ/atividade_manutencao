# Cadastro de clientes

Programa de terminal em Python para fazer login e cadastrar, listar, editar
e excluir clientes. Os dados ficam em um banco SQLite.

## Executar

Use Python 3 com suporte a SQLite; o projeto foi validado com Python 3.12.14.
Não há pacotes externos para instalar.

Na pasta do projeto, execute:

```bash
python3 -B main.py
```

Em um banco novo, entre com usuário `admin` e senha `admin123`. O arquivo
`sistema.db` é criado na pasta de execução; execute sempre da pasta do projeto
para acessar o mesmo banco. Um banco existente mantém seus dados e usuários.

## Entender o código

| Arquivo | Responsabilidade |
| --- | --- |
| `main.py` | Login, perguntas ao usuário, exibição e menu. Cada ação tem sua própria função. |
| `auth.py` | Conferir usuário e senha. |
| `clientes.py` | Validar os dados e cadastrar, consultar, editar ou excluir clientes. |
| `database.py` | Abrir a conexão e criar as tabelas quando necessário. |
| `test_sistema.py` | Testar o programa usando bancos temporários. |

Para acompanhar o fluxo, comece por `iniciar()` em `main.py`, depois leia
`menu_principal()` e a função da opção desejada. Cadastro e edição compartilham
`ler_dados_cliente()` e `validar_dados_cliente()`.

As consultas usam `conexao.execute()` diretamente. O bloco
`with closing(conectar())` fecha a conexão ao terminar, inclusive se ocorrer
uma exceção. As gravações continuam usando `commit()` explicitamente.

## Testes e documentação

```bash
python3 -B -m unittest discover -v
```

Os 12 testes usam bancos temporários e não modificam o banco do projeto.
As correções e a simplificação estão em [CORRECOES.md](CORRECOES.md).
Os problemas restantes e possíveis melhorias estão em [REVISAO.md](REVISAO.md).
