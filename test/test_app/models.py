from pydantic import BaseModel

__author__ = "Bruno Lange"
__email__ = "blangeram@gmail.com"
__license__ = "MIT"


class Model(BaseModel):
    name: str
