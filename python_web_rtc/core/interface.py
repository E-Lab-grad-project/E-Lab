from abc import ABC, abstractmethod
import numpy as np


class VideoSource(ABC):
    @abstractmethod
    def read(self) -> np.ndarray:
        pass

class frameProcessor(ABC):
    @abstractmethod
    def process(self, frame: np.ndarray) -> np.ndarray:
        pass