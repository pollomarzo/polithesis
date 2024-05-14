from abc import ABC, abstractmethod


class SpikingModel(ABC):
    @abstractmethod
    def describe_model(**kwargs):
        pass
