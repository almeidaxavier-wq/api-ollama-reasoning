from flask import Flask, render_template, redirect, url_for, request
from forms.user import SubmitQueryForm
from markdown import markdown
from api.model.reasoning import Reasoning
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
requests = {} # Just for storing session data, not definitive (would use a database instead)


def read_markdown_to_html(log_dir:str):
    d_path = os.path.join("api", "model", log_dir)
    if os.path.exists(d_path):
        fp = os.path.join(d_path, "output.md")
        markdown_content = ""
        with open(fp, 'r') as f:
            markdown_content = f.read()

        html_code = markdown(markdown_content)
        return html_code

    else: return False

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/<log_dir>")
def read(log_dir:str):
    result = read_markdown_to_html(log_dir)
    if result:
        return render_template('response.html', aditional_code=result)
    
    elif log_dir in requests.keys():
        # Recupera os dados armazenados para este log_dir e executa a geração
        req = requests.get(log_dir)
        if req:
            output = generate(
                log_dir,
                req.get('query'),
                req.get('context'),
                n_tokens=req.get('n_tokens'),
                model_name=req.get('model_name')
            )

            # Se a função retornar uma sequência de passos, converte para HTML e exibe
            if output:
                try:
                    md = "\n\n".join(output) if isinstance(output, (list, tuple)) else str(output)
                    return render_template('response.html', aditional_code=markdown(md))
                except Exception:
                    return str(output)

    return 'Wait while we are processing the data'

@app.route("/submit_question", methods=["GET", "POST"])
def submit_question():
    form = SubmitQueryForm()
    if request.method == 'POST' and form.validate_on_submit():
        query = form.data.query
        context = form.data.context
        log_dir = form.data.log_dir or 'default_log'
        n_tokens = form.data.n_tokens if form.data.n_tokens is not None else 100000 # Default value
        model_name = form.data.model_name if form.data.model_name is not None else "deepseek-v3.1:671b-cloud"

        # Armazena a requisição e chama a geração imediatamente (síncrona)
        requests[log_dir] = {
            'query': query,
            'context': context,
            'n_tokens': n_tokens,
            'model_name': model_name
        }

        output = generate(log_dir, query, context, n_tokens=n_tokens, model_name=model_name)

        if output:
            md = "\n\n".join(output) if isinstance(output, (list, tuple)) else str(output)
            return render_template('response.html', aditional_code=markdown(md))

        return redirect(url_for('read', log_dir=log_dir))

    return render_template('form.html', form=form)

def generate(log_dir:str, query:str, context:str, n_tokens:int, model_name:str):
    thinker = Reasoning(
        max_width=3,
        max_depth=20,
        model_name=model_name,
        n_tokens_default=n_tokens

    )
    # Retorna o resultado da cadeia de raciocínio para que possamos repassar à rota Flask
    return thinker.reasoning_step(query, context, log_dir=log_dir)
    

if __name__ == '__main__':
    app.run(debug=True)
