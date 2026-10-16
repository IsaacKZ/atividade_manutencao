# Como o programa funciona

Para executar e usar o menu, veja o [README](README.md). Este documento explica
o código e os dados. Os [limites conhecidos e a orientação para senhas da versão
antiga](REVISAO.md) continuam válidos.

## Fluxo e arquivos

Ao executar `main.py`, `iniciar()` prepara o banco, pede login até acertar e abre
o menu. Cada opção chama sua própria função. Ao terminar a ação, o menu aparece
novamente; a opção `0` encerra o programa.

| Arquivo | Responsabilidade |
| --- | --- |
| `main.py` | Ler o teclado, mostrar mensagens, repetir campos inválidos e chamar as operações. |
| `auth.py` | Consultar se usuário e senha correspondem a uma conta. |
| `clientes.py` | Validar nome e CPF; cadastrar, consultar, editar e excluir clientes. |
| `consulta_clientes.py` | Buscar por nome ou CPF, exibir páginas e selecionar clientes para edição ou exclusão. |
| `entrada_cpf.py` | Formatar o CPF e, em terminais POSIX compatíveis, mostrar a máscara durante a digitação. |
| `database.py` | Definir o caminho do SQLite, abrir conexões, executar SQL e criar as tabelas. |
| `test_sistema.py` e `tests/` | Conferir as regras e o uso pelo terminal com bancos temporários. |

No cadastro e na edição, o nome é lido primeiro. Depois, o CPF é validado antes
de pedir os contatos. Um erro repete só o campo que precisa de correção. Os
contatos indicam que são opcionais; na edição, as perguntas mostram as regras
de Enter e `-`. O cadastro confirma o nome salvo. A edição compara os quatro
campos com os valores anteriores: se forem iguais, informa que não houve
alteração e não chama `editar_cliente()`; se mudar, confirma ID e nome.

As opções `2` e `5` mostram listas em páginas de dez clientes. Até dez registros
são exibidos sem pedir outra entrada. Acima disso, `p` avança, `a` volta e `0`
ou Enter retorna ao menu. A opção `5` pede parte do nome ou CPF; Enter lista
todos. Na busca por nome, `casefold()` ignora maiúsculas e minúsculas, inclusive
nas letras acentuadas, mas não retira acentos. Na busca por CPF, pontos e hífens
são retirados tanto do termo como do valor armazenado. A filtragem ocorre em
memória, mantendo a ordem de `listar_clientes()` e sem alterar banco ou esquema.

Edição e exclusão usam `selecionar_cliente()`. Sem clientes, voltam ao menu.
Com clientes, aceitam um ID positivo, `b` para buscar, `p` e `a` para navegar e
`0` para voltar. ID inválido ou inexistente pode ser corrigido na mesma tela.
A seleção se limita ao resultado atual da busca, incluindo suas outras páginas.
Uma busca vazia remove o filtro; uma busca sem resultado permite buscar de novo
ou voltar. Cada nova busca começa na primeira página.

A exclusão mostra ID, nome e CPF formatado antes da confirmação. `s` e `sim`
confirmam; `n`, `não`, `nao` e Enter cancelam, ignorando maiúsculas e espaços
externos. Uma resposta diferente repete a confirmação.

`iniciar()` trata fim da entrada e `Ctrl+C` com uma mensagem e saída de código
`0`, sem gravar formulários incompletos. Erros de SQLite nas ações são tratados
por `menu_principal()`, que mostra orientação e volta ao menu. Na inicialização
ou no login, o erro de banco encerra com orientação e código `1`, sem traceback.

## Banco e caminho do arquivo

O SQLite guarda tudo em um arquivo. Não há servidor de banco para iniciar.

| Nome | Significado |
| --- | --- |
| `PASTA_PROJETO` | Pasta absoluta onde está `database.py`, calculada a partir de `__file__`. |
| `SISTEMA_DB_PATH` | Variável de ambiente opcional para escolher outro arquivo de banco. |
| `DB_PATH` | Caminho absoluto usado por `conectar()`. Vem de `SISTEMA_DB_PATH`; se ela estiver ausente ou vazia, usa `sistema.db` em `PASTA_PROJETO`. |

O caminho é calculado **ao importar `database.py`**. Se `SISTEMA_DB_PATH` for
relativo, ele é resolvido a partir da pasta atual naquele momento. Mudar a pasta
ou a variável de ambiente depois do import não recalcula `DB_PATH`. Prefira um
caminho absoluto e configure a variável antes de iniciar o programa. A pasta
escolhida precisa existir e permitir gravação; o SQLite cria o arquivo se necessário.

`inicializar_banco()` cria as tabelas somente se ainda não existirem. Se não
houver nenhum usuário, cria `admin` com senha `admin123`. Repetir a inicialização
preserva os registros existentes; ela não muda a estrutura de tabelas antigas.
A verificação de tabela vazia e a criação da conta usam um único comando SQL,
evitando a disputa pelo administrador quando duas execuções iniciam juntas.

| Tabela | Campo | Tipo e regra no banco |
| --- | --- | --- |
| `usuarios` | `id` | Inteiro, chave primária gerada automaticamente. |
| `usuarios` | `username` | Texto obrigatório e único. |
| `usuarios` | `senha` | Texto obrigatório, guardado em texto simples. |
| `clientes` | `id` | Inteiro, chave primária gerada automaticamente. |
| `clientes` | `nome` | Texto; o programa exige que não esteja vazio. |
| `clientes` | `cpf` | Texto; o programa valida e salva sem pontos ou hífen. |
| `clientes` | `email` | Texto opcional. |
| `clientes` | `telefone` | Texto opcional. |

Os quatro campos de texto de `clientes` aceitam `NULL` (ausência de valor) no banco. As regras de
nome e CPF são aplicadas em `clientes.py`; a tabela não tem uma restrição de CPF
único. A listagem exibe valores nulos como campos vazios.

As consultas usam `?` e passam os valores separados do SQL. `consultar()`,
`executar()` e `inicializar_banco()` usam `closing(conectar())`: a conexão fecha
ao sair do bloco, inclusive se ocorrer erro. No SQLite do Python, usar apenas
`with conexao:` cuida da transação, mas **não fecha a conexão**. As gravações
chamam `commit()` explicitamente para salvar. Se houver erro antes desse passo,
o fechamento descarta as alterações ainda não confirmadas.

Quem chamar `conectar()` diretamente precisa fechar a conexão e confirmar suas
gravações. As funções de banco repassam erros de SQLite, como falta de permissão
ou banco bloqueado, ao chamador. O tratamento na interface fica em
`menu_principal()` e `iniciar()`, conforme o fluxo acima.

## Como o CPF é conferido

1. Retira espaços externos, pontos e hífens. Espaços no meio não são retirados.
2. Exige 11 caracteres, todos da lista `0123456789`. Letras, `²` e números de
   outros alfabetos são recusados.
3. Recusa sequências com os 11 dígitos iguais.
4. Multiplica os primeiros nove dígitos pelos pesos de 10 até 2 e soma os valores.
   Calcula `11 - (soma % 11)`, em que `%` dá o resto da divisão; se o resultado for 10 ou 11, usa 0. Compara com
   o décimo dígito.
5. Repete a conta com os primeiros dez dígitos e pesos de 11 até 2. Compara com
   o último dígito.

O laço calcula cada peso pela posição: `quantidade + 1 - posicao`. A validação
dos dados também consulta se o CPF já existe. Na edição, ignora o próprio ID
para permitir manter o CPF. A comparação normaliza tanto a entrada quanto os
CPFs armazenados, incluindo registros antigos com pontuação ou espaços externos.
Essa consulta não modifica os registros e ignora CPFs nulos. As contas conferem
os verificadores, sem comprovar que o CPF foi emitido.

### Entrada e máscara de CPF

`ler_cpf()` devolve o texto digitado, sem normalizar nem validar. Em terminais
POSIX com entrada e saída interativas e `TERM` diferente de `dumb`, usa
`termios` e `tty`, da biblioteca padrão, para mostrar a pontuação enquanto o
usuário digita. Backspace apaga o último caractere, `Ctrl+U` limpa a linha e as
setas são ignoradas. A colagem aceita CPF com ou sem pontuação. O modo original
do terminal é restaurado em `finally`, inclusive após EOF ou `Ctrl+C`.

A máscara não descarta letras, pontuação inválida ou caracteres além do limite;
o texto original continua disponível para validação e pode ser recusado. Na edição, só a entrada
originalmente vazia, após retirar espaços externos, mantém o CPF antigo.
Entradas como `-` e `...` são validadas e recusadas, em vez de manter o anterior.

Em Windows, pipes, `TERM=dumb` ou terminais sem a configuração necessária,
`ler_cpf()` usa `input()`, sem máscara ao vivo. Os formatos com e sem pontuação
continuam válidos. `formatar_cpf()` também é usado para mostrar o CPF atual na
edição e na confirmação de exclusão; ele não muda o valor no banco.

## Referência das funções

As 24 funções que já existiam em `main.py`, `clientes.py`, `database.py` e
`auth.py` mantêm suas assinaturas. Foram acrescentadas `pesquisar_clientes()` e
as funções dos módulos de consulta e entrada de CPF descritas abaixo.

As funções esperam textos nos campos e um ID compatível com o SQLite. `None`
significa ausência de valor; `True` e `False` significam verdadeiro e falso.
Uma tupla é uma sequência de valores, como `(id, nome, cpf, email, telefone)`.
Quando uma função termina sem `return`, seu retorno é `None`. Funções que
acessam o banco podem repassar erros de SQLite; funções que leem o terminal
podem repassar `EOFError` ou `KeyboardInterrupt`. Ao executar `main.py`, os
tratamentos de `menu_principal()` e `iniciar()` cuidam dessas exceções.

### Terminal: `main.py`

| Assinatura | O que faz | Retorno e tratamento de erros |
| --- | --- | --- |
| `tela_login()` | Pede usuário e senha, retira espaços externos só do usuário e mostra o resultado. | `True` se autenticou; `False` caso contrário. Não altera contas. |
| `exibir_clientes()` | Consulta e delega a listagem em páginas a `paginar_clientes()`. | `True` se havia clientes; `False` se a lista estava vazia. |
| `ler_contato(campo, valor_atual='', edicao=False)` | Pede email ou telefone e retira espaços externos da nova entrada. Na edição, Enter devolve o valor atual sem modificá-lo e `-` devolve texto vazio. | Texto lido, ou o valor atual na edição, inclusive `None` ou texto com espaços. No cadastro, `-` é texto normal. |
| `ler_dados_cliente(cliente=None)` | Lê os quatro campos. Sem cliente, faz cadastro; com a tupla `(id, nome, cpf, email, telefone)`, faz edição. Usa `ler_cpf()` e valida antes dos contatos. | Tupla `(nome, cpf, email, telefone)`. Mostra os `ValueError` da validação e repete o CPF; nome vazio é repetido antes disso. Enter na edição mantém o valor atual. |
| `cadastrar_pelo_menu()` | Lê os dados, chama o cadastro e confirma o nome salvo. | `None`. Mostra os `ValueError` de `cadastrar_cliente()`. |
| `editar_pelo_menu()` | Seleciona um cliente, lê os dados e atualiza somente se houver mudança. | `None`. Sem mudança, informa o resultado sem executar `UPDATE`. Na atualização, mostra ID e nome; trata `ValueError`. |
| `excluir_pelo_menu()` | Seleciona e identifica o cliente; repete a confirmação até receber uma resposta válida. | `None`. `s`/`sim` excluem; `n`/`não`/`nao`/Enter cancelam. Só anuncia sucesso se remover o registro. |
| `menu_principal()` | Repete as opções de clientes, incluindo a busca, e chama a ação escolhida. | `None` ao escolher `0`. Opção inválida repete o menu. Trata erro de SQLite na ação com orientação e permite continuar. |
| `iniciar()` | Inicializa o banco, repete o login até entrar e abre o menu. Trata EOF, `Ctrl+C` e erro de SQLite na inicialização ou no login. | `None` na saída normal ou por interrupção; `1` na falha de banco. Executado como programa, esses retornos produzem códigos de saída `0` e `1`. |

O terminal retira espaços externos de nome e contatos recém-digitados. As
funções de cadastro e edição de `clientes.py` não fazem essa limpeza nesses
campos; recebem e guardam os valores fornecidos. Na edição pelo terminal, Enter
preserva exatamente um contato antigo, inclusive espaços ou `None`. Cada
contato é tratado separadamente: apagar email não apaga telefone, e vice-versa.

### Regras e clientes: `clientes.py`

| Assinatura | O que faz | Retorno e erros |
| --- | --- | --- |
| `normalizar_cpf(cpf)` | Retira espaços externos, pontos e hífens. Não consulta o banco. | Texto resultante; não verifica se o CPF é válido. |
| `validar_cpf(cpf)` | Normaliza e confere o tamanho, os caracteres e os dois verificadores. | `True` para CPF válido; `False` para inválido. |
| `cpf_ja_cadastrado(cpf, id_cliente=None)` | Compara a entrada e os CPFs armazenados após normalizá-los em memória; ignora nulos e o próprio ID na edição. | `True` se outro registro tiver o CPF, inclusive com pontuação antiga; `False` caso contrário. Não altera registros. |
| `cliente_existe(id_cliente)` | Procura o ID no banco. | `True` se existir; `False` caso contrário. |
| `buscar_cliente(id_cliente)` | Consulta os dados do ID informado. | Tupla `(id, nome, cpf, email, telefone)`, ou `None` se não existir. |
| `validar_dados_cliente(nome, cpf, id_cliente=None)` | Confere nome preenchido, CPF válido e ausência de duplicidade. Usa o ID para permitir o próprio CPF na edição. | `None` se estiver correto. Lança `ValueError` se o nome estiver vazio, o CPF for inválido ou já estiver cadastrado. Não grava. |
| `cadastrar_cliente(nome, cpf, email, telefone)` | Normaliza o CPF, valida e insere um cliente. | `None`. Lança `ValueError` se a validação falhar, sem inserir. |
| `listar_clientes()` | Consulta todos os clientes, sem definir ordem no SQL. | Lista de tuplas `(id, nome, cpf, email, telefone)`; `[]` se não houver registros. |
| `pesquisar_clientes(termo)` | Retira espaços externos e filtra a listagem em memória por parte do nome com `casefold()` ou do CPF normalizado. | Lista de tuplas, mantendo a ordem da listagem. Termo vazio retorna todos; sem correspondência, `[]`. `%` e `_` são texto literal. Não altera dados. |
| `editar_cliente(id_cliente, nome, cpf, email, telefone)` | Verifica o ID, normaliza o CPF, valida e atualiza todos os campos. | `True` se atualizou; `False` se o ID não existir. Validação inválida lança `ValueError`, preservando os dados anteriores. |
| `excluir_cliente(id_cliente)` | Remove o registro pelo ID. A confirmação é responsabilidade do menu. | `True` se removeu; `False` se não encontrou o ID. |

### Consulta no terminal: `consulta_clientes.py`

`TAMANHO_PAGINA` vale `10`. `PERGUNTA_BUSCA` contém a pergunta compartilhada pela
busca no menu e pela seleção de clientes.

| Assinatura | O que faz | Retorno |
| --- | --- | --- |
| `paginar_clientes(clientes)` | Exibe a lista em páginas de dez. Com até dez registros, não pede comando; acima disso, lê `p`, `a`, `0` ou Enter. | `True` se havia registros; `False` se a lista estava vazia. |
| `buscar_pelo_menu()` | Lê o termo, chama `pesquisar_clientes()` e pagina os resultados. | `None`. Se não encontrar, mostra aviso. |
| `selecionar_cliente(acao)` | Lista, permite buscar e navegar e repete IDs inválidos. `acao` é `editar` ou `excluir`. | Tupla do cliente selecionado no resultado atual, ou `None` ao voltar com `0` ou se não houver clientes cadastrados. |
| `_exibir_pagina(clientes, pagina)` | Imprime a página, com índice começando em zero e campos nulos como vazios. | `None`. |
| `_mudar_pagina(comando, pagina, quantidade)` | Aplica `p` ou `a`, avisando se já estiver na primeira ou última página. | Índice da página resultante. |

### Entrada de CPF: `entrada_cpf.py`

| Assinatura | O que faz | Retorno e erros |
| --- | --- | --- |
| `formatar_cpf(valor)` | Acrescenta a máscara a uma sequência de até onze dígitos, preservando pontuação válida já digitada. | Texto formatado; devolve o original se houver caracteres inválidos ou excesso. Não valida verificadores. |
| `ler_cpf(pergunta)` | Usa a máscara no terminal compatível, ou `input()` como alternativa. Restaura o modo do terminal ao terminar. | Texto original. EOF e `Ctrl+C` são repassados para o tratamento de `iniciar()`. |

Os auxiliares internos `_configuracao_terminal()`, `_ler_escape(descritor)`,
`_mostrar(pergunta, valor)` e `_ler_com_mascara(pergunta, descritor)` verificam o
terminal, tratam sequências de teclas, redesenham a linha e leem os caracteres.
Eles não acessam o banco.

### SQLite: `database.py`

| Assinatura | O que faz | Retorno e erros |
| --- | --- | --- |
| `conectar()` | Abre o SQLite em `DB_PATH`; pode criar o arquivo. | Conexão aberta. O chamador fica responsável por fechá-la. Pode lançar erro de SQLite ao abrir. |
| `consultar(sql, parametros=())` | Executa o SQL com os parâmetros, busca todas as linhas e fecha a conexão. | Lista de linhas, cada uma em uma tupla; `[]` se a consulta não retornar linhas. Erros de SQL são repassados. |
| `executar(sql, parametros=())` | Executa o SQL com os parâmetros, confirma a gravação e fecha a conexão. | `rowcount`: quantidade de linhas afetadas nas operações de clientes. O SQLite pode devolver `-1` para outros tipos de comando. Erros são repassados. |
| `inicializar_banco()` | Cria as tabelas ausentes e insere a conta padrão com uma condição atômica de tabela vazia; confirma e fecha a conexão. | `None`. Preserva os dados existentes, permite inicializações simultâneas e repassa erros de SQLite. |

### Login: `auth.py`

| Assinatura | O que faz | Retorno e erros |
| --- | --- | --- |
| `login(username, senha)` | Consulta os dois valores exatamente como recebidos, com parâmetros SQL. Não modifica usuários ou senhas. | `True` se encontrar a conta; `False` caso contrário. Repassa erros de SQLite. |

## Mapa dos testes

O comando completo está no [README](README.md#testes). Os testes usam arquivos
temporários e substituem `DB_PATH` ou definem `SISTEMA_DB_PATH` nos processos
do programa, mantendo o banco do projeto separado.

| Arquivo | O que confere |
| --- | --- |
| `test_sistema.py` | Cadastro, listagem sem abrir edição, edição válida ou recusada, IDs inexistentes, login e exclusão confirmada ou cancelada. |
| `tests/test_auth.py` | Login padrão, acertos e erros sem mudar senhas, usuário inexistente, texto SQL e comparação exata da senha. |
| `tests/test_clientes.py` | Verificadores de CPF, caracteres permitidos, pontuação, duplicidade incluindo CPFs legados, edição do próprio CPF, nulos e preservação dos dados quando a edição falha. |
| `tests/test_database.py` | Criação do banco e conta padrão, inicialização repetida e concorrente, preservação de usuários sem admin e caminhos padrão, absoluto e relativo. |
| `tests/test_menu.py` | Fluxos completos do programa, campos inválidos, espaços, listagem com nulos, confirmação e manutenção ou remoção independente dos contatos. |
| `tests/test_ux.py` | Indicações de campos opcionais, CPF inválido na edição, confirmação de exclusão, correção de ID, edição sem `UPDATE`, busca, paginação, interrupções e falhas de banco. Os casos em PTY também exercitam cadastro com máscara e interrupção no programa completo. |
| `tests/test_entrada_cpf.py` | Máscara e preservação da entrada; alternativa por pipe; digitação, colagem, Backspace, `Ctrl+U`, setas e restauração do terminal em PTY POSIX, inclusive após EOF ou `Ctrl+C`. |
| `tests/test_consulta_clientes.py` | Páginas, limites de navegação, listas vazias, busca no menu, correção e cancelamento de ID, seleção em outras páginas e restrição ao filtro atual. |
| `tests/test_pesquisa.py` | Busca parcial por nome sem distinguir caixa e por CPF com ou sem pontuação, termo vazio, nulos, texto literal e preservação dos dados. |

Os testes de PTY exercitam a máscara antes de Enter em um pseudoterminal Linux.
São ignorados quando `pty` ou `termios` não estão disponíveis; os demais testes
de formatação e leitura por pipe continuam separados desses casos.

Para executar só um grupo, use, por exemplo:

```bash
python3 -B -m unittest tests.test_menu -v
```
