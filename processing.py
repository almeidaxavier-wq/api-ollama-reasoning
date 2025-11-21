from flask import Blueprint, redirect, url_for, session, stream_with_context, request, Response
from api.model.reasoning import Reasoning
from database.db import Upload
import os

bp_processing_api = Blueprint("bp_processing_api", __name__)
thinker = Reasoning("", 0, 0)

@bp_processing_api.route('/process?query=<query>&log_dir=<log_dir>&model=<model>&max_width=<max_width>')
def process(query, log_dir, model, max_width):
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

    thinker.max_depth = int(session.get(query, {}).get('max_depth', 10))
    thinker.context = session.get(query, {}).get('context', '')

    result = thinker.reasoning_step(
        query=query,
        context=obj_context.file.read().decode('utf-8'),
        init=session.get(query, {}).get("current_depth") == 0
    )

    # update session after streaming (best-effort)
    session[query]['context'] = session.get(query, {}).get('context', '') + thinker.context
    session[query]['current_depth'] = session.get(query, {}).get('current_depth', 0) + 1

    return Response(stream_with_context(result), content_type='text/plain')
