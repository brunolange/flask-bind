from typing import Optional

from pydantic import BaseModel, root_validator

__author__ = "Bruno Lange"
__email__ = "blangeram@gmail.com"
__license__ = "MIT"


class Model(BaseModel):
    name: str


class Node(BaseModel):
    label: str
    value: int

class NodePatch(BaseModel):
    label: Optional[str]
    value: Optional[int]

    @root_validator
    def at_least_one(cls, values):
        if not values["value"] and not values["label"]:
            raise ValueError("must provide either label or value (or both)")
        return values
