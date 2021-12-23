import inspect
from functools import wraps
from http import HTTPStatus
from typing import Dict, Union

from flask import Blueprint, Flask, request
from flask.wrappers import Response
from pydantic import BaseModel, ValidationError

from .exceptions import NoRequestDataError
from .utils import MaybeModel, get_maybe_model

__author__ = "Bruno Lange"
__email__ = "blangeram@gmail.com"
__license__ = "MIT"

def route(app: Union[Blueprint, Flask], path: str, **kwargs):
    def outer(fn):
        sig = inspect.signature(fn)

        @app.route(path, **kwargs)
        @wraps(fn)
        def inner(*args, **kw):
            data = request.get_json()

            model_map: Dict[str, MaybeModel] = {
                arg: maybe_model
                for arg, maybe_model in [
                    (a, get_maybe_model(parameter))
                    for a, parameter in sig.parameters.items()
                ]
                if maybe_model
            }

            for arg, maybe_model in model_map.items():
                try:
                    kw[arg] = maybe_model.cls.parse_obj(data)
                except ValidationError:
                    if not maybe_model.optional:
                        raise NoRequestDataError(
                            f"Cannot build {maybe_model.cls}. Request has no data."
                        )

            payload = fn(*args, **kw)

            if isinstance(payload, Response):
                return payload

            if isinstance(payload, tuple):
                payload, code = payload
            else:
                code = HTTPStatus.OK

            if isinstance(payload, BaseModel):
                return payload.dict(), code

            return payload, code

        return inner

    return outer
