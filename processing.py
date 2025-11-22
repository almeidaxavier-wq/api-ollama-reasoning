from flask import Blueprint, redirect, url_for, session, stream_with_context, request, Response
from api.model.reasoning import Reasoning
from database.db import Upload
import os

bp_processing_api = Blueprint("bp_processing_api", __name__)
thinker = Reasoning("", 0, 0)

@bp_processing_api.route('/process?query=<query>&log_dir=<log_dir>&model=<model>&max_width=<int:max_width>&max_depth=<int:max_depth>&n_tokens=<int:n_tokens>&prompt=<prompt>&api_key=<api_key>')
def process(query, log_dir, model, max_width, max_depth, n_tokens, prompt, api_key):
    obj_context = Upload.objects(filename__contains=os.path.join(log_dir, 'context.md')).first()

    if not query:
        return redirect(url_for('home'))

    # set model and numeric parameters
    if model:
        thinker.model = model

    try:
        thinker.max_width = int(max_width) if max_width is not None else thinker.max_width
    except Exception:
        thinker.max_width = thinker.max_width
    
    thinker.api_key = api_key
    thinker.max_depth = int(max_depth) if max_depth is not None else thinker.max_depth
    thinker.context = obj_context.file.read().decode('utf-8')
    thinker.n_tokens_default = int(n_tokens) if n_tokens is not None else thinker.n_tokens_default

    result = thinker.reasoning_step(
        query=query,
        context=obj_context.file.read().decode('utf-8'),
        init=obj_context.depth == 0,
        prompt=None if prompt == 'None' else prompt
    )

    obj_context.file.delete()
    obj_context.file.put(thinker.context.encode('utf-8'), content_type="text/markdown")
    obj_context.depth += 1
    obj_context.save()

    return Response(stream_with_context(result), content_type='text/plain'), 200
