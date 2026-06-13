
from abc import ABC, abstractmethod


class INeo4jNodeLabels(ABC):
    @abstractmethod
    def get_node_labels(self, file_caller: str = "") -> list[str]:
        pass

    @abstractmethod
    def get_relationship_type(self, file_caller: str = "") -> list[str]:
        pass