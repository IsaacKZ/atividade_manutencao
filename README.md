# Cadastro de clientes

Programa local de terminal para cadastrar, listar, editar e excluir clientes.
Usa Python 3 e SQLite, sem pacotes externos.

## Executar

```bash
cd /workspace/atividade_manutencao
python3 -B main.py
```

Em um banco novo, o login é **admin** e a senha é **admin123**. Se o banco já
possuir usuários, eles são mantidos. Não há cadastro inicial, tamanho mínimo
ou troca obrigatória de senha. A senha é comparada diretamente com o texto
salvo no banco, conforme a proposta de uso local simples.

O banco padrão é o `sistema.db` ao lado de `database.py`, mesmo se o programa
for iniciado de outra pasta. Para usar um banco separado:

```bash
SISTEMA_DB_PATH=/tmp/cadastro-teste.db python3 -B main.py
```

A pasta de destino precisa existir. Os clientes do banco original não são
apagados nem modificados pela inicialização.

## Como o código está organizado

- `main.py`: perguntas, mensagens e menu.
- `auth.py`: uma função para conferir usuário e senha.
- `clientes.py`: validação e operações de clientes.
- `database.py`: caminho do arquivo, conexão e criação das tabelas.

A aplicação importa somente `os` (caminhos) e `sqlite3` (banco), além dos
próprios arquivos do projeto. Em `database.py`, `consultar()` devolve uma lista
de resultados e `executar()` grava a alteração e devolve a quantidade de linhas
afetadas. Elas fecham as conexões com `close()`, inclusive em caso de erro,
evitando repetir esse código no login e nas operações de clientes.
Não há hash, salt, iterações ou migração automática de senhas no programa.

## Regras e funcionamento

- Nome não pode estar vazio ou conter somente espaços.
- CPF deve ter 11 dígitos sem pontuação, sem sequência uniforme e com os dois
  verificadores corretos. O cálculo usa contas, `for` e `if`.
- Cadastro e edição rejeitam CPF de outro cliente, mas permitem manter o próprio.
- Sem clientes, editar e excluir retornam ao menu sem fazer perguntas. ID
  inexistente também retorna antes de solicitar dados ou confirmação.
- A listagem aparece uma vez, com campos separados por `|`, sem larguras
  fixas. Campos nulos importados aparecem vazios, e nomes longos são mantidos.
- A exclusão de um cliente existente continua pedindo confirmação.
- Email e telefone continuam opcionais, sem validação de formato.

## Se você já utilizou a versão com hash

Senhas já convertidas não voltam ao texto original. O programa não sobrescreve
essas contas automaticamente. Para escolher uma nova senha para uma dessas
contas, execute na pasta do projeto:

```bash
python3 -B -c '
from database import conectar
usuario = input("Usuário da conta: ")
senha = input("Nova senha: ")
conexao = conectar()
cursor = conexao.execute(
    "UPDATE usuarios SET senha = ? WHERE username = ? AND senha LIKE ?",
    (senha, usuario, "pbkdf2_sha256$%"),
)
conexao.commit()
print("Contas atualizadas:", cursor.rowcount)
conexao.close()
'
```

Isso altera somente a senha da conta informada que ainda esteja no formato
antigo de hash. Clientes e outros usuários são preservados. Se você definiu
`SISTEMA_DB_PATH`, use o mesmo banco nesse comando e na execução do programa.

## Testes e registro das alterações

```bash
python3 -B -m unittest discover -v
```

Os testes usam bancos temporários, sem alterar o banco original. Os testes de
criptografia foram retirados junto da funcionalidade removida; os testes de
menu, CPF, cadastro, edição, exclusão e caminho do banco continuam.

Veja [CORRECOES.md](CORRECOES.md) para o que foi ajustado e
[REVISAO.md](REVISAO.md) para os limites conhecidos.
