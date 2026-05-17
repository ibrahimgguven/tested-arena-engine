from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple
from ..models import SessionStatus

class BaseGame(ABC):

    @abstractmethod
    def get_initial_state(self) -> Dict[str, Any]:
        ...

    @abstractmethod
    def process_correct(self, state: Dict[str, Any]) -> Dict[str, Any]:
        ...

    @abstractmethod
    def process_incorrect(self, state: Dict[str, Any]) -> Dict[str, Any]:
        ...

    @abstractmethod
    def check_win(self, state: Dict[str, Any]) -> bool:
        ...

    def check_loss(self, can: int) -> bool:
        return can <= 0

    def get_status(self, state: Dict[str, Any], can: int) -> Tuple[bool, SessionStatus]:
        if self.check_win(state):
            return True, SessionStatus.KAZANDI
        if self.check_loss(can):
            return True, SessionStatus.KAYBETTI
        return False, SessionStatus.AKTIF