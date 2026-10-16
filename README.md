# Cadastro de clientes

Programa de terminal para cadastrar, listar, buscar, editar e excluir clientes.
Precisa de **Python 3 com SQLite**; foi validado com Python 3.12.
Usa apenas bibliotecas que já vêm com o Python.

## Começar

Na pasta do projeto:

```bash
python3 -B main.py
```

Se o banco não tiver usuários, o programa cria a conta **admin**, com senha
**admin123**. Por padrão, os dados ficam em `sistema.db`, na pasta do projeto,
mesmo quando o programa é iniciado de outra pasta.

Na nuvem, use um banco fora da pasta do repositório. Exemplo em Bash:

```bash
mkdir -p /tmp/atividade-manutencao
SISTEMA_DB_PATH=/tmp/atividade-manutencao/sistema.db python3 -B main.py
```

Use o mesmo caminho nas próximas execuções para acessar os mesmos dados.
O conteúdo de `/tmp` é temporário; para guardar os dados, escolha outro local
disponível e faça uma cópia do arquivo do banco.

## Usar o menu

| Opção | Ação |
| --- | --- |
| `1` | Cadastrar nome, CPF, email e telefone. |
| `2` | Listar os clientes e seus IDs, em páginas de dez. |
| `3` | Buscar ou escolher um ID e editar seus dados. |
| `4` | Buscar ou escolher um ID e confirmar a exclusão. |
| `5` | Buscar por parte do nome ou do CPF. |
| `0` | Sair. |

Na listagem e nos resultados de busca, até dez clientes aparecem de uma vez e
o programa volta ao menu. Com mais de dez, use `p` para a próxima página, `a`
para a anterior e `0` ou Enter para voltar.

A busca ignora maiúsculas e minúsculas no nome, mas mantém as diferenças de
acentuação: `JOÃO` encontra `João`; `Joao` não encontra `João`. O CPF pode ser
buscado inteiro ou em parte, com ou sem pontuação. Enter na busca lista todos.

Ao escolher um cliente para editar ou excluir, use `b` para buscar, `p` e `a`
para navegar ou `0` para voltar. Um ID inválido ou inexistente pode ser corrigido
na mesma tela. A seleção aceita qualquer ID do resultado atual, inclusive de
outra página; clientes fora do filtro precisam de uma nova busca.

Antes de excluir, confira ID, nome e CPF. `s` ou `sim` confirmam; `n`, `não`,
`nao` ou Enter cancelam. Outra resposta repete a pergunta.

## Regras dos campos

- Nome é obrigatório. Email e telefone são opcionais, sem validação de formato.
- CPF pode ser digitado com ou sem pontos e hífen; o banco guarda só os dígitos.
- Em terminais POSIX compatíveis, a máscara aparece enquanto o CPF é digitado.
  É possível colar com ou sem pontuação, usar Backspace para apagar o último
  caractere e `Ctrl+U` para limpar o campo. Em Windows, pipes e terminais sem
  suporte, a leitura comum continua aceitando os dois formatos, sem máscara ao vivo.
- CPF precisa ter 11 dígitos de `0` a `9`, verificadores corretos e não pode
  repetir o de outro cliente. Sequências com todos os dígitos iguais são recusadas.
- Nome e CPF são conferidos antes das perguntas seguintes. Se houver erro,
  basta corrigir o campo, sem recomeçar o cadastro ou a edição.
- No cadastro, os contatos mostram que são opcionais e Enter pula o campo.
- Na edição, Enter mantém o valor mostrado. Para apagar email ou telefone,
  digite `-` no campo. No cadastro, `-` é salvo como texto. No CPF, somente
  entrada vazia ou só com espaços mantém o anterior; `-` e `...` são inválidos.
- Se nenhum dado mudar na edição, o programa informa isso sem gravar uma
  atualização. Uma alteração confirmada mostra o ID e o nome do cliente.
- O terminal retira espaços externos dos campos recém-digitados, do usuário e da opção do menu.
  A senha é comparada exatamente como digitada, inclusive os espaços.

Fim da entrada ou `Ctrl+C` encerram com uma mensagem, sem salvar um formulário
incompleto. Falhas de SQLite durante uma ação mostram orientação e devolvem ao
menu; se o banco falhar na inicialização ou no login, o programa encerra com
código de erro `1`.

## Testes

```bash
python3 -B -m unittest discover -v
```

Os testes usam bancos temporários, sem alterar os dados do projeto. A leitura
do CPF também é exercitada em um pseudoterminal (PTY) no Linux; esses casos são
ignorados em plataformas sem PTY POSIX. O [mapa dos testes](DOCUMENTACAO.md#mapa-dos-testes)
explica os grupos.

Consulte a [documentação do código](DOCUMENTACAO.md), o [histórico de correções](CORRECOES.md)
e os [limites conhecidos e orientação sobre senhas antigas](REVISAO.md).
