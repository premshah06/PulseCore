from abc import ABC, abstractmethod

from producer.models import StreamEvent


class BaseGenerator(ABC):
    """All domain generators implement this interface."""

    @property
    @abstractmethod
    def domain(self) -> str: ...

    @abstractmethod
    def generate(self) -> StreamEvent: ...
