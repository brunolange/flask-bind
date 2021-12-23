import json
from http import HTTPStatus


__author__ = "Bruno Lange"
__email__ = "blangeram@gmail.com"
__license__ = "MIT"


def test_index(client):
    response = client.get("/")
    assert response.data == b"hello world"


def test_regular_route(client):
    for path, value in [
        ("path", "the_answer"),
        ("path", "the/answer/is/42"),
        ("int", "42"),
        ("uuid", "6926a61d-71c4-47a0-a063-9e5104ab409a"),
    ]:
        response = client.get(f"/echo/{path}/{value}")
        assert response.data == value.encode("utf-8")


def test_model_route(client):
    response = client.post("/model", json={"name": "Foo"})
    assert response.status_code == HTTPStatus.CREATED
    data = json.loads(response.data)
    assert data == {"id": 1, "name": "Foo"}


def test_reflective_model_route(client):
    response = client.post("/r/model", json={"name": "Foo"})
    assert response.status_code == HTTPStatus.CREATED
    data = json.loads(response.data)
    assert data == {"name": "Foo"}

    response = client.post("/s/model/200", json={"name": "Bar"})
    assert response.status_code == HTTPStatus.OK
    data = json.loads(response.data)
    assert data == {"name": "Bar"}


def test_optional_model(client):
    response = client.post("/opt/model")
    data = json.loads(response.data)
    assert data == {"name": "Out Of Thin Air!"}

    response = client.post("/opt/model", json={"name": "Foobar"})
    data = json.loads(response.data)
    assert data == {"name": "Foobar"}


def test_optional_model_with_url_param(client):
    response = client.post("/opt/model/the_url_param")
    data = json.loads(response.data)
    assert data == {"name": "Out Of Thin Air!", "url_param": "the_url_param"}

    response = client.post("/opt/model/the_url_param", json={"name": "Foobar"})
    data = json.loads(response.data)
    assert data == {"name": "Foobar", "url_param": "the_url_param"}
