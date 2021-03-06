from http import HTTPStatus
from typing import Any, Optional

from flask import Flask, make_response
from flask_bind.decorators import route
from pydantic import BaseModel, SecretStr, ValidationError

from .models import Model, Node, NodePatch
from .utils import extend

__author__ = "Bruno Lange"
__email__ = "blangeram@gmail.com"
__license__ = "MIT"


app = Flask(__name__)


@app.errorhandler(ValidationError)
def handle_validation_error(err: ValidationError):
    return "Invalid request", HTTPStatus.BAD_REQUEST


def echo(value: Any):
    return make_response(str(value))


@route(app, "/")
def index():
    return "hello world"


@route(app, "/echo/path/<path:value>")
def echo_path(value):
    return value


@route(app, "/echo/int/<int:value>")
def echo_int(value):
    return echo(value)


@route(app, "/echo/uuid/<uuid:value>")
def echo_uuid(value):
    return echo(value)


@route(app, "/model", methods=["POST"])
def post_model(model: Model):
    return {"id": 1, "name": model.name}, HTTPStatus.CREATED


@route(app, "/r/model", methods=["POST"])
def post_model_reflect(model: Model):
    return model, HTTPStatus.CREATED


@route(app, "/s/model/<int:status>", methods=["POST"])
def post_model_code(status, model: Model):
    return model, status


@route(app, "/opt/model", methods=["POST"])
def post_optional_model(model: Optional[Model] = None):
    return model or {"name": "Out Of Thin Air!"}


@route(app, "/opt/model/<param>", methods=["POST"])
def post_optional_with_url_param(param, model: Optional[Model] = None):
    return extend(
        {"name": "Out Of Thin Air!", "url_param": param}, model.dict() if model else {}
    )


@route(app, "/node/<int:node_id>", methods=["PUT"])
def put_node(node_id, node: Node):
    return "", HTTPStatus.NO_CONTENT


@route(app, "/node/<int:node_id>", methods=["PATCH"])
def patch_node(node_id, node: NodePatch):
    return "", HTTPStatus.NO_CONTENT


class Form(BaseModel):
    username: str
    password: SecretStr


@route(app, "/form", methods=["POST"])
def post_form(form: Form):
    return {"username": form.username}
