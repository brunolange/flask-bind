# flask-bind

## Binding contracts for Flask's routing system

Heavily influenced by [FastAPI](https://fastapi.tiangolo.com/), `flask-bind` provides a nearly
drop-in replacement for Flask's `app.route` decorator to fulfill the decorated endpoint's
requirement for annotated arguments that represent [pydantic](https://pydantic-docs.helpmanual.io/)
models.

## Usage

```python
from flask_bind.decorators import route
from pydantic import BaseModel, EmailField, SecretStr
...

class Account(BaseModel):
    email: EmailField
    password: SecretStr
    age: Optional[int]

@route(app, "/account", methods=["POST"])
def create_account(account: Account):
    # ... add new account to the database
    return {"id": account_id}, HTTPStatus.CREATED
```

## Motivation

Suppose our application supports the creation of new users by accepting `POST` requests to the
`"/user"` route. Your task is to understand exactly how the endpoint operates - what it requires
from the client in order to perform its objective. So you pull up the source and glance at its
definition, which loooks something like this:

```python
@app.route("/user", methods=["POST"])
def create_user():
    data = request.json()
    if not data:
        abort(400, "Missing data")

    name = data.get("name", "").strip()
    if not name:
        abort(400, "Name is required")

    if not insinstance(name, str):
        abort(400, "Excepted 'name' to be a string")

    about = data.get("about", "").strip()
    if not insinstance(name, about):
        abort(400, "Excepted 'about' to be a string")

    if len(about) > 1000:
        abort(400, "About must not exceed 1000 characters")

    if not "email" in data:
        abort(400, "Missing email")

    email = data["email"]
    if not is_valid_email(email):
        abort(400, "invalid email")

    user = User(name=name, about=about, email=email)

    db.session.add(user)
    db.session.commit()

    return {"id": user.id}, HTTPStatus.CREATED
```

Though it looks reasonable and somewhat structured, it is not at all obvious what the "rules of
engagement" are. Let's go through the implementation to see if we can figure it out.

First, the endpoint expects JSON data in the request body, which is captured in the `data`
variable. If the request does not have any data, we abort with a `HTTPStatus.BAD_REQUEST` code.

```python
data = request.json()
if not data:
    abort(400, "Missing data")
```

We can then infer that `data` must be a dictionary since the `get` method is invoked to extract
a `name` key, which must represent a non-empty string. Again, if those conditions aren't met, we
report `BAD_REQUEST` back to the client.

```python
name = data.get("name", "").strip()
if not name:
    abort(400, "Name is required")
```

The `about` key is optional but, if a value is sent, it must be a string with no more than 1000
characters.

```python
about = data.get("about", "")
if not insinstance(about, str):
    abort(400, "Excepted 'about' to be a string")

if len(about) > 1000:
    abort(400, "About must not exceed 1000 characters")
```

Finally, the endpoint also expects to receive a valid email.

While it wasn't too hard to dig out this "contract" in this simple example, things can get much
more complicated if the endpoint invokes other auxiliary functions or makes use of classes that
are each at liberty to query the request body for information.

You could also argue that the validation carried out by the endpoint imbues some duplication as
it imperatively checks for valid strings for multiple keys.

If our goal is to expose the endpoint's interface, the implicit protocol that the clients must
follow in order to properly issue their requests, then this imperative, "free-for-all" approach to
accessing and validating the request falls short as you're left with no choice but the follow the
entire endpoint's implementation whilst keeping track of where and how the request information is
consumed.

### Taming the complexity

In functional programming, functions express their "requirements" very naturally in terms of
their inputs. After all, functions can't be called unless you provide them with all the inputs they
require.

Endpoints could borrow this concept to declare what they nede in order to operate a certain task.
From our example, we determined that `create_model` needs to pull a lot of information from a
dictionary representation of the request body. However, the universe of dictionaries is far too
permissive for it to provide useful structures. We need something more restrictive, more
structured, to more rigorously convey what an endpoint requires.

Python 3.5 introduced _type hints_. Even though the Python interpreter itself is not concerned
with types, this language feature enables 3rd part tools to provide static type analysis.

In particular, `pydantic` uses type annotations to enforce them at runtime, providing detailed
error mesages when validation fails. It is therefore a particularly well-suited tool for the task
of defining the requirements for our endpoints, and it is indeed what the FastAPI framework uses.

In our example, we can define the following model to describe the request payload to the
`create_user` endpoint.

```python
from pydantic import BaseModel, EmailField, constr

class NewUser(BaseModel):
    name: constr(strip_whitespace=True, min_length=1)
    about: Optional[constr(strip_whitespace=True, min_length=1)]
    email: EmailField
```

Following the defintion, we can `bind` this model to the endpoint, so that it can unequivocally
broadcast to its consumers that it needs an instance of `NewUser` to operate.

```diff
- def create_user():
+ def create_user(new_user: NewUser):
```

Finally, we decorate the enpoint with the `route` decorator provided by `flask-bind` so that it
can assemble an instance of `User` from the request body and pass it along to the endpoint whenever
it is invoked.

```diff
- @app.route("/user", methods=["POST"])
+ @route(app, "/user", methods=["POST"])
```

The endpoint, in turn, can then focus on its own operation since it knows that all of its
requirements have been met. Otherwise, it could not even have been invoked in the first place.
The implementation then becomes trivial:

```python
@route(app, "/user", methods=["POST"])
def create_model(new_user: NewUser):

    user = User(name=new_user.name, about=new_user.about, email=new_user.email)

    db.session.add(user)
    db.session.commit()

    return {"id": user.id}, HTTPStatus.CREATED
```

More importantly, if you need to know under what conditions the endpoint is capable of operating,
you need to look no further than the specification of the `NewUser` class. The type annotations
will tell you precisely what keys the endpoint expects, as well as any other rules that apply.
