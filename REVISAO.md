# Estado atual e limites conhecidos

O programa foi simplificado para execução local. O login consulta diretamente
a senha em texto no SQLite. Não há hash, política de senha ou cadastro inicial.
Essa escolha substitui a proteção de senhas introduzida anteriormente.

As correções do menu, da edição, do CPF e do caminho do banco foram mantidas.
A edição verifica se há clientes e se o ID existe antes de pedir novos dados.
O funcionamento está descrito no [README.md](README.md), e o registro das
alterações está em [CORRECOES.md](CORRECOES.md).

## Limites que continuam fora desta alteração

- Dados importados com campos `NULL` podem interromper a formatação da lista.
- Fim da entrada (`Ctrl+D`) e falhas de banco ainda podem encerrar com traceback.
- Nomes longos podem desalinhar as colunas.
- Duas execuções simultâneas podem cadastrar o mesmo CPF, pois não há restrição
  `UNIQUE` nessa coluna. A validação cobre as operações sequenciais do programa.
- Edição e exclusão podem indicar sucesso se outro processo remover o cliente
  entre a consulta de existência e a gravação.
- Email e telefone não possuem validação de formato.
- O CPF é conferido matematicamente; não há consulta a um cadastro oficial.
- Usuários com senhas convertidas na versão anterior precisam redefini-las
  uma vez, seguindo o README. A simplificação não apaga nem redefine contas.

Os experimentos sobre nulos, concorrência e falhas de banco foram descritos na
revisão anterior, disponível no histórico do Git. Não foram repetidos nesta
simplificação. Os 35 testes atuais passaram; eles não afirmam resolver esses
limites pendentes.
