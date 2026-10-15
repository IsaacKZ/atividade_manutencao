# Correções de funcionamento

Este documento reúne as sete correções solicitadas e as orientações para
verificá-las. O [README.md](README.md) contém os comandos de execução e um
roteiro manual com banco descartável.

## O que mudou

| Problema | Antes | Agora | Arquivos |
| --- | --- | --- | --- |
| 1. Edição encerrava o programa | Escolher `3` diretamente podia causar `UnboundLocalError`: os dados só eram lidos na opção `2`. | A própria edição solicita o ID e os novos dados antes de usá-los. | `main.py` |
| 2. Listagem iniciava edição | A opção `2` mostrava a lista duas vezes e solicitava dados de edição. | A lista aparece uma vez e a opção retorna ao menu. | `main.py` |
| 3. Edição podia usar dados de outra ação | Variáveis compartilhadas entre opções podiam reaproveitar o ID e os dados anteriores, alterando o cliente errado. | Cada ação tem sua função e a edição usa os valores informados naquela chamada. | `main.py` |
| 4. Edição burlava a validação | Era possível gravar nome vazio, CPF inválido ou CPF de outro cliente. | Cadastro e edição compartilham a validação; o cliente pode manter o próprio CPF, mas não usar o de outro. O menu mostra o erro e continua. | `clientes.py`, `main.py` |
| 5. CPF sem dígitos verificadores | Comprimento e `isdigit()` aceitavam sequências repetidas, caracteres numéricos não ASCII e CPFs matematicamente inválidos. | São exigidos 11 dígitos ASCII, rejeição de sequência uniforme e cálculo dos dois verificadores. | `clientes.py` |
| 6. Senhas em texto puro e conta padrão | Senhas eram comparadas em texto puro e um banco novo recebia automaticamente uma conta com credenciais conhecidas. | O primeiro usuário escolhe sua senha; novas senhas recebem PBKDF2-SHA256 e salt aleatório. Senhas antigas são migradas após autenticação correta. A antiga senha padrão precisa ser substituída antes do menu. | `auth.py`, `database.py`, `main.py` |
| 7. Banco dependia da pasta atual | `sistema.db` relativo podia abrir bancos diferentes conforme a pasta de execução. | O padrão aponta para o banco ao lado de `database.py`; `SISTEMA_DB_PATH` permite escolher outro arquivo. Prefira um caminho absoluto no override. | `database.py` |

## Código simples e reaproveitamento

As primeiras correções de menu e validação já estavam acompanhadas de uma
simplificação do código. Ela foi preservada:

- Cada ação do menu tem uma função curta. `ler_dados_cliente()` reúne as
  perguntas de cadastro e edição, e `iniciar()` é o ponto de entrada.
- `validar_dados_cliente()` reúne as regras comuns. A consulta de CPF recebe
  o ID na edição para desconsiderar o próprio cliente.
- A verificação dos dígitos do CPF usa `for`, operações aritméticas e `if`.
- As consultas usam `conexao.execute()` com parâmetros; `closing()` garante
  o fechamento das conexões e as gravações mantêm `commit()` explícito.

Não há bibliotecas externas. Para senhas, o uso de `hashlib`, salt aleatório e
comparação apropriada da biblioteca padrão evita criar um algoritmo de
segurança próprio. Essa parte serve para não armazenar novas senhas como texto
legível; a senha ainda aparece enquanto é digitada no terminal.

## Preservação dos dados existentes

As tabelas e os clientes antigos são preservados. A inicialização não limpa o
banco, não troca todos os usuários nem reescreve CPFs inválidos. As novas regras
de cliente são aplicadas nas operações de cadastro e edição.

Uma senha antiga em texto puro só é convertida após a senha correta ser
informada. A migração preserva a senha escolhida e os demais dados. A conta
legada `admin` com senha `admin123` exige uma senha nova antes de entrar no
menu; manter uma senha padrão pública não seria corrigido apenas pelo hash.
Senhas criadas ou trocadas precisam ter pelo menos 8 caracteres e ser
diferentes de `admin123`.

Essas mudanças não apagam cópias de senhas em backups ou no histórico do Git.
O banco versionado contém dados históricos de demonstração: não acrescente
dados pessoais reais a ele para enviar ao repositório.

O cálculo do CPF confere os verificadores, mas não consulta um cadastro oficial
nem demonstra que o documento foi emitido. Email e telefone continuam sem
validação de formato. Outros problemas conhecidos estão em
[REVISAO.md](REVISAO.md).

## Verificação

Execute a partir da pasta do repositório:

```bash
python3 -B -m unittest discover -v
```

A suíte reúne `test_sistema.py` e os testes em `tests/`. Ela verifica as
regressões de menu, validação compartilhada, CPFs, autenticação, migração e
localização do banco usando arquivos SQLite temporários. Os testes não
precisam modificar o banco original. Na verificação desta versão, os 50 testes
foram aprovados. O banco original e os caches rastreados ficaram sem alterações.

Na etapa anterior da manutenção, a documentação registrou a comparação de
nove cenários antes e depois da simplificação: login inválido seguido de
válido, opção inválida e lista vazia, cadastro e listagem, cadastros inválidos,
CPF duplicado, edição mantendo CPF, edições inválidas e duplicadas, IDs
inexistentes e exclusão cancelada ou confirmada. Essa comparação pertencia à
refatoração anterior; ela não substitui executar a suíte da versão atual.

Para conferir interativamente as correções, siga a seção de teste manual do
[README.md](README.md), usando os CPFs de teste `52998224725` e `11144477735` e
um banco descartável fora do repositório.
