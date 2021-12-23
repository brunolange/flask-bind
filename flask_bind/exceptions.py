__author__ = "Bruno Lange"
__email__ = "blangeram@gmail.com"
__license__ = "MIT"


class NoRequestDataError(Exception):
    """Thrown when flask_bind is expected to build a model from a request that has no data in it"""
