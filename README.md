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
  - Histórico de execução
  - Ambientes e variáveis

- **Interface**
  - Tema escuro e claro
  - Sidebar com coleções
  - Painel de requisição
  - Painel de resposta
  - Janela de ambientes
  - Janela de histórico

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
- suporte a scripts pré e pós requisição.

---

## Observações

- Este projeto foi pensado para uso local.
- O banco de dados fica armazenado na máquina do usuário.
- O design foi planejado para ser simples, moderno e fácil de expandir.

---

## Licença

Use e adapte livremente conforme sua necessidade.