from ollama import Client
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("OLLAMA_API_KEY")
client = Client(
    host="https://ollama.com",
    headers = {'authorization': f"Bearer {API_KEY}"}

)

def make_request_ollama_reasoning(model_name:str, prompt:str, context:str, n_tokens:int):
    print("Making request")
    result = client.chat(
        model=model_name,
        messages = [
            {
                "role":"user",
                "content": prompt,
            },
            {
                "role":"system",
                "content":context,
            }

        ],
        num_predict=n_tokens,
        stream=False

    )

    return result["message"]["content"]
