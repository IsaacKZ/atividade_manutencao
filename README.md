# Cadastro de clientes

Programa de terminal em Python para fazer login e cadastrar, listar, editar
e excluir clientes. Os dados ficam em um banco SQLite.

## Executar

Use Python 3 com suporte a SQLite. O programa usa somente a biblioteca padrão;
não há pacotes externos para instalar nem serviços para iniciar.

Na pasta do projeto:

```bash
cd /workspace/atividade_manutencao
python3 -B main.py
```

Também é possível iniciar de outra pasta, informando o caminho do programa:

```bash
python3 -B /workspace/atividade_manutencao/main.py
```

Por padrão, as duas formas abrem o mesmo `sistema.db`, ao lado de `database.py`.
Para usar outro banco, informe `SISTEMA_DB_PATH`. Prefira um caminho absoluto
para acessar o mesmo arquivo de qualquer pasta. A pasta de destino deve existir
e permitir gravação:

```bash
SISTEMA_DB_PATH=/tmp/cadastro-teste.db python3 -B /workspace/atividade_manutencao/main.py
```

Se o arquivo ainda não existir, o SQLite o cria. Um banco existente mantém seus
clientes e usuários. A validação nova de CPF não reescreve dados antigos.

## Primeiro acesso e senhas antigas

Em um banco sem usuários, o programa pede a criação do primeiro usuário e a
confirmação da senha. Escolha uma senha com pelo menos 8 caracteres e diferente
da antiga senha padrão `admin123`. Não há criação automática de uma conta com
senha conhecida. Depois, use as credenciais escolhidas na tela de login.

As senhas novas são armazenadas usando PBKDF2 com SHA-256 e um salt aleatório
por senha, por meio de `hashlib` da biblioteca padrão. O hash permite conferir
a senha sem guardar seu texto original; não é um algoritmo de segurança
inventado para o projeto.

Contas antigas com senha em texto puro recebem um hash somente após um login
correto, sem trocar a senha escolhida nem apagar clientes. A exceção é a antiga
conta `admin` com senha `admin123`: o programa exige que essa senha conhecida
seja substituída antes de abrir o menu.

A migração atualiza o banco em uso. Ela não remove senhas copiadas para backups
ou para o histórico do Git. Se uma senha antiga foi exposta ou reutilizada em
outro serviço, troque-a também nesse serviço. A senha ainda aparece durante a
digitação no terminal; use o programa em um ambiente de confiança.

## Regras dos clientes

- O nome não pode ficar vazio ou conter somente espaços.
- O CPF deve ter exatamente 11 dígitos ASCII, sem pontos ou hífen. Sequências
  como `00000000000` e CPFs com verificadores incorretos são rejeitados.
- Cadastro e edição aplicam as mesmas regras. Um CPF já usado por outro
  cliente é rejeitado; editar um cliente mantendo o próprio CPF é permitido.
- Email e telefone continuam opcionais e sem validação de formato.

Os dígitos verificadores confirmam somente a estrutura matemática do CPF.
Eles não comprovam emissão, existência da pessoa ou identidade de quem o informa.
Dados antigos inválidos não são alterados silenciosamente: ao editar um cliente,
os novos dados precisam atender às regras atuais.

## Entender o código

| Arquivo | Responsabilidade |
| --- | --- |
| `main.py` | Primeiro acesso, login, perguntas, exibição e menu. |
| `auth.py` | Criação de usuário, verificação e migração de senhas. |
| `clientes.py` | Validação, cadastro, consulta, edição e exclusão de clientes. |
| `database.py` | Escolha do arquivo SQLite, conexão e criação das tabelas. |
| `test_sistema.py` e `tests/` | Testes de regressão com bancos temporários. |

Comece por `iniciar()` em `main.py`, depois leia `menu_principal()` e a função
da opção desejada. Cadastro e edição compartilham `ler_dados_cliente()` e
`validar_dados_cliente()`. A validação do CPF calcula seus dois dígitos com
laços `for` e condições `if`.

As consultas usam parâmetros para os valores fornecidos pelo usuário.
`with closing(conectar())` fecha a conexão inclusive quando ocorre uma exceção;
as gravações usam `commit()` explicitamente.

## Testes automáticos

Na pasta do projeto, execute a suíte completa:

```bash
python3 -B -m unittest discover -v
```

Os testes usam arquivos SQLite temporários, inclusive nas execuções do menu em
subprocessos. Não precisam modificar o `sistema.db` do repositório. O comando
mostra o resultado e a quantidade efetivamente executada; o registro das
correções está em [CORRECOES.md](CORRECOES.md).

## Conferência manual em um banco descartável

O roteiro abaixo usa dados fictícios e CPFs com verificadores válidos para
teste. Execute com um banco separado para preservar o banco do projeto:

```bash
cd /tmp
pasta_teste="$(mktemp -d)"
SISTEMA_DB_PATH="$pasta_teste/sistema.db" python3 -B /workspace/atividade_manutencao/main.py
```

1. Crie o usuário `teste` com uma senha de teste de pelo menos 8 caracteres,
   diferente de `admin123`, e confirme-a. Faça login quando solicitado.
2. Escolha `2`. A lista vazia deve aparecer uma vez, e o programa deve voltar
   ao menu sem pedir dados de edição.
3. Escolha `3` diretamente, antes de cadastrar alguém. Informe ID `999`, nome
   `Pessoa Teste A`, CPF `52998224725`, email `a@example.invalid` e telefone
   `123`. Deve aparecer a mensagem de cliente inexistente, sem encerrar o programa.
4. Escolha `1` e cadastre `Pessoa Teste A`, CPF `52998224725`, email
   `a@example.invalid` e telefone `123`. Cadastre também `Pessoa Teste B`, CPF
   `11144477735`, email `b@example.invalid` e telefone `456`.
5. Escolha `2`, anote os IDs e confira que cada cliente aparece uma vez. A
   listagem não deve iniciar uma edição.
6. Escolha `3`, informe o ID de A, nome `Pessoa Teste A Editada`, o mesmo CPF
   `52998224725`, email `a2@example.invalid` e telefone `789`. Deve haver sucesso.
   Escolha `2` e confira que somente A mudou e B mantém seus dados.
7. Repita a edição de A, sempre fornecendo os quatro campos, para tentar cada
   caso: nome só com espaços; CPF `52998224724`; CPF `00000000000`; e CPF de B,
   `11144477735`. Cada tentativa deve mostrar erro e manter A sem alterações.
   Repita esses valores inválidos no cadastro para conferir as mesmas regras.
8. Escolha `4` com o ID de A e responda `n`. Confira que A continua na lista.
   Repita e responda `s`; A deve desaparecer e B deve permanecer.
9. Escolha `0`. Inicie novamente de outra pasta com o mesmo caminho absoluto:

   ```bash
   cd /workspace
   SISTEMA_DB_PATH="$pasta_teste/sistema.db" python3 -B /workspace/atividade_manutencao/main.py
   ```

   Entre com a conta criada e escolha `2`. B deve continuar cadastrado, sem
   pedir a criação de outra conta. Saia com `0`.

O repositório contém um banco com dados históricos de demonstração. Não grave
novos dados pessoais reais em arquivos que serão versionados. Os limites ainda
conhecidos, como campos nulos importados e operações simultâneas, estão em
[REVISAO.md](REVISAO.md).
