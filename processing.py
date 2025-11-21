from flask import Blueprint, redirect, url_for, session, stream_with_context, request, Response
from api.model.reasoning import Reasoning

bp_processing_api = Blueprint("bp_processing_api", __name__)
thinker = Reasoning("", 0, 0)

@bp_processing_api.route('/process')
def process():
    query = request.args.get('query')
    max_width = request.args.get('max_width')
    model = request.args.get('model')

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
        context=session.get(query, {}).get("context"),
        init=session.get(query, {}).get("current_depth") == 0
    )

    # update session after streaming (best-effort)
    session[query]['context'] = session.get(query, {}).get('context', '') + thinker.context
    session[query]['current_depth'] = session.get(query, {}).get('current_depth', 0) + 1

    return Response(stream_with_context(result), content_type='text/plain')
