# Correções e simplificação

A versão atual mantém as correções de funcionamento e volta ao login simples
para uso local, conforme solicitado.

## O que foi simplificado

- `auth.py`: passou de várias funções de proteção de senha para uma função
  `login()`, que consulta usuário e senha no SQLite e retorna `True` ou `False`.
- Foram removidos hash, salt, iterações, migração automática, tamanho mínimo
  de senha, cadastro inicial e troca obrigatória.
- Um banco sem usuários recebe novamente a conta `admin` com senha `admin123`.
  Usuários e clientes já existentes não são apagados ou substituídos.
- Foram retirados `hashlib`, `hmac`, `secrets`, `contextlib` e `pathlib` da
  aplicação. Ela usa apenas `os` e `sqlite3` da biblioteca padrão.
- `consultar()` e `executar()`, em `database.py`, concentram a abertura e o
  fechamento das conexões. A primeira devolve resultados; a segunda confirma
  a gravação e devolve quantas linhas foram afetadas. O SQL continua visível
  nas funções de clientes e login, com os parâmetros `?`.
- Edição e exclusão usam a quantidade de linhas afetadas para indicar sucesso.
  A exclusão não precisa consultar a existência do cliente novamente no banco
  antes de executar o `DELETE`.
- A listagem usa `print()` com o separador `|`. Saíram a função de formatação
  e as cinco constantes de largura, e campos nulos passaram a aparecer vazios.
- A exclusão também verifica lista vazia e ID inexistente antes de perguntar
  pela confirmação, seguindo o mesmo fluxo da edição.

O login não modifica senhas. Contas que já tenham hash precisam de uma nova
senha definida uma vez, conforme o comando do [README.md](README.md). Não é
possível recuperar o texto de uma senha a partir do hash.

## Correções de funcionamento preservadas

| Problema | Ajuste |
| --- | --- |
| Editar diretamente encerrava o programa. | A edição lê seus próprios dados. |
| Listagem aparecia duas vezes e iniciava edição. | A opção apenas lista uma vez e volta ao menu. |
| Edição reaproveitava ID de outra ação. | Cada ação tem suas variáveis locais. |
| Edição aceitava nome vazio, CPF inválido ou CPF de outro cliente. | Cadastro e edição compartilham as validações. |
| CPF era conferido só pelo tamanho. | Cálculo dos dois verificadores com contas e laços simples. |
| Banco mudava conforme a pasta de execução. | Caminho padrão fixado na pasta do projeto. |
| Editar sem clientes pedia dados desnecessários. | Retorno imediato ao menu quando a lista está vazia. |
| ID inexistente ainda levava às perguntas de edição. | Conferência do ID antes dos novos dados. |
| Exclusão pedia ID ou confirmação sem um cliente válido. | Retorno ao menu antes de fazer essas perguntas. |
| Campos nulos interrompiam a lista e nomes longos deslocavam as colunas. | Impressão simples com separadores e campos vazios quando necessário. |

A opção `SISTEMA_DB_PATH` continua disponível para usar um banco separado.
CPFs antigos não são reescritos automaticamente. Email e telefone continuam
opcionais, e a exclusão mantém sua confirmação.

## Verificação

```bash
python3 -B -m unittest discover -v
```

A suíte atual tem 38 testes: login simples, preservação de usuários, caminho
do banco, CPF e operações de clientes, incluindo o programa real em subprocessos.
Nesta revisão, foram mantidos os 35 testes anteriores e adicionados três para
exclusão sem clientes, exclusão com ID inexistente e listagem com nome longo
e campos nulos. Os três falharam antes do ajuste e passaram depois.
Todos passaram com bancos temporários. Os testes exclusivos de hash, cadastro
inicial e troca obrigatória foram removidos porque essas funções deixaram de
existir. Os testes das correções de funcionamento foram mantidos.

O `sistema.db` original e os arquivos de bytecode rastreados não foram alterados.
