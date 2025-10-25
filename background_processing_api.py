# Flask Restful API
from flask.blueprints import Blueprint
from flask import jsonify, request, url_for, redirect
import asyncio

# Essential imports
from api.model.reasoning import Reasoning
import threading

loop = None

try:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

except Exception as err:
    print(err)
    loop = asyncio.get_event_loop()

bp_processing = Blueprint(name='process', import_name=__name__, static_folder='static', template_folder='templates')
@bp_processing.route('/run_model', methods=['GET', 'POST'])
def run_model():
    json_code = request.get_json()
    print(json_code, request)

    if request.is_json:
        query = json_code.get('query')
        context = json_code.get('context')
        max_depth = json_code.get('max_depth')
        n_tokens = json_code.get('n_tokens')
        log_dir = json_code.get('log_dir', 'log_dir_default')

        model_name = json_code.get('model_name', 'deepseek-v3.1:671b-cloud')
        return redirect(url_for(
            'process.threads',
            query=query,
            context=context,
            n_tokens=n_tokens,
            model_name=model_name,
            max_depth=max_depth,
            log_dir=log_dir
        ))

    return jsonify({"message": "Send"}), 200

@bp_processing.route('/run?query=<query>&context=<context>&n_tokens=<int:n_tokens>&model_name=<model_name>&max_depth=<int:max_depth>&log_dir=<log_dir>', methods=['GET', 'POST'])
def threads(query, context, n_tokens, model_name, max_depth, log_dir):
    asyncio.run(run_threads(query, context, n_tokens, model_name, max_depth, log_dir))
    return redirect(url_for('home'))

async def run_threads(query, context, n_tokens, model_name, max_depth, log_dir):
    await asyncio.to_thread(generate, log_dir, query, context, n_tokens, model_name, max_depth)

def generate(log_dir:str, query:str, context:str, n_tokens:int, model_name:str, max_depth:int):
    thinker = Reasoning(
        max_width=5,
        max_depth=max_depth,
        model_name=model_name if model_name else "deepseek-v3.1:671b-cloud",
        n_tokens_default=n_tokens

    )
    # Retorna o resultado da cadeia de raciocínio para que possamos repassar à rota Flask
    #print(query, context, log_dir)
    return thinker.reasoning_step(query=query, context=context, log_dir=log_dir)
