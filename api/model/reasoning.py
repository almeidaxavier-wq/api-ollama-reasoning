from api.model.api_main import make_request_ollama_reasoning
import os

generate_prompt = lambda width: f"""
THINK LOUDLY!
1. Break the problem into {width} step alternatives to adress it
2. Choose one alternative
3. DO NOT USE CONJECTURES. Only use well known theorems, lemmas and mathematical concepts. 

Do not write an answer yet, only propose the alternatives.
Display math in KATEX form
"""

continue_prompt = lambda width: f"""
Now, extensively create an mathematical approximation using this alternative,
proposing {width} new ones from the result of the approach.

Remember: don't use any conjecture, only theorems, lemmas and other mathematical concepts well known.
If any solution encountered, return SOLVED, else *only return PROGRESS*
*Display math in KATEX form*
"""

class Reasoning:
    def __init__(self, api_key:str, max_width:int, max_depth:int, model_name:str="deepseek-v3.1:671b-cloud", n_tokens_default:int=100000):
        self.max_width = max_width,
        self.max_depth = max_depth
        self.model = model_name 
        self.n_tokens_default = n_tokens_default
        self.api_key = api_key
        self.context = ""

    def reasoning_step(self, query:str, context:str, init=True):
        #print(depth)
        prompt = ""
        prompt += f"PROBLEM: {query}\n\n"
        prompt += generate_prompt(self.max_width) if init else continue_prompt(self.max_width)

        #print('PROMPT', prompt, context, self.model, self.n_tokens_default, log_dir)
        result = make_request_ollama_reasoning(api_key=self.api_key, model_name=self.model, prompt=prompt, context=context, n_tokens=self.n_tokens_default)
        self.context += "\n\n" + prompt + "\n\n" + result

        def iterate(r):
            for chunk in r:
                if 'message' in chunk:
                    yield chunk['message']['content']

        return iterate(result)
