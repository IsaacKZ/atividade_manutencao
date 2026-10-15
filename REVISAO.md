# Estado atual e limites conhecidos

O programa foi simplificado para execução local. O login consulta diretamente
a senha em texto no SQLite. Não há hash, política de senha ou cadastro inicial.
Essa escolha substitui a proteção de senhas introduzida anteriormente.

As correções do menu, da edição, do CPF e do caminho do banco foram mantidas.
Edição e exclusão verificam se há clientes e se o ID existe antes das perguntas
seguintes. A listagem aceita campos nulos e nomes longos, e operações de
gravação conferem quantas linhas foram afetadas para indicar sucesso.
O funcionamento está descrito no [README.md](README.md), e o registro das
alterações está em [CORRECOES.md](CORRECOES.md).

## Limites que continuam fora desta alteração

- Fim da entrada (`Ctrl+D`) e falhas de banco ainda podem encerrar com traceback.
- Duas execuções simultâneas podem cadastrar o mesmo CPF, pois não há restrição
  `UNIQUE` nessa coluna. A validação cobre as operações sequenciais do programa.
- Email e telefone não possuem validação de formato.
- O CPF é conferido matematicamente; não há consulta a um cadastro oficial.
- Usuários com senhas convertidas na versão anterior precisam redefini-las
  uma vez, seguindo o README. A simplificação não apaga nem redefine contas.

Experimentos anteriores sobre concorrência e falhas de banco estão no histórico
do Git. Eles não foram repetidos nesta revisão. O resultado da suíte atual está
em `CORRECOES.md`; ela não afirma resolver os limites pendentes acima.
