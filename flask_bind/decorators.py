import inspect
from functools import wraps
from http import HTTPStatus
from typing import Dict, Union

from flask import Blueprint, Flask, request
from flask.wrappers import Response
from pydantic import BaseModel, ValidationError

from .utils import MaybeModel, get_maybe_model


__author__ = "Bruno Lange"
__email__ = "blangeram@gmail.com"
__license__ = "MIT"


def route(app: Union[Blueprint, Flask], path: str, **kwargs):
    """A near drop-in replacement for Flask's standard router.

    Beyond the tokenization for url parameters, `route` also fulfills the decorated endpoint's
    requirement for annotated arguments that represent pydantic models.

    The models are constructed from the JSON data in the request's body. A `ValidationError` is
    thrown if the model can't be constructed.
    """

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
                        raise

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
