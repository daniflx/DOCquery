from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

# Forçamos o cliente a usar a versão 'v1' explicitamente
client = genai.Client(
    api_key=os.getenv("GOOGLE_API_KEY"),
    http_options={'api_version': 'v1'} # <-- O segredo está aqui!
)

try:
    response = client.models.generate_content(
        model='gemini-2.5-flash-lite', 
        contents="Teste final: você está na v1?"
    )
    print("Sucesso Absoluto:", response.text)
except Exception as e:
    print(f"Erro persistente: {e}")