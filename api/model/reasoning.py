from api.model.api_main import make_request_ollama_reasoning
import os

generate_prompt = lambda width: f"""
1. Break the problem into {width} step alternatives to adress it
2. Choose one alternative
3. DO NOT USE CONJECTURES. Only use well known theorems, lemmas and mathematical concepts. 

Do not write an answer yet, only propose the alternatives.
"""

continue_prompt = lambda width: f"""
Now, extensively create an mathematical aproximation using this alternative,
proposing {width} new ones from the result of the approach.

Also, don't use any conjecture, only theorems, lemmas and other mathematical concepts well known.
"""

class Reasoning:
    def __init__(self, max_width:int, max_depth:int, model_name:str="deepseek-v3.1:671b-cloud", n_tokens_default:int=100000):
        self.max_width = max_width,
        self.max_depth = max_depth
        self.model = model_name 
        self.n_tokens_default = n_tokens_default

    def reasoning_step(self, query:str, context:str, seq=None, init=True, depth=0, log_dir="log_dir_default"):
        if depth >= self.max_depth:
            return seq
        
        seq = [] if seq is None else seq
        
        prompt = ""
        prompt += f"PROBLEM: {query}\n\n"
        prompt += generate_prompt(self.max_width) if init else continue_prompt(self.max_width)

        print('PROMPT', prompt, context, self.model, self.n_tokens_default, log_dir)
        result = make_request_ollama_reasoning(model_name=self.model, prompt=prompt, context=context, n_tokens=self.n_tokens_default)
        context += "\n\n" + prompt

        if "SOLVED" in result:
            log_path = os.path.join('tmp', log_dir, 'steps', 'output.md')
            os.makedirs(os.path.join('tmp', log_dir, 'steps')) if not os.path.exists(log_path) else None

            with open(log_path, 'a', encoding='utf-8') as output_file:
                for s in seq:
                    output_file.write(s+'\n\n')

            return seq

        log_path_steps = os.path.join('tmp', log_dir, "steps")
        os.makedirs(log_path_steps) if not os.path.exists(log_path_steps) else None

        with open(os.path.join(log_path_steps, 'log'+str(depth+1)+'.md'), 'w', encoding='utf-8') as file:
            file.write(result)

        return self.reasoning_step(query=query, context=context+"\n\n"+result, seq=seq+[result], init=False, depth=depth+1, log_dir=log_dir)
        