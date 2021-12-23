import pytest

from .test_app.app import app as test_app

__author__ = "Bruno Lange"
__email__ = "blangeram@gmail.com"
__license__ = "MIT"


@pytest.fixture
def client():
    with test_app.test_client() as client:
        with test_app.app_context():
            yield client
