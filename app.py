from flask import Flask, session, render_template, redirect, url_for, request
from forms.user import SubmitQueryForm
from forms.search import Search
from markupsafe import Markup
from markdown import markdown
from database import db, upload_file, Upload
from dotenv import load_dotenv
from background_processing_api import bp_processing, handle_threads
from threading import Thread
import os

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config['MONGODB_HOST'] = os.getenv("MONGODB_URI")
app.register_blueprint(bp_processing)

threads = []
db.init_app(app)

def read_markdown_to_html(log_dir:str):
    objs = Upload.objects(filename__contains=log_dir)
    markdown_content = ""
    for obj in objs:
        markdown_content += '\n\n' + obj.file.read().decode('utf-8')

    html_code = markdown(markdown_content)
    #print(html_code)
    return Markup(html_code)

@app.route("/", methods=["GET", "POST"])
def home():
    form = Search()

    if form.validate_on_submit():
        query = form.query.data
        objs = Upload.objects(filename__contains=query)
        files = set()
        for obj in objs:
            filename = obj.filename.split("\\")

            if len(filename) == 1:
                files.add(filename[0].split("/")[0])

            else:
                files.add(filename[0])


        return render_template('search.html', query=files)
    return render_template('index.html', form=form)

@app.route("/<log_dir>")
def read(log_dir:str):
    result = read_markdown_to_html(log_dir)
    return render_template('response.html', aditional_code=result)

@app.route("/load_log_dir/<log_dir>")
def load(log_dir:str):
    for file in os.listdir(os.path.join('/tmp', log_dir, 'steps')):
        with open(os.path.join('/tmp', log_dir, 'steps', file), 'rb') as f:
            raw = f.read()
            upload_file(temp_log_dir=log_dir, filename=file, raw_file=raw)

    return redirect(url_for('home'))


@app.route("/submit_question", methods=["GET", "POST"])
async def submit_question():
    form = SubmitQueryForm()
    if form.validate_on_submit() and request.method == 'POST':
        # Form validation and processing

        session['json'] = {
            'query': form.query.data,
            'context': form.context.data,
            'api_key': form.api_key.data,
            'log_dir_temp' : form.log_dir.data or 'default_log',
            'n_tokens' : form.n_tokens.data if form.n_tokens.data is not None else 100000,  # Default value
            'model_name' : form.model_name.data if form.model_name.data else "deepseek-v3.1:671b-cloud",
            'max_depth' : form.max_depth.data
        }

        return redirect(url_for('process.run_model'))
    return render_template('form.html', form=form)
    

if __name__ == '__main__':
    t = Thread(target=handle_threads)
    t.start()
    app.run(debug=True)
