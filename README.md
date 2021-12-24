# flask-bind

## Binding contracts for Flask's routing system

Heavily influenced by [FastAPI](https://fastapi.tiangolo.com/), `flask-bind` provides a nearly
drop-in replacement for Flask's `app.route` decorator to fulfill the decorated endpoint's
requirement for annotated arguments that represent [pydantic](https://pydantic-docs.helpmanual.io/)
models.

## Usage

```python
from http import HTTPStatus

from flask import app
from flask_bind.decorators import route

from models import User

app = Flask(__name__)

@route(app, "/user", methods=["POST"])
def create_user(user: User):
    # ... add user to the database
    return {"id": user.id}, HTTPStatus.CREATED
```

## Motivation

Take the following Flask endpoint. It is responsible for creating a hypothetical model in response to
`POST` requests to the `/model` route.

```python
@app.route("/model", methods=["POST"])
def create_model():
    data = request.json()
    if not data:
        abort(400, "Missing data")

    name = data.get("name")
    if not name:
        abort(400, "Name is required")

    if not isinstance(name, str):
        abort(400, "Invalid name")

    value = data.get("value")
    if not value:
        abort(400, "Value is required")

    if not instance(value, int):
        abort(400, "Invalid value")

    if value < len(name):
        abort(400, f"Value must not be smaller than {len(name)}")

    db_model = DBModel(name=name, value=value)
    db.sesson.add(db_model)
    db.session.commit()

    return {"id": db_model.id}, HTTPStatus.CREATED
```

Looking at the endpoint's implementation, it is not at all obvious what kind of data is expected
from the client. In order to extract that information, one would have no option but to go through
the entire endpoint's implementation and keep track of how it consumes data that comes off of the
global `request` variable.

In this simple example, we can infer that the request must feature two keys, `name` and `value`,
and that the values associated with these keys must be of types `str` and `int`, respectively.
Furthermore, a seemingly arbitrary business rule dictates that the value cannot be smaller than
the length of the provided string. While it isn't too hard to dig out this "contract" from the
code, things can get much more complicated if the endpoint invokes other auxiliary functions or
makes use of other classes that are each at liberty to query the request data for information.

### Exposing the "contract"

Pure functions unambiguously express their "requirements" in terms of their inputs. This follows
very naturally from how functions are invoked by feeding it their inputs. We can borrow from this
concept to determine exactly what an endpoint might expect from the request payload (or what the
server might expect from the client) by declaring an argument that encapsulates those requirements.

```diff
- def create_model():
+ def create_model(model: Model):
```

In this example, the `create_model` endpoint is unequivocally broadcasting to its consumers that
it needs an instance of `Model` to operate. Looking at `Model`, we can easily inspect what it is
composed of and what rules it must observe.

`pydantic` is a particularly well-suited tool for the task of defining such models because it
leverages Python's type hints to clearly expose and reliably validate the data inside an
application.

```python
from pydantic import BaseModel

class Model(BaseModel):
    name: str
    value: int

    @root_validator
    def some_business_rule(cls, values):
        value, name = values["value"], values["name"]
        if value < len(name):
            raise ValueError(f"Value must not be smaller than {len(name)}")
        return values
```

Once this model is defined, we can then _bind_ it to the endpoint through the `@route` decorator.
The decorator will take care of sourcing the required instance of `Model` from the request data and
pass it to the endpoint. The endpoint, in turn, can then focus on its own operation since it knows
that all of its requirements have been met, otherwise it could not even have been invoked in the
first place.

Having these guarantees met, the endpoint's implementation becomes trivial:

```python
from flask_bind import route

@route(app, "/model", methods=["POST"])
def create_model(model: Model):

    db_model = DBModel(name=model.name, value=model.value)
    db.sesson.add(db_model)
    db.session.commit()

    return {"id": db_model.id}, HTTPStatus.CREATED
```

Here's an example of a successful POST request to the endpoint.

```bash
$ http --verbose :5000/model name=Foo value=5
POST /model HTTP/1.1
Accept: application/json, */*
Accept-Encoding: gzip, deflate
Connection: keep-alive
Content-Length: 29
Content-Type: application/json
Host: localhost:5000
User-Agent: HTTPie/1.0.3

{
    "name": "Foo",
    "value": "5"
}

HTTP/1.0 201 CREATED
Content-Length: 17
Content-Type: application/json
Date: Thu, 23 Dec 2021 21:51:35 GMT
Server: Werkzeug/2.0.2 Python/3.8.10

{
    "id": 1001
}
```

Requests to the endpoint that fail to meet the contract exposed by the definition of `Model` will
trigger a `ValidationError` exception, as `pydantic` can't instantiate the model off of the request
data. If the exception goes unhandled, Flask generates a `500` (Internal Server Error) response in
return. A perhaps more appropriate response would be `400` (Bad Request), to inform the client
that the information it provided is breaching the requirements or it's lackluster. We can this
register a custom error handler to respond to `ValidationError` exceptions.

```python
@app.errorhandler(ValidationError)
def handle_valiation_error(err):
    return str(err), HTTPStatus.BAD_REQUEST
```

In the example below, we simulate a request that breaks the endpoint's contract. `Model` requires a
string for its `value` property but the client sends `null` instead. The `route` decorator, unable
to yield a valid instance of `Model` with which to call `get_model`, throws a `ValidationError`,
which in turn produces the `400` response.

```bash
$ echo '{"name": "Foo", "value": null}' | http :5000/model
HTTP/1.0 400 BAD REQUEST
Content-Length: 100
Content-Type: text/html; charset=utf-8
Date: Thu, 23 Dec 2021 22:05:16 GMT
Server: Werkzeug/2.0.2 Python/3.8.10

1 validation error for Model
value
  none is not an allowed value (type=type_error.none.not_allowed)
```
