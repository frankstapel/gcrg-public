"""Help save and load objects to and from pickle files."""

import pickle
from typing import Union

import pandas as pd


def save_object(obj, file) -> None:
    """Save an object to a pickle file."""
    with open(file, "wb") as f:
        pickle.dump(obj, f)


def load_object(file: str) -> Union[dict, pd.DataFrame]:
    """Load an object from a pickle file."""
    with open(file, "rb") as f:
        return pickle.load(f)
