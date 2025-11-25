from flask import Blueprint, redirect, url_for, session, stream_with_context, request, Response
from api.model.reasoning import Reasoning
from database.db import Upload
import os
import time

bp_processing_api = Blueprint("bp_processing_api", __name__)
thinker = Reasoning("", 0, 0)

@bp_processing_api.route('/process')
def process():
    query = request.args.get('query')
    log_dir = request.args.get('log_dir')
    model = request.args.get('model')
    max_width = request.args.get('max_width')
    max_depth = request.args.get('max_depth')
    n_tokens = request.args.get('n_tokens')
    api_key = request.args.get('api_key')
    prompt = request.args.get('prompt')

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
    thinker.n_tokens_default = int(n_tokens) if n_tokens is not None else thinker.n_tokens_default

    result = thinker.reasoning_step(
        username=session.get('username'),
        log_dir=log_dir,
        query=query,
        init=False,
        prompt=None if prompt == 'None' else prompt
    )

    # set headers to reduce buffering by proxies and clients
    headers = {
        'Content-Type': 'text/plain',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'X-Accel-Buffering': 'no'
    }
    return Response(stream_with_context(result), headers=headers), 200

@bp_processing_api.route('/write_article')
def write_article():
    query = request.args.get('query')
    log_dir = request.args.get('log_dir')
    model = request.args.get('model')
    iterations = request.args.get('iterations')
    api_key = request.args.get('api_key')

    if not query:
        return redirect(url_for('home'))

    thinker.api_key = api_key
    thinker.model = model
    thinker.n_tokens_default = 65000

    result = thinker.write_article(
        username=session.get('username'),
        log_dir=log_dir,
        iterations=int(iterations)
    )

    headers = {
        'Content-Type': 'text/plain',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'X-Accel-Buffering': 'no'
    }
    return Response(stream_with_context(result), headers=headers), 200
