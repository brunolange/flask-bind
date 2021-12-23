from functools import reduce

__author__ = "Bruno Lange"
__email__ = "blangeram@gmail.com"
__license__ = "MIT"


def extend(*dicts):
    def update(acc, curr):
        acc.update(curr)
        return acc

    return reduce(update, dicts, {})
