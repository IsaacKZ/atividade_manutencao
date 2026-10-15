# Limites conhecidos

- Senhas ficam em texto simples, conforme a proposta de uso local.
- Email e telefone são opcionais e não têm validação de formato.
- O cálculo do CPF não comprova que ele foi emitido.
- Duas execuções simultâneas podem cadastrar o mesmo CPF.
- Fim da entrada (`Ctrl+D`) e erros de banco podem encerrar o programa.

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
