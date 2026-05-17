from typing import Dict, Any
from .base import BaseGame

BOMBA_SURESI_SANIYE = 20
HEDEF_DOGRU_SAYISI  = 10

class BombaGame(BaseGame):

    def get_initial_state(self) -> Dict[str, Any]:
        return {
            "bomba_suresi_saniye": BOMBA_SURESI_SANIYE,
            "hedef_dogru_sayisi":  HEDEF_DOGRU_SAYISI,
            "tamamlanan_dogru":    0,
        }

    def process_correct(self, state: Dict[str, Any]) -> Dict[str, Any]:
        yeni = dict(state)
        yeni["tamamlanan_dogru"] = state["tamamlanan_dogru"] + 1
        return yeni

    def process_incorrect(self, state: Dict[str, Any]) -> Dict[str, Any]:
        return dict(state)

    def check_win(self, state: Dict[str, Any]) -> bool:
        return state["tamamlanan_dogru"] >= state["hedef_dogru_sayisi"]