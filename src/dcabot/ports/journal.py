"""Application-facing journal boundary; adapters own storage details."""

from typing import Protocol, Callable
from dcabot.domain.config import Config
from dcabot.domain.engine import State


class Journal(Protocol):
    config: Config

    def transact(self, batch_id: str, request: dict, builder: Callable) -> bool: ...
    def load(self) -> State: ...
    def audit(self) -> dict: ...
