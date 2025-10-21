from flask import Flask, render_template, redirect, url_for, request
from forms.user import SubmitQueryForm
from markupsafe import Markup
from markdown import markdown
from api.model.reasoning import Reasoning
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
requests = {} # Just for storing session data, not definitive (would use a database instead)


def read_markdown_to_html(log_dir:str):
    d_path = os.path.join(os.getcwd(), log_dir)
    print(d_path, os.path.exists(d_path))
    if os.path.exists(d_path):
        fp = os.path.join(d_path, "output.md")
        markdown_content = ""
        with open(fp, 'r') as f:
            markdown_content = f.read()

        for file in os.listdir(os.path.join(d_path, "steps")):
            step_path = os.path.join(d_path, "steps", file)
            with open(step_path, 'r') as step_file:
                step_content = step_file.read()
                markdown_content += f"\n\n## Step {file}\n\n"
                markdown_content += step_content

        html_code = markdown(markdown_content)
        return Markup(html_code)

    else: return False

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/<log_dir>")
def read(log_dir:str):
    result = read_markdown_to_html(log_dir)
    if result:
        return render_template('response.html', aditional_code=result)

    return "Log directory not found.", 404

@app.route("/submit_question", methods=["GET", "POST"])
def submit_question():
    form = SubmitQueryForm()
    if form.validate_on_submit():
        query = form.query.data
        context = form.context.data
        log_dir = form.log_dir.data or 'default_log'
        n_tokens = form.n_tokens.data if form.n_tokens.data is not None else 100000 # Default value
        model_name = form.model_name.data if form.model_name.data else "deepseek-v3.1:671b-cloud"

        # Armazena a requisição e chama a geração imediatamente (síncrona)
        requests[log_dir] = {
            'query': query,
            'context': context,
            'n_tokens': n_tokens,
            'model_name': model_name
        }
        output = generate(log_dir, query, context, n_tokens=n_tokens, model_name=model_name)
        return redirect(url_for('read', log_dir=log_dir))
    return render_template('form.html', form=form)

def generate(log_dir:str, query:str, context:str, n_tokens:int, model_name:str):
    thinker = Reasoning(
        max_width=5,
        max_depth=20,
        model_name=model_name if model_name else "deepseek-v3.1:671b-cloud",
        n_tokens_default=n_tokens

    )
    # Retorna o resultado da cadeia de raciocínio para que possamos repassar à rota Flask
    print(query, context, log_dir)
    return thinker.reasoning_step(query=query, context=context, log_dir=log_dir)
    

if __name__ == '__main__':
    app.run(debug=True)
