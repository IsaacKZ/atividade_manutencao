# Limites conhecidos

- Senhas ficam em texto simples, conforme a proposta de uso local.
- Email e telefone são opcionais e não têm validação de formato.
- O cálculo do CPF não comprova que ele foi emitido.
- Duas execuções simultâneas podem cadastrar o mesmo CPF.
- A busca por nome ignora maiúsculas e minúsculas, mas diferencia acentos.
  Busca e paginação carregam a lista inteira em memória, adequadas ao cadastro
  local simples; o SQL não define uma ordem de listagem.
- A máscara ao digitar CPF depende de um terminal POSIX compatível. Windows,
  pipes e `TERM=dumb` usam leitura comum, com ou sem pontuação. A edição do
  campo permite apagar no final com Backspace e limpar com `Ctrl+U`; as setas
  são ignoradas e não movem o cursor.

## Interrupções e falhas de banco

Fim da entrada (por exemplo, `Ctrl+D` no Linux) e `Ctrl+C` encerram o programa
com uma mensagem e código `0`. Formulários incompletos não são gravados; as
operações já concluídas continuam salvas.

Erros de SQLite durante uma ação mostram orientação e retornam ao menu. Se
ocorrerem ao preparar o banco ou autenticar, o programa encerra com código `1`
e orientação sobre caminho e permissões, sem traceback. A pasta do banco
precisa existir e permitir gravação. Esses tratamentos informam o problema;
não corrigem permissões, arquivo inacessível ou bloqueios de outra execução.

## Conta da antiga versão com hash

Se a senha foi convertida pela versão anterior, redefina-a com o comando abaixo,
na pasta do projeto. Clientes e outras contas são preservados. Use o mesmo
`SISTEMA_DB_PATH` do programa, caso tenha configurado outro banco.

```bash
python3 -B -c '
from database import conectar
usuario = input("Usuário: ")
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
