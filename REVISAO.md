# Revisão após as correções

Esta revisão não altera o código do programa. Os problemas abaixo foram
reproduzidos em bancos temporários; o banco do repositório foi consultado
somente em modo de leitura.

Após a revisão, o código foi simplificado conforme `CORRECOES.md`. As conexões
agora são fechadas também nos caminhos de exceção. Os problemas de funcionamento
abaixo permanecem; as referências usam nomes de funções para acompanhar a
reorganização do código.

## Resultado da verificação

- `python3 -B -m unittest discover -v`: 12 testes executados e aprovados.
- `git diff --check`: nenhuma inconsistência de espaços no diff.
- `PRAGMA integrity_check` do banco existente: `ok`.
- O banco existente tem 1 cliente, nenhum registro com campos nulos e nenhum
  grupo de CPF duplicado. Não foram exibidos dados pessoais nem senhas.
- Os testes atuais cobrem o fluxo usual. Os cenários adicionais abaixo ainda
  não estão cobertos pela suíte de regressão.

## Problemas de funcionamento confirmados

### 1. O banco depende da pasta de onde o programa é iniciado

Local: `DB_PATH` em `database.py`.

Ao executar `python3 -B /workspace/atividade_manutencao/main.py` de outra pasta,
o programa cria ou abre `sistema.db` nessa pasta. No teste, um banco com cliente
cadastrado pareceu vazio na outra execução. Os dados originais não são apagados,
mas o usuário pode passar a cadastrar clientes em bancos diferentes sem perceber.

Correção sugerida: resolver o caminho do banco a partir da localização do
arquivo do projeto. Até lá, executar sempre da pasta do repositório, conforme
`CORRECOES.md`.

### 2. Campos nulos interrompem a listagem

Locais: `formatar_linha()` em `main.py` e `inicializar_banco()` em `database.py`.

O esquema permite `NULL` em nome, CPF, email e telefone. Um registro com email
nulo causa `TypeError` ao aplicar a formatação da tabela. A reprodução usou um
registro inserido diretamente em um banco temporário. Isso não ocorre nos dados
atuais nem nas entradas de texto do menu, mas pode afetar dados antigos ou
importados. Como edição e exclusão também listam clientes antes de pedir o ID,
essas opções igualmente ficam indisponíveis nessa condição.

Correção sugerida: representar campos opcionais nulos como texto vazio na
exibição, sem modificar automaticamente os dados existentes.

### 3. Erros de banco e fim da entrada encerram o programa com traceback

Locais: `conectar()` e `inicializar_banco()` em `database.py`, e os `input()` de
`main.py`.

Foi confirmado `OperationalError: database is locked` durante a inicialização,
quando outra conexão manteve um bloqueio exclusivo. Também foi confirmado
`EOFError` ao terminar a entrada no login e no menu (equivalente a Ctrl+D no
terminal Linux). O tratamento atual cobre `ValueError` das validações, mas não
essas situações. Não houve evidência de corrupção ou perda de dados.

Correção sugerida: tratar encerramento da entrada e apresentar uma mensagem
clara para falhas de acesso ao banco; não apresentar sucesso em uma operação
que falhou.

### 4. Nomes longos desalinham a tabela

Local: `formatar_linha()` em `main.py`.

As larguras de formatação são mínimas, não limites máximos. No teste, um nome
de 40 caracteres deslocou o email 20 posições em relação ao cabeçalho.

Correção sugerida: usar separadores entre campos ou calcular as larguras pela
lista exibida. Os valores armazenados não precisam ser cortados.

### 5. A validação de CPF duplicado falha com operações simultâneas

Locais: `validar_dados_cliente()`, `cadastrar_cliente()` e `editar_cliente()` em
`clientes.py`, e `inicializar_banco()` em `database.py`.

Duas operações podem verificar que um CPF está livre antes de qualquer uma
gravar. A reprodução sincronizou duas consultas reais e ambas as inserções
foram aceitas. A tabela não possui restrição `UNIQUE` para CPF. O problema
depende de operações concorrentes; os cadastros sequenciais são rejeitados
corretamente.

Correção sugerida: garantir unicidade no banco e tratar a violação na aplicação.
Uma migração deve verificar duplicidades existentes antes de criar a restrição.

### 6. Edição/exclusão podem indicar sucesso após remoção concorrente

Locais: `editar_cliente()` e `excluir_cliente()` em `clientes.py`.

A existência é consultada antes do `UPDATE`/`DELETE`, em outra conexão. Se
outra execução apagar o cliente nesse intervalo, a função retorna `True` mesmo
sem afetar linhas. A edição foi reproduzida com uma remoção real entre a
consulta e o `UPDATE`; a exclusão usa o mesmo padrão, mas esse cenário específico
de exclusão não foi executado.

Correção sugerida: determinar o resultado pelo número de linhas afetadas pela
própria operação, evitando depender da consulta anterior.

## Melhorias possíveis, separadas dos bugs do fluxo atual

- **Senhas:** o esquema e a autenticação usam texto puro, e bancos novos
  recebem a senha padrão conhecida `admin123`. Antes de uso com dados reais,
  adotar hash de senha e configurar credenciais próprias. A senha também aparece
  durante a digitação; `getpass` evita a exibição. Não foi realizado um scan
  completo de segurança nesta revisão.
- **Validação de CPF:** hoje ela verifica somente comprimento e `isdigit()`.
  Foram aceitos `00000000000` e 11 caracteres `²`. Verificar dígitos ASCII,
  sequências repetidas e dígitos verificadores seria uma ampliação das regras
  atuais, não parte das correções já realizadas. Aceitar CPF com pontuação
  exigiria também normalização antes de comparar duplicidade.
- **Email e telefone:** entradas vazias ou sem formato são aceitas. É necessário
  definir se esses campos devem ser opcionais antes de impor novas regras.
- **Edição:** verificar o ID antes de solicitar todos os novos dados e permitir
  preservar campos existentes reduziria trabalho desnecessário, mas mudaria
  a interação atual.
- **Repositório:** manter banco com dados e arquivos `__pycache__` fora do
  versionamento, preservar os dados locais e documentar a inicialização de um
  banco novo. Esses arquivos já são rastreados, então adicionar apenas um
  `.gitignore` não resolve o histórico nem remove o rastreamento.
- **Testes:** adicionar regressões para as falhas acima e para login inválido
  seguido de login válido no programa completo. Os 12 testes atuais não
  demonstram que todos esses cenários funcionam.

Para o uso local atual, priorizar o caminho do banco e a tolerância a campos
nulos, depois o tratamento de falhas e a exibição. Se houver uso simultâneo,
priorizar também as garantias de unicidade e o resultado das operações. Se
houver uso com dados reais, priorizar a proteção das credenciais.
