from abc import ABC, abstractmethod

class DetectorBaseClass(ABC):

    @abstractmethod
    def detect(self, local_file):
        pass