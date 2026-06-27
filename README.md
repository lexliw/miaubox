# MiauBox 🐱📦

MiauBox é uma ferramenta estilo Postman feita em Python, com interface moderna em **CustomTkinter**, backend de execução de requisições com **httpx** e persistência local em **SQLite** via **SQLAlchemy**.

A proposta é permitir:

- criar e organizar **coleções** de requisições;
- trabalhar com **ambientes** e variáveis como `{{VAR_NAME}}`;
- executar requisições HTTP com suporte a **headers, params, body e autenticação**;
- visualizar a **resposta formatada**, status code e tempo de resposta;
- consultar o **histórico** das requisições executadas.

---

## Funcionalidades

- **Execução de requisições HTTP**
  - `GET`
  - `POST`
  - `PUT`
  - `PATCH`
  - `DELETE`

- **Suporte a dados de requisição**
  - Headers
  - Query params
  - Body em:
    - JSON
    - XML
    - form-data
    - raw

- **Autenticação**
  - Bearer Token
  - Basic Auth
  - API Key

- **Ambientes**
  - Criação de ambientes
  - Seleção de ambiente ativo
  - Variáveis por ambiente
  - Substituição automática com sintaxe `{{VAR_NAME}}`

- **Persistência local**
  - Coleções
  - Requisições salvas
  - Requisições salvas com scripts pré e pós-requisição
  - Histórico de execução
  - Ambientes e variáveis

- **Interface**
  - Tema escuro e claro
  - Sidebar com coleções
  - Painel de requisição
  - Painel de resposta
  - Janela de ambientes
  - Janela de histórico

- **Automação com scripts**
  - Script pré-requisição em Python
  - Script pós-requisição em Python
  - Acesso a `request`, `response` e `env`
  - Logs de execução exibidos na interface

---

## Arquitetura

A aplicação está organizada em três camadas principais:

- **Backend**
  - Regras de negócio
  - Banco de dados local
  - Execução das requisições
  - Gerenciamento de variáveis de ambiente

- **Interface gráfica**
  - Construída com **CustomTkinter**
  - Responsável pela experiência do usuário

- **Persistência**
  - Banco **SQLite** local
  - Acesso via **SQLAlchemy**

---

## Estrutura do Projeto

```txt
miaubox/
├── main.py
├── requirements.txt
├── miaubox.db
├── backend/
│   ├── __init__.py
│   ├── database.py
│   ├── env_manager.py
│   └── request_runner.py
├── ui/
│   ├── __init__.py
│   ├── app.py
│   ├── sidebar.py
│   ├── request_panel.py
│   ├── response_panel.py
│   ├── environment_dialog.py
│   ├── history_window.py
│   └── styles.py
└── assets/
    └── .gitkeep
```

> Observação: neste momento, os modelos do banco estão concentrados em `backend/database.py`, então **não é necessário um arquivo `models.py` separado**.

---

## Requisitos

- **Python 3.12+**
- Sistema com suporte a interface gráfica
- Conexão com internet para testar APIs externas

---

## Instalação local

### 1. Criar um ambiente virtual

No Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

No Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Instalar as dependências

```bash
pip install -r requirements.txt
```

### 3. Inicializar o banco

O banco SQLite é criado automaticamente na primeira execução.

Se quiser inicializar manualmente, basta rodar a aplicação uma vez.

---

## Como executar

Na raiz do projeto, execute:

```bash
python main.py
```

Isso irá:

- criar as tabelas no SQLite, se ainda não existirem;
- abrir a interface do MiauBox;
- permitir criar requisições, coleções e ambientes.

---

## Como a aplicação funciona

### 1. Criar ou carregar uma requisição
Você pode montar uma requisição com:

- método HTTP;
- URL;
- headers;
- params;
- body;
- autenticação.

### 2. Executar a requisição
Ao clicar em enviar:

- variáveis como `{{BASE_URL}}` são substituídas pelo valor do ambiente ativo;
- a requisição é enviada com `httpx`;
- o resultado é exibido na tela;
- a execução é salva no histórico.

### 3. Salvar a requisição
As requisições podem ser salvas no banco local para reutilização futura.

### 4. Gerenciar ambientes
Você pode criar ambientes como:

- `dev`
- `staging`
- `prod`

E definir variáveis como:

- `BASE_URL`
- `TOKEN`
- `API_VERSION`

Exemplo:

```txt
{{BASE_URL}}/users
Authorization: Bearer {{TOKEN}}
```

### 5. Ver histórico
Toda requisição executada fica registrada com:

- método;
- URL;
- status code;
- tempo de resposta;
- data de execução.

---

## Variáveis de ambiente

A substituição de variáveis usa a sintaxe:

```txt
{{VAR_NAME}}
```

Exemplos:

```txt
{{BASE_URL}}/login
```

```json
{
  "token": "{{TOKEN}}"
}
```

Se a variável não existir no ambiente ativo, o texto é mantido como está.

---

## Scripts pré e pós-requisição

O MiauBox permite executar scripts em **Python** antes e depois do envio da requisição.

Isso permite automatizar ajustes no request, processar a resposta e salvar valores em variáveis de ambiente.

### O que é possível fazer

#### Pré-script
Executado **antes** do envio da requisição.

Você pode:

- alterar `request.url`
- alterar `request.headers`
- alterar `request.params`
- alterar `request.body`
- ler e gravar variáveis de ambiente com `env["CHAVE"]`

#### Pós-script
Executado **depois** que a resposta é recebida.

Você pode:

- ler `response.status_code`
- ler `response.headers`
- acessar o corpo com `response.json()`
- acessar o conteúdo bruto com `response.raw`
- salvar valores da resposta em `env["CHAVE"]`

### Objetos disponíveis no script

#### `request`
Disponível no pré-script e no pós-script.

- `request.method`
- `request.url`
- `request.headers`
- `request.params`
- `request.body`

#### `response`
Disponível apenas no pós-script.

- `response.status_code`
- `response.headers`
- `response.json()`
- `response.raw`

#### `env`
Disponível no pré-script e no pós-script.

- `env["CHAVE"]` para ler uma variável
- `env["CHAVE"] = "valor"` para salvar uma variável

### Logs de execução

Qualquer `print()` usado no script aparece no log de execução da aba de script.

Exemplo:

```python
print("Executando pré-script...")
```

### Fluxo de execução

1. O pré-script é executado, se existir.
2. A requisição HTTP é enviada.
3. O pós-script é executado, se existir.
4. O resultado e o log são exibidos na interface.

### Exemplos de uso

#### 1. Alterar o body antes do envio

```python
import json

payload = json.loads(request.body)
payload["title"] = "Título alterado no pré-script"
payload["userId"] = 10
request.body = json.dumps(payload)
```

#### 2. Usar uma variável de ambiente no body

```python
import json

payload = json.loads(request.body)
payload["title"] = env["USER_ID"]
request.body = json.dumps(payload)
```

#### 3. Adicionar um header dinamicamente

```python
request.headers["X-Trace-Id"] = "trace-123"
```

#### 4. Ajustar query params antes do envio

```python
request.params["page"] = "1"
request.params["limit"] = "20"
```

#### 5. Salvar um valor da resposta no ambiente

```python
if response.status_code == 200:
    data = response.json()
    env["LAST_USER_ID"] = str(data["id"])
```

#### 6. Exibir informações no log

```python
print("Status:", response.status_code)
print("Body original:", request.body)
```

### Exemplo completo de pré-script

```python
import json

print("Executando pré-script...")

payload = json.loads(request.body)
payload["title"] = env["USER_ID"]
payload["body"] = "Conteúdo alterado no pré-script"
request.body = json.dumps(payload)

request.headers["X-App"] = "MiauBox"
print("Body final:", request.body)
```

### Exemplo completo de pós-script

```python
print("Status:", response.status_code)

if response.status_code == 201:
    data = response.json()
    env["LAST_CREATED_ID"] = str(data["id"])
    print("ID salvo em LAST_CREATED_ID")
```

### Observações

- O corpo da requisição (`request.body`) deve estar no formato esperado pela API.
- Para payloads JSON, o padrão é usar `json.loads()` para ler e `json.dumps()` para salvar.
- Os scripts são salvos junto com a requisição e recarregados quando ela é aberta novamente.

---

## Exportação e importação

A aplicação suporta:

- exportação de ambientes em JSON;
- importação de ambientes a partir de JSON;
- futura expansão para exportação de coleções.

---

## Banco de dados

O projeto usa **SQLite** com SQLAlchemy.

Arquivo padrão:

```txt
miaubox.db
```

Ele armazena:

- coleções;
- requisições salvas;
- histórico;
- ambientes;
- variáveis de ambiente.

---

## Dependências principais

- `customtkinter` — interface moderna
- `httpx` — execução de requisições HTTP
- `sqlalchemy` — ORM e acesso ao banco
- `Pillow` — manipulação de imagens
- `pygments` — apoio para formatação/realce de texto

---

## Roadmap sugerido

- melhor suporte a `form-data`;
- autenticação OAuth2;
- editor de JSON com validação;
- suporte a múltiplos ambientes importados;
- exportação de coleções;
- testes automatizados de resposta;
- temas personalizados;
- atalhos de teclado;
- melhorias no editor de scripts;
- autocomplete para variáveis e campos;
- validação de scripts antes de salvar.

---

## Observações

- Este projeto foi pensado para uso local.
- O banco de dados fica armazenado na máquina do usuário.
- O design foi planejado para ser simples, moderno e fácil de expandir.

---

## Licença

Use e adapte livremente conforme sua necessidade.