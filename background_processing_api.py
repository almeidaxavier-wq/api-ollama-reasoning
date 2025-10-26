# Flask Restful API
from flask.blueprints import Blueprint
from flask import session, jsonify, url_for, redirect

# Essential imports
from api.model.reasoning import Reasoning
from threading import Thread, Lock


bp_processing = Blueprint(name='process', import_name=__name__, static_folder='static', template_folder='templates')
threads = []
lock = Lock()

def handle_threads():
    while True:
        for thread in threads:
            try:
                with lock:
                    thread.start()

            except Exception as err:
                if not thread.is_alive() and thread in threads:
                    print('Already finishied =>', err)
                    thread.join()
                    threads.remove(thread)

@bp_processing.route('/run_model', methods=['GET', 'POST'])
def run_model():
    json_code = session.get('json', None)
    session.pop('json', None)

    if json_code:
        query = json_code.get('query')
        context = json_code.get('context')
        api_key = json_code.get('api_key')
        max_depth = json_code.get('max_depth')
        n_tokens = json_code.get('n_tokens')
        log_dir = json_code.get('log_dir', 'log_dir_default')

        model_name = json_code.get('model_name', 'deepseek-v3.1:671b-cloud')
        t = Thread(target=generate ,args=(api_key, log_dir, query, context, n_tokens, model_name, max_depth), daemon=True)
        threads.append(t)

        with lock:
            t.start()

        return redirect(url_for('home'))

    return jsonify({"message": "Send"}), 200

def generate(api_key:str, log_dir:str, query:str, context:str, n_tokens:int, model_name:str, max_depth:int):
    thinker = Reasoning(
        api_key=api_key,
        max_width=5,
        max_depth=max_depth,
        model_name=model_name if model_name else "deepseek-v3.1:671b-cloud",
        n_tokens_default=n_tokens

    )
    # Retorna o resultado da cadeia de raciocínio para que possamos repassar à rota Flask
    #print(query, context, log_dir)
    return thinker.reasoning_step(query=query, context=context, log_dir=log_dir)
