# Case – API de Chat com Agente de IA (FastAPI + Strands + Ollama)

Este repositório contém a implementação de uma **API de Chat** simples utilizando **FastAPI** integrada a um **Agente de IA** com o **Strands Agents SDK**, utilizando a **Ollama** como LLM local.  
O agente é capaz de:

- Responder perguntas de conhecimento geral.
- Identificar quando uma pergunta envolve **cálculo matemático**.
- Utilizar uma **tool de cálculo** (função Python) para resolver operações matemáticas.

---

## 🧩 Objetivo do Case

Atender aos requisitos descritos no PDF do desafio:

- Criar uma API `POST /chat` com FastAPI.
- Integrar essa API a um agente de IA (Strands Agents).
- Configurar uma **Tool de Cálculo Matemático** para o agente.
- Rodar tudo localmente usando **Ollama** como modelo de linguagem.

---

## 🏗️ Arquitetura Geral

Visão geral do fluxo:

1. O usuário envia uma requisição `POST /chat` com um JSON:
   ```json
   { "message": "Quanto é 2+2?" }
   ```
2. O FastAPI recebe a mensagem e chama a função `run_agent(message)`.
3. `run_agent` encaminha a mensagem para um `Agent` do Strands:
   - O `Agent` usa o modelo configurado via `OllamaModel`.
   - Tem acesso a uma tool Python chamada `calcular`, usada para operações matemáticas.
4. O agente decide, com base na pergunta:
   - Se deve responder diretamente com conhecimento geral, ou
   - Se deve chamar a tool `calcular` para fazer contas.
5. A resposta final volta para o FastAPI e é retornada ao cliente como:
   ```json
   { "response": "A resposta para a pergunta "Quanto é 2+2?" é 4." }
   ```

---

## 📁 Estrutura do Projeto

Exemplo de estrutura:

```
.
├── main.py          # API FastAPI (/chat)
├── agent.py         # Definição do Agent, tools e integração com Ollama
├── requirements.txt # Dependências do projeto
├── .env             # Variáveis de ambiente (NÃO versionado)
├── .gitignore       # Arquivos e pastas ignorados pelo Git
└── README.md        # Este documento
```

---

## ⚙️ Configuração do Ambiente

### 1. Pré-requisitos

- **Python 3.10+** instalado
- **Ollama** instalado e rodando localmente  
  - Site oficial: [https://ollama.com/](https://ollama.com/)
  - Após instalar, certifique-se de ter baixado um modelo, por exemplo:
    ```bash
    ollama pull llama3.1
    ```

### 2. Clonar o repositório

```bash
git clone https://github.com/Davi-SR/IA-DreamSquad.git
cd IA-DreamSquad
```

### 3. (Opcional, mas recomendado) Criar ambiente virtual

Mesmo que você não tenha usado, é boa prática sugerir:

```bash
python -m venv venv
source venv/bin/activate      # Linux/macOS
venv\Scripts\ctivate         # Windows
```

### 4. Instalar dependências

```bash
pip install -r requirements.txt
```

O `requirements.txt` inclui, por exemplo:

- `fastapi`
- `uvicorn`
- `python-dotenv`
- `strands-agents` (com suporte a Ollama)
- outros pacotes necessários ao projeto

---

## 🔐 Variáveis de Ambiente (`.env`)

Todas as configurações de modelo e host da LLM são feitas via `.env` (ou variáveis de ambiente).

Crie um arquivo `.env` na raiz do projeto com conteúdo semelhante a:

```env
# Modelo a ser usado no Ollama
LLM_MODEL=llama3.1

# URL do servidor Ollama
OLLAMA_BASE_URL=http://localhost:11434
```

- `LLM_MODEL` → nome do modelo dentro do Ollama (ex.: `llama3.1`).
- `OLLAMA_BASE_URL` → endereço do servidor do Ollama (por padrão, `http://localhost:11434`).

O carregamento dessas variáveis é feito no `agent.py` com:

```python
from dotenv import load_dotenv
import os

load_dotenv()

LLM_MODEL = os.getenv("LLM_MODEL", "llama3.1")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
```

---

## 🧠 Implementação do Agente (Strands + Ollama)

Toda a lógica do agente está em `agent.py`.

### 1. Tool de Cálculo Matemático

```python
from strands import tool
import math

@tool
def calcular(expressao: str) -> str:
    """
    Avalia uma expressão matemática simples em Python e retorna o resultado.
    Exemplo: "1234 * 5678" ou "math.sqrt(144)"
    """
    contexto_seguro = {
        "math": math,
        "__builtins__": {}
    }

    try:
        resultado = eval(expressao, contexto_seguro, {})
        return str(resultado)
    except Exception as e:
        return f"Erro ao calcular: {e}"
```

- Decorador `@tool` → registra a função como **tool** que o agente pode chamar.
- Usa `eval` com um **contexto seguro** (`math` e sem `__builtins__`) para evitar execução de código perigoso.
- Retorna o resultado como string.

### 2. Configuração do modelo Ollama

```python
from strands.models.ollama import OllamaModel

ollama_model = OllamaModel(
    host=OLLAMA_BASE_URL,
    model_id=LLM_MODEL,
)
```

- `host` → URL do servidor Ollama.
- `model_id` → nome do modelo definido no `.env`.

Esse objeto é o “conector” entre o Strands e o Ollama.

### 3. Definição do Agent

```python
from strands import Agent

agent = Agent(
    model=ollama_model,
    tools=[calcular],
    system_prompt=(
        "Você é um assistente de IA. "
        "Quando a pergunta envolver cálculos matemáticos ou operações numéricas, "
        "use a ferramenta 'calcular' passando apenas a expressão matemática. "
        "Caso contrário, responda normalmente com seu conhecimento."
    ),
)
```

- `model=ollama_model` → define qual LLM o agente usa.
- `tools=[calcular]` → ferramentas disponíveis para o agente.
- `system_prompt` → instruções de comportamento:
  - orienta o uso da tool de cálculo,
  - orienta respostas normais para perguntas de conhecimento geral.

### 4. Função `run_agent`

```python
async def run_agent(message: str) -> str:
    """
    Recebe a mensagem do usuário, envia para o agente e retorna APENAS o texto principal da resposta.

    Estratégia:
    1. Chama o agente com a mensagem.
    2. Tenta extrair response["content"][0]["text"], que é o formato mais comum.
    3. Se não conseguir, devolve a resposta convertida para string.
    """
    # 1. Envia a mensagem para o agente e espera a resposta
    response = await agent.invoke_async(message)

    # 2. Se a resposta for um dicionário no formato:
    #    {"role": "assistant", "content": [{"text": "alguma coisa"}]}
    if isinstance(response, dict):
        content = response.get("content")
        if isinstance(content, list) and content:
            first_item = content[0]
            if isinstance(first_item, dict) and "text" in first_item:
                return str(first_item["text"])

    # 3. Se a resposta já for string, só devolve
    if isinstance(response, str):
        return response

    # 4. Se tiver atributo .content com lista semelhante
    if hasattr(response, "content"):
        c = response.content
        if isinstance(c, list) and c:
            first_item = c[0]
            if isinstance(first_item, dict) and "text" in first_item:
                return str(first_item["text"])
        return str(c)

    # 5. Fallback: devolve qualquer coisa como string
    return str(response)
```

**Resumo conceitual**:

- `invoke_async(message)` → chama o agente (Strands + Ollama + tools).
- A função tenta “desembrulhar” a resposta para pegar apenas o texto (`"text"`) retornado pelo agente.
- Sempre retorna uma `str`, que será enviada ao cliente pela API.

---

## 🌐 Implementação da API (FastAPI)

Toda a API está em `main.py`.

### 1. Modelos de Entrada/Saída

```python
from fastapi import FastAPI
from pydantic import BaseModel
from agent import run_agent

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

app = FastAPI()
```

- `ChatRequest` → define o formato do JSON de entrada:
  ```json
  { "message": "texto do usuário" }
  ```
- `ChatResponse` → define o formato do JSON de saída:
  ```json
  { "response": "resposta do agente" }
  ```

### 2. Endpoint `/chat`

```python
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(body: ChatRequest):
    user_message = body.message
    resposta_do_agente = await run_agent(user_message)
    return ChatResponse(response=resposta_do_agente)
```

Fluxo:

1. Recebe `POST /chat` com um corpo JSON `{"message": "..."}`.
2. Extrai `body.message` para `user_message`.
3. Chama `await run_agent(user_message)` para obter a resposta da IA.
4. Retorna um `ChatResponse` com o campo `response`.

---

## ▶️ Como Executar o Projeto

1. Certifique-se de que o **Ollama** está instalado e rodando:
   ```bash
   ollama serve
   ```
   E que o modelo configurado no `.env` (ex.: `llama3.1`) já foi baixado:
   ```bash
   ollama pull llama3.1
   ```

2. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

3. Execute o servidor FastAPI com Uvicorn:

   ```bash
   uvicorn main:app --reload
   ```

4. Acesse a documentação interativa (Swagger UI):

   - http://127.0.0.1:8000/docs

5. Teste o endpoint `/chat`:

   - Exemplo de entrada (no `/docs` → `POST /chat`):

     ```json
     {
       "message": "Quanto é 2+2?"
     }
     ```

   - Exemplo de saída:

     ```json
     {
       "response": "A resposta para a pergunta "Quanto é 2+2?" é 4."
     }
     ```

   - Pergunta de conhecimento geral:

     ```json
     {
       "message": "Quem foi Albert Einstein?"
     }
     ```

---

## ✅ Requisitos Atendidos (segundo o PDF)

1. **Configuração do Ambiente**
   - `.env` com configurações do modelo e host do LLM.
   - `requirements.txt` com dependências (FastAPI, Strands, python-dotenv, etc.).

2. **Implementação da API (FastAPI)**
   - Endpoint `POST /chat` que recebe `{"message": "..."}` e retorna `{"response": "..."}`.
   - Executável via `uvicorn main:app --reload`.

3. **Implementação do Agente (Strands Agents)**
   - Agente configurado com `OllamaModel`.
   - Tool de cálculo matemático (`@tool calcular`).
   - Capaz de responder:
     - Perguntas matemáticas (ex.: `"Quanto é 1234 * 5678?"`, `"Qual a raiz quadrada de 144?"`).
     - Perguntas de conhecimento geral (ex.: `"Quem foi Albert Einstein?"`).

4. **Versionamento**
   - `.gitignore` configurado (incluindo `.env` e arquivos de cache/log).

---

## 💡 Observações Pessoais (Opcional, mas recomendável)

> Antes deste case, eu não tinha trabalhado com Strands Agents nem com Ollama.  
> Durante a implementação, aprendi:
>
> - Como estruturar uma API com FastAPI e Pydantic.
> - Como configurar e consumir um modelo local via Ollama.
> - Como criar um agente com tools usando o Strands Agents SDK.
> - Como trabalhar com variáveis de ambiente usando `python-dotenv`.
>
> Também enfrentei alguns desafios com:
>
> - Diferenças entre versões da biblioteca Strands (métodos e formatos de resposta).
> - Formato da resposta do agente (estrutura com `role`, `content`, `text`).
>
> Para este case, optei por uma lógica de pós-processamento simples em `run_agent`,
> priorizando clareza do código e entendimento da arquitetura completa.

---

## 📚 Referências

- **FastAPI – Documentação Oficial**  
  https://fastapi.tiangolo.com/
- **Strands Agents SDK – Documentação**  
  https://strandsagents.com/latest/documentation/docs/
- **Ollama – Modelos locais**  
  https://ollama.com/
- **python-dotenv – Gerenciamento de Variáveis de Ambiente**  
  https://pypi.org/project/python-dotenv/
