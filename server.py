from __future__ import annotations

from functools import wraps

import numpy as np
from flask import Flask, request, jsonify, render_template
from flask_restful import Api
from flask_cors import CORS
from pelutils import log, DataStorage
from dataclasses import dataclass
from pprint import pformat


app = Flask(__name__)
Api(app)
CORS(app)

app.config["UPLOAD_FOLDER"] = "static"

scores = np.zeros((6, 3))  # [post, group]
submitted = np.zeros((6, 3))

@dataclass
class GroupStatus:
    current_post: int
    show_hint: bool

post_codes = [483, 548, 194, 420, 849, 392]

def code_to_group(code: int) -> int:
    return [391, 498, 193].index(code)

groups = [
    GroupStatus(0, True),
    GroupStatus(2, True),
    GroupStatus(4, True),
]

def json_endpoint(fun):
    """
    This decorator wraps all request method. It has two purposes:
        - Ensure same return type. Whatever a function returns, it is wrapped in a json of shape
            { "data": whatever, "code": 0 }, where 0 is the status code of a successful request
        - Handle errors. If an error is thrown by the method, it handles the error and wraps it in a json:
            { "data": None, "code": 1 }, where 1 is the status code of an unsuccessful request
            In the future, specific error codes > 1 can be added
    """
    @wraps(fun)
    def fun_wrapper(*args, **kwargs):
        log(f"Call at function {fun.__name__}")
        return_value = fun(*args, **kwargs)
        log(f"Returning {return_value}")
        return jsonify(return_value)

    return fun_wrapper

@app.get("/")
def index():
    return render_template("index.html", kort="static/kort.png")

@app.get("/log-in")
@json_endpoint
def log_in():
    group_no = code_to_group(int(request.args.get("group")))
    return groups[group_no]

@app.get("/scores")
@json_endpoint
def get_scores():
    return scores.tolist()

@app.get("/submit")
@json_endpoint
def submit():
    group_no = code_to_group(int(request.args.get("group")))
    score = float(request.args.get("score"))
    group = groups[group_no]
    if submitted[group.current_post, group_no]:
        return

    submitted[group.current_post, group_no] = True
    scores[group.current_post, group_no] = score

    group.current_post = (group.current_post + 1) % 6
    group.show_hint = True

    return group

@app.get("/at-post")
@json_endpoint
def at_post():
    group_no = code_to_group(int(request.args.get("group")))
    post_code = int(request.args.get("post-code"))
    group = groups[group_no]
    if post_code != post_codes[group.current_post]:
        return

    group.show_hint = False

    return group

if __name__ == "__main__":
    log.configure("server.log")
    app.run(host="0.0.0.0", port=6969, debug=False, processes=1, threaded=False)

