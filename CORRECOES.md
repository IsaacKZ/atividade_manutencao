# O que foi ajustado

- Login simples, sem hash ou troca obrigatória de senha.
- Listagem exibida uma vez, com separadores e suporte a campos nulos.
- Edição e exclusão param se não houver clientes ou se o ID não existir.
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

Os testes cobrem essas operações. Comandos de uso e teste: [README.md](README.md).
