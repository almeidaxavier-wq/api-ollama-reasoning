from flask import Flask, session, render_template, redirect, url_for, request, flash
from turbo_flask import Turbo
from processing import bp_processing_api, thinker
from thread_manager import ThreadManager
from functools import wraps
import time

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
app.config['SERVER_NAME'] = 'localhost:5000'
app.register_blueprint(bp_processing_api)
turbo = Turbo()

turbo.init_app(app)
db.init_app(app)


manager = ThreadManager()
manager.start()

def read_markdown_to_html(content:str):
    html_code = markdown(content)
    #print(html_code)
    return Markup(html_code)

def check_if_logged_in(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

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
                files.add(obj.creator.username+'/'+filename[0].split("/")[0])

            else:
                files.add(obj.creator.username+'/'+filename[0])


        return render_template('search.html', query=files)
    return render_template('index.html', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginUser()
    if form.validate_on_submit():
        username_or_email = form.username_or_email.data
        password = form.password.data

        session.permanent = True
        session.permanent_session_lifetime = 3600  # 1 hour

        users = User.objects(__raw__={'$or':[{'username':username_or_email},{'email':username_or_email}]})
        if users.first() is None:
            flash("No users matching the description", 'error')

        else:
            usr = users.first()
            if usr.check_password(password):
                flash('Sucessfully logged in')
                session['logged_in'] = True
                session['username'] = usr.username

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

        session.permanent = True
        session.permanent_session_lifetime = 3600  # 1 hour

        existing = User.objects(__raw__={'$or':[{'username':username},{'email':email}]})
        if existing.first() is not None:
            flash("Username or email already registered", 'error')

        else:
            session['logged_in'] = True
            session['username'] = username
            usr = User(id=User.objects.count()+1, username=username, email=email)
            usr.generate_password_hash(password)
            usr.save()

            return redirect(url_for('home'))
    return render_template('user_forms.html', login=False, form=form)


@app.route("/<username>/<log_dir>")
@check_if_logged_in
def view_logs(username:str, log_dir:str):
    user = User.objects(username=username).first()
    if user is None:
        flash("User not found", 'error')
        return redirect(url_for('home'))

    objs = Upload.objects(filename__contains=os.path.join(log_dir, 'response.md'), creator=user).order_by('depth')
    response = Upload.objects(filename__contains=os.path.join(log_dir, 'response.md'), creator=user).first()
    article = Upload.objects(filename__contains=os.path.join(log_dir, 'article.md'), creator=user).first()
    if objs.first() is None:
        flash("No logs found for this user/log_dir", 'error')
        return redirect(url_for('home'))
    
    return render_template('response.html', response=response.file.read(), article=article.file.read(), read_markdown_to_html=read_markdown_to_html)

@app.route("/<username>/<log_dir>/write_logs")
@check_if_logged_in
def write(username:str, log_dir:str):
    return render_template('response.html')

@app.route("/<username>/<log_dir>/write_article")
@check_if_logged_in
def write_article(username:str, log_dir:str):
    query=request.args.get('query')
    model=request.args.get('model')
    iterations = request.args.get('iterations')
    api_key = request.args.get('api_key')

    process_url = url_for('bp_processing_api.write_article', query=query, log_dir=log_dir, model=model, iterations=iterations, api_key=api_key, _external=True)
    t = threading.Thread(target=store_article, args=(process_url, username, iterations))
    # append thread in a thread-safe way so ThreadManager can pick it up
    with manager.lock:
        manager.threads.append(t)
    
    print("queued thread", t)
    return render_template('article.html')



@app.route("/submit_question", methods=["GET", "POST"])
@check_if_logged_in
def submit_question():
    form = SubmitQueryForm()
    if form.validate_on_submit() and request.method == 'POST':
        # Form validation and processing
        print(User.objects(username=session.get('username')).first())
        upload_file(
            user=User.objects(username=session.get('username')).first(),
            log_dir=form.log_dir.data or 'default_log',
            filename='context.md',
            raw_file=f"Initial context: {form.context.data}".encode('utf-8'),
            depth=0
        )

        upload_file(
            user=User.objects(username=session.get('username')).first(),
            log_dir=form.log_dir.data or 'default_log',
            filename='response.md',
            raw_file="".encode('utf-8'),
            depth=0
        )

        upload_file(
            user=User.objects(username=session.get('username')).first(),
            log_dir=form.log_dir.data or 'default_log',
            filename='article.md',
            raw_file="".encode('utf-8'),
            depth=0
        )

        return redirect(url_for('write', query=form.query.data, prompt=None, username=session.get('username'), log_dir=form.log_dir.data or 'default_log', model=form.model_name.data or "deepseek-v3.1:671b-cloud", max_width=form.max_width.data, max_depth=form.max_depth.data, n_tokens=form.n_tokens.data if form.n_tokens.data is not None else 100000, api_key=form.api_key.data))
    return render_template('form.html', form=form)
    

if __name__ == '__main__':
    # Enable threading so worker threads can make HTTP requests back to this server
    # (use a production WSGI server for real deployments)
    app.run(debug=True, threaded=True)
