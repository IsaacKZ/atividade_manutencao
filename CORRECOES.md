# O que foi ajustado

## Correções anteriores às melhorias de UX

Esta seção registra o comportamento da versão anterior. As mudanças de seleção,
paginação e confirmação da versão atual estão na seção de UX abaixo.

- Login simples, sem hash ou troca obrigatória de senha.
- Listagem exibida uma vez, com separadores e suporte a campos nulos.
- Naquela versão, edição e exclusão paravam se não houvesse clientes ou se o
  ID não existisse. Agora, um ID incorreto pode ser corrigido na mesma tela.
- Cada ação usa seus próprios dados, evitando alterar o cliente errado.
- Cadastro e edição validam nome, CPF e duplicidade.
- CPF tem os dois dígitos verificadores conferidos com contas e laços.
- Exclusão pede confirmação e só informa sucesso se remover um registro.
- Banco usa o mesmo caminho ao iniciar o programa de outra pasta.
- Consultas e gravações compartilham duas funções em `database.py`.
- Edição mostra os valores atuais: Enter mantém e `-` apaga email ou telefone.
- Nome e CPF inválidos são corrigidos no próprio campo, antes de avançar.
- Menu, usuário e CPF ignoram espaços externos; a senha mantém seus espaços.
- CPF aceita pontuação e é salvo só com dígitos, sem permitir duplicação por formato.

O fluxo e as operações estão descritos em [DOCUMENTACAO.md](DOCUMENTACAO.md).

## Histórico da simplificação

- As 23 funções anteriores e suas assinaturas foram mantidas. Foi acrescentada
  `ler_contato(campo, valor_atual='', edicao=False)` para compartilhar a leitura
  de email e telefone, sem repetir as regras de Enter e `-`.
- A edição continua preservando o contato atual ao receber Enter, inclusive
  valores nulos ou com espaços. O hífen só apaga contatos na edição; no cadastro,
  é salvo como texto.
- `consultar()`, `executar()` e `inicializar_banco()` usam `contextlib.closing`
  para fechar conexões também em caso de erro. As gravações mantêm `commit()`
  explícito.
- O CPF mantém os dois verificadores e a lista explícita de caracteres de `0`
  a `9`. Os pesos são calculados pela posição em vez de atualizar uma variável
  a cada dígito.
- As três verificações de listas não vazias em `login()`, `cpf_ja_cadastrado()`
  e `cliente_existe()` usam `bool(...)` no lugar de `len(...) > 0`.
- O texto do menu foi reunido em um bloco de várias linhas, com as mesmas opções
  e mensagens daquela versão.
- Foram acrescentados três testes de contatos: hífen literal no cadastro,
  Enter preservando `None` e apagar um contato enquanto uma entrada só de espaços
  mantém o outro. A suíte passou de 50 para 53 testes.
- O README passou a apresentar requisitos, uso local e banco fora do repositório
  na nuvem. A [documentação do código](DOCUMENTACAO.md) reúne fluxo, módulos,
  campos do banco, caminhos, todas as funções e cálculo do CPF.

## Melhorias de UX atuais — itens 2, 3, 4, 5, 6, 7 e 10

- **2 — Erros amigáveis:** EOF ou `Ctrl+C` encerram com mensagem e código `0`,
  sem gravar um formulário incompleto. Erro de SQLite durante uma ação mostra
  orientação e retorna ao menu; falha na inicialização ou no login encerra com
  código `1`, sem traceback.
- **3 — Confirmação de exclusão:** identifica ID, nome e CPF. `s` e `sim` excluem;
  `n`, `não`, `nao` e Enter cancelam. Antes, `sim` cancelava. Respostas inválidas
  agora repetem a pergunta.
- **4 — Correção de ID:** edição e exclusão permitem corrigir um ID inválido ou inexistente, buscar com
  `b`, navegar por páginas e voltar com `0`. A escolha respeita a busca atual.
- **5 — Campos opcionais:** cadastro informa que email e telefone são opcionais.
  A edição mostra os valores atuais e as legendas de Enter para manter e `-`
  para apagar contatos.
- **6 — CPF consistente e máscara:** o CPF recebe máscara durante a digitação em terminais POSIX compatíveis,
  usando somente a biblioteca padrão. Aceita colagem com ou sem pontuação,
  Backspace e `Ctrl+U`, e restaura o terminal mesmo após uma interrupção. Windows,
  pipes e terminais sem suporte usam leitura comum, sem máscara ao vivo.
  A entrada original do CPF é preservada para validar; caracteres inválidos e
  excesso não são descartados. Na edição, somente entrada vazia ou só com
  espaços mantém o CPF anterior; `-` e `...` exigem correção.
- **7 — Feedback da edição:** sem mudança, informa “Nenhuma alteração realizada” sem executar
  `UPDATE`; antes, anunciava atualização. Uma mudança confirma ID e nome, e o
  cadastro confirma o nome salvo.
- **10 — Busca e paginação:** a opção `5` busca parte do nome, ignorando caixa,
  ou parte do CPF, com ou sem pontuação. Enter lista todos. A pesquisa ocorre em
  memória, sem mudar o esquema do banco ou acrescentar dependências. Listagens
  e resultados são divididos em páginas de dez. Acima de dez, `p` avança, `a`
  volta e `0` ou Enter retorna ao menu. Listas menores não pedem Enter adicional.

As 24 funções da versão simplificada mantêm suas assinaturas. Foram acrescentados
`pesquisar_clientes()` e os módulos `consulta_clientes.py` e `entrada_cpf.py`.
Busca, seleção, paginação, mensagens, falhas de banco e máscara foram verificadas
com testes, incluindo PTY Linux.

## Correções da revisão geral — erros 3 e 4

- **3 — CPF legado:** a verificação de duplicidade normaliza também os CPFs
  armazenados. Cadastro e edição reconhecem o mesmo CPF com ou sem pontuação
  ou espaços externos. A edição continua permitindo manter o próprio CPF e a
  consulta ignora valores nulos, sem modificar os registros antigos.
- **4 — Inicialização simultânea:** a criação da conta padrão verifica se há
  usuários e insere o administrador em um único comando SQL. Isso evita o erro
  de usuário duplicado entre inicializações e preserva contas já existentes,
  inclusive quando não há um administrador.
- Foram acrescentados testes de regressão para os formatos legados, preservação
  de dados e inicializações concorrentes com conexões SQLite reais.

Os [limites conhecidos e a orientação para senhas antigas](REVISAO.md) permanecem
documentados separadamente.

## Validação e remoção dos testes e README

Antes da remoção, foram executados 300 testes: 297 aprovados e 3 falhas
esperadas, correspondentes aos erros conhecidos 1, 2 e 5 descritos em
[REVISAO.md](REVISAO.md#regressões-pendentes).

Por solicitação do usuário, foram removidos `tests/`, `test_sistema.py` e
`README.md`. As referências aos arquivos removidos foram atualizadas na
documentação restante. O código do programa e o banco foram preservados.
