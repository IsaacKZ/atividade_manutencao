# Correções de funcionamento

## Bugs corrigidos

- **Listagem iniciava uma edição:** a opção 2 exibia a lista duas vezes e
  solicitava os dados de edição. A coleta desses dados foi movida para a opção 3.
- **Edição encerrava o programa:** selecionar a opção 3 diretamente causava
  `UnboundLocalError`, pois os dados só eram definidos na opção 2. Agora a
  própria opção de edição solicita o ID e os novos dados.
- **Edição burlava a validação do cadastro:** era possível salvar nome vazio,
  CPF sem os 11 dígitos exigidos ou CPF pertencente a outro cliente. A edição
  aplica as mesmas regras existentes no cadastro, permitindo manter o CPF do
  próprio cliente. Nenhuma validação adicional de CPF foi introduzida.
- **Tratamento de erro na edição:** o menu apresenta a mensagem de validação
  e continua funcionando, como já ocorria no cadastro. Dados rejeitados não
  são gravados.

Não foram adicionadas funcionalidades nem alterados o esquema ou os dados do
banco existente. As correções iniciais estão em `main.py` e `clientes.py`.

## Simplificação posterior

- `main.py`: cada ação do menu tem uma função curta. `ler_dados_cliente()`
  reúne as perguntas comuns a cadastro e edição, e `iniciar()` apresenta
  o ponto de entrada do programa.
- `clientes.py`: `validar_dados_cliente()` reúne as regras que cadastro e
  edição já aplicavam. A consulta de CPF distingue cadastro e edição com um
  `if`, deixando explícito que o cliente pode manter o próprio CPF.
- `auth.py`, `clientes.py` e `database.py`: as consultas usam
  `conexao.execute()` diretamente, sem criar variáveis de cursor separadas.
  `closing()` fecha as conexões mesmo quando ocorre uma exceção; as gravações
  mantêm `commit()` explícito.
- Comentários redundantes e anotações antigas de erros foram removidos.
  `README.md` explica como executar e acompanhar o fluxo do código.

A simplificação preserva opções, perguntas, mensagens, regras de validação,
assinaturas das funções existentes e esquema do banco. Não adiciona bibliotecas
externas. Os problemas funcionais restantes continuam descritos em `REVISAO.md`.

## Executar no ambiente de desenvolvimento

O programa usa somente a biblioteca padrão do Python (incluindo SQLite).
Validado com Python 3.12.14; não é necessário instalar pacotes ou iniciar
serviços externos.

Execute a partir da pasta do repositório, pois `sistema.db` é um caminho relativo:

```bash
cd /workspace/atividade_manutencao
python3 -B main.py
```

Em um banco recém-inicializado, o usuário padrão é `admin` e a senha é
`admin123`. Um banco existente preserva seus usuários.

## Verificação

```bash
cd /workspace/atividade_manutencao
python3 -B -m unittest discover -v
```

Foram executados 12 testes em `test_sistema.py`, todos aprovados após as
correções. Antes delas, 8 falhavam. A suíte verifica login, inicialização
repetida, cadastro, listagem, edição válida e inválida, IDs inexistentes e
exclusão cancelada ou confirmada. Os testes do menu executam o programa real
em subprocessos. Cada teste usa um banco SQLite temporário, sem modificar o
`sistema.db` do repositório.

Após a simplificação, os 12 testes continuam aprovados. Também foram comparados
9 cenários do programa completo antes e depois da refatoração: login inválido
seguido de válido, opção inválida e lista vazia, cadastro e listagem, cadastros
inválidos, cadastro duplicado, edição mantendo CPF, edições inválidas e com CPF
duplicado, IDs inexistentes e exclusão cancelada ou confirmada. As saídas do
terminal, os clientes gravados e as colunas e índices das tabelas foram iguais.
A comparação usou bancos temporários e um snapshot local do código anterior;
os cenários adicionais não foram incorporados como novos testes na suíte.
