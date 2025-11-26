from dotenv import load_dotenv
import os
import math
import json  
from strands import Agent, tool
from strands.models.ollama import OllamaModel  # <- IMPORT CERTO PRO OLLAMA

load_dotenv()


LLM_MODEL = os.getenv("LLM_MODEL", "llama3.1")  
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

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


ollama_model = OllamaModel(
    host=OLLAMA_BASE_URL,  
    model_id=LLM_MODEL,    
   
)


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

async def run_agent(message: str) -> str:
    response = await agent.invoke_async(message)

    if isinstance(response, dict):
        content = response.get("content")
        if isinstance(content, list) and content:
            first_item = content[0]
            if isinstance(first_item, dict) and "text" in first_item:
                return str(first_item["text"])

    if isinstance(response, str):
        return response

    if hasattr(response, "content"):
        c = response.content
        if isinstance(c, list) and c:
            first_item = c[0]
            if isinstance(first_item, dict) and "text" in first_item:
                return str(first_item["text"])
        return str(c)

    return str(response)
                

                    

                    
                    
                    

    

   

                    

       

    