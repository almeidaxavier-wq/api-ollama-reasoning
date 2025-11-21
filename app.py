from flask import Flask, session, render_template, redirect, url_for, request, flash
from flask import stream_with_context
from processing import bp_processing_api
from functools import wraps

from api.model.reasoning import Reasoning
from forms.user import SubmitQueryForm, LoginUser, CreateUser
from forms.search import Search
from markupsafe import Markup
from markdown import markdown
from database.db import db, upload_file, Upload, User
from dotenv import load_dotenv
import threading
import requests
import os

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config['MONGODB_HOST'] = os.getenv("MONGODB_URI")
app.register_blueprint(bp_processing_api)

db.init_app(app)
thinker = Reasoning("", 0, 0)


def check_if_logged_in(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def read_markdown_to_html(user, log_dir:str):
    objs = Upload.objects(filename__contains=log_dir, creator=user)
    markdown_content = ""
    for obj in objs:
        markdown_content += '\n\n' + obj.file.read().decode('utf-8')

    html_code = markdown(markdown_content)
    #print(html_code)
    return Markup(html_code)

@app.route("/", methods=["GET", "POST"])
@check_if_logged_in
def home():
    if not session['logged_in']:
        return redirect(url_for('login'))
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

@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginUser()
    if form.validate_on_submit():
        username_or_email = form.username_or_email.data
        password = form.password.data

        users = User.objects(__raw__={'$or':[{'username':username_or_email},{'email':username_or_email}]})
        if users.first() is None:
            flash("No users matching the description", 'error')

        else:
            usr = users.first()
            if usr.check_password(password):
                flash('Sucessfully logged in')
                session['logged_in'] = True
                return redirect(url_for('home'))

            else:
                flash('Incorrect Password', 'error')

    return render_template('user_forms.html', login=True, form=form)

@app.route("/register", methods=["GET", "POST"])
def register():
    form = CreateUser()       
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data

        existing = User.objects(__raw__={'$or':[{'username':username},{'email':email}]})
        if existing.first() is not None:
            flash("Username or email already registered", 'error')

        else:
            session['logged_in'] = True
            usr = User(id=User.objects.count()+1, username=username, email=email)
            usr.generate_password_hash(password)
            usr.save()

            return redirect(url_for('home'))
    return render_template('user_forms.html', login=False, form=form)

    

@app.route("/<username>/<log_dir>")
@check_if_logged_in
def read(username:str, log_dir:str):
    generator = requests.get(url_for('process', query=username))
    user = User.objects(username=username).first()
    
    obj_reponse = Upload.objects(filename__contains=os.path.join(log_dir, 'response.md'), creator=user).first()
    content = obj_reponse.file.read().decode('utf-8')
    content += '\n\n' + generator.text

    obj_context = Upload.objects(filename__contains=os.path.join(log_dir, 'context.md'), creator=user).first()
    context_content = obj_context.file.read().decode('utf-8')
    context_content += '\n\n' + thinker.context

    obj_reponse.file.put(content.encode('utf-8'), content_type="text/markdown")
    #print(html_code)
    
    return render_template('response.html', aditional_code=generator)


@app.route("/submit_question", methods=["GET", "POST"])
@check_if_logged_in
def submit_question():
    form = SubmitQueryForm()
    if form.validate_on_submit() and request.method == 'POST':
        # Form validation and processing

        if session.get(form.query.data, None) is None:
            session[form.query.data] = {
                'context': form.context.data,
                'api_key': form.api_key.data,
                'log_dir_temp' : form.log_dir.data or 'default_log',
                'n_tokens' : form.n_tokens.data if form.n_tokens.data is not None else 100000,  # Default value
                'model_name' : form.model_name.data if form.model_name.data else "deepseek-v3.1:671b-cloud",
                'max_depth' : form.max_depth.data,
                "current_depth": -1
            }

        session[form.query.data]['current_depth'] += 1
        return redirect(url_for('read', username=form.query.data, log_dir=session[form.query.data]['log_dir_temp']))
    return render_template('form.html', form=form)
    

if __name__ == '__main__':
    threads = []
    app.run(debug=True)
