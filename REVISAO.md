# Estado dos problemas da revisão

A revisão anterior reproduziu problemas em bancos temporários e consultou o
banco do repositório somente em modo de leitura. Esta atualização registra o
que foi corrigido na manutenção e o que ainda permanece fora de seu escopo.
As observações históricas não são uma nova execução dos mesmos experimentos.

## Corrigidos nesta manutenção

- **Caminho do banco:** o arquivo padrão fica ao lado de `database.py`,
  independentemente da pasta atual. Para outro banco, prefira um caminho
  absoluto em `SISTEMA_DB_PATH`.
- **CPF:** a validação agora confere caracteres ASCII, sequências uniformes e
  os dois dígitos verificadores. Cadastro e edição usam as mesmas regras.
- **Senhas e primeiro acesso:** bancos novos não recebem conta com senha
  fixa. Há criação inicial de usuário e hash PBKDF2-SHA256 com salt aleatório;
  contas antigas são migradas após login correto. A credencial legada
  `admin`/`admin123` precisa ser substituída antes de acessar o menu.
- **Menu e edição:** as opções têm dados próprios, a lista aparece uma vez,
  editar diretamente funciona e erros de validação não encerram o menu.

A suíte atual foi executada com `python3 -B -m unittest discover -v`: 50 testes
aprovados. O banco original e os arquivos de cache rastreados permaneceram sem
alterações. Os detalhes antes/depois estão em [CORRECOES.md](CORRECOES.md);
o roteiro manual está em [README.md](README.md).

## Problemas de funcionamento ainda pendentes

### 1. Campos nulos podem interromper a listagem

Locais: `formatar_linha()` em `main.py` e `inicializar_banco()` em `database.py`.

O esquema permite `NULL` em nome, CPF, email e telefone. Na revisão anterior,
um registro com email nulo causou `TypeError` ao formatar a tabela. O registro
foi inserido diretamente em um banco temporário. As entradas de texto do menu
não produzem esse caso, mas dados antigos ou importados podem produzi-lo.
Edição e exclusão também exibem a lista antes de pedir o ID e podem ser afetadas.

Possível correção futura: mostrar campos opcionais nulos como texto vazio,
sem modificar automaticamente os dados existentes.

### 2. Erros de banco e fim da entrada podem encerrar com traceback

Locais: `conectar()` e `inicializar_banco()` em `database.py`, e os `input()` de
`main.py`.

A revisão anterior confirmou `OperationalError: database is locked` quando
outra conexão manteve um bloqueio exclusivo na inicialização. Também confirmou
`EOFError` ao terminar a entrada no login e no menu, como em Ctrl+D no Linux.
O tratamento de `ValueError` das validações não cobre todas essas situações.
Não foi observada corrupção ou perda de dados nesses experimentos.

Possível correção futura: tratar fim da entrada e apresentar mensagens claras
para falhas de acesso ao banco, sem anunciar sucesso quando a operação falhar.

### 3. Nomes longos desalinham a tabela

Local: `formatar_linha()` em `main.py`.

As larguras usadas na formatação são mínimas, não limites máximos. Na revisão
anterior, um nome de 40 caracteres deslocou o email em relação ao cabeçalho.

Possível correção futura: usar separadores ou calcular larguras pela lista
exibida, sem cortar os valores armazenados.

### 4. Operações simultâneas podem gravar o mesmo CPF

Locais: `validar_dados_cliente()`, `cadastrar_cliente()` e `editar_cliente()` em
`clientes.py`, e `inicializar_banco()` em `database.py`.

Duas operações podem verificar que um CPF está livre antes de qualquer uma
gravar. A revisão anterior sincronizou duas consultas reais e ambas as
inserções foram aceitas. A tabela não possui restrição `UNIQUE` para CPF.
As novas verificações matemáticas não resolvem essa disputa; operações
sequenciais continuam rejeitando o CPF de outro cliente.

Possível correção futura: garantir unicidade no banco e tratar a violação na
aplicação. A migração precisaria conferir dados duplicados antes de criar a
restrição, sem apagar clientes silenciosamente.

### 5. Remoção concorrente pode produzir uma mensagem de sucesso incorreta

Locais: `editar_cliente()` e `excluir_cliente()` em `clientes.py`.

A existência é consultada antes do `UPDATE` ou `DELETE`, em outra conexão.
Se outra execução remover o cliente nesse intervalo, a função pode retornar
`True` sem afetar linhas. A revisão anterior reproduziu a edição com uma
remoção real entre consulta e gravação. A exclusão usa o mesmo padrão, mas
aquele experimento específico não foi executado para exclusão.

Possível correção futura: determinar o resultado pelo número de linhas
afetadas pela própria operação.

## Outros limites e possíveis melhorias

- **Entrada de senhas:** a senha ainda aparece enquanto é digitada, pois a
  interface usa `input()`. A troca para `getpass` é uma melhoria pendente;
  a proteção do armazenamento não esconde o que aparece no terminal.
- **Migração de senhas:** converter o banco atual não elimina texto puro de
  backups e do histórico do Git. Credenciais expostas ou reutilizadas precisam
  ser trocadas. Esta manutenção não equivale a uma auditoria completa de segurança.
- **CPF:** os verificadores não comprovam emissão ou identidade. O programa
  exige dígitos sem pontuação; aceitar pontos e hífen exigiria normalização
  antes da comparação de duplicidade.
- **Email e telefone:** continuam aceitando entradas vazias ou sem formato.
  É preciso definir as regras desses campos antes de restringi-los.
- **Edição:** o programa ainda solicita todos os dados antes de verificar o ID.
  Conferir o ID primeiro e permitir manter campos reduziria trabalho, mas
  mudaria a interação atual.
- **Repositório:** o banco histórico de demonstração e arquivos gerados já
  rastreados precisam de tratamento próprio se forem removidos do versionamento.
  Um `.gitignore` sozinho não apaga arquivos ou dados já presentes no histórico.
  Não envie novos dados pessoais reais ou senhas ao repositório.
- **Testes futuros:** acrescentar regressões específicas ao corrigir campos
  nulos, fim da entrada, falhas de banco e concorrência. Passar na suíte atual
  não demonstra que esses problemas pendentes foram resolvidos.

Para uso local, os próximos trabalhos possíveis são a tolerância a campos
nulos, o encerramento de entrada e as mensagens de falha. Se houver várias
execuções simultâneas, também são necessárias garantias no banco para CPF
único e resultados de edição e exclusão.
