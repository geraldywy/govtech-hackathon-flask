from abc import ABC, abstractmethod

class ModelBaseClass(ABC):

    @abstractmethod
    def generate(self, local_file):
        pass