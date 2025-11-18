from flask import Blueprint, redirect, url_for, session, stream_with_context
from api.model.reasoning import Reasoning

bp_processing_api = Blueprint("bp_processing_api", __name__)
thinker = Reasoning("", 0, 0)

@bp_processing_api.route('/process?query=<query>&max_width=<max_width>')
def process(query, max_width):
    thinker.model_name = model
    thinker.max_depth = session[query].get('max_depth', 10)
    thinker.max_width = max_width
    thinker.context = session[query].get('context', '')

    result = thinker.reasoning_step(
        query=query,
        context=session[query].get("context"),
        init=session[query].get("current_depth") == 0
    )

    session[query]['context'] += thinker.context
    session[query]['current_depth'] += 1

    return stream_with_context(result)
