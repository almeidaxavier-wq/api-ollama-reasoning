from ollama import Client
from dotenv import load_dotenv

def make_request_ollama_reasoning(api_key:str, model_name:str, prompt:str, context:str, n_tokens:int):
    client = Client(
        host="https://ollama.com",
        headers={'authorization': f"Bearer {api_key}"}

    )

    print("Making request", context, model_name)
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

        ], options={
            "temperature":0.2,
            "num_predict": n_tokens,

        },
        stream=False

    )
    print(result['message'])

    return result["message"]["content"]
