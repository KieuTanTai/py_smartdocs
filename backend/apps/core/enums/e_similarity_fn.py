from enum import Enum


class ESimilarityFn(str, Enum):
    COSINE = "cosine"
    EUCLIDEAN = "euclidean"
