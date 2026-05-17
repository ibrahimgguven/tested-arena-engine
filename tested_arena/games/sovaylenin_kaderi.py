import math
from typing import Dict, Any
from .base import BaseGame
from ..models import CANAVAR_KATALOGU, Canavar

def _canavar_dict(c: Canavar) -> Dict[str, Any]:
    return {
        "canavar_id": c.canavar_id,
        "ad":         c.ad,
        "hp":         c.hp,
        "direnc":     c.direnc,
    }

class SovayleninsKaderiGame(BaseGame):

    def get_initial_state(self) -> Dict[str, Any]:
        ilk = CANAVAR_KATALOGU[0]
        return {
            "canavar_siralamasi":       [c.canavar_id for c in CANAVAR_KATALOGU],
            "mevcut_canavar":           _canavar_dict(ilk),
            "canavar_mevcut_hp":        ilk.hp,
            "oldurülen_canavar_sayisi": 0,
        }

    @staticmethod
    def hasar_hesapla(direnc: float) -> int:
        return max(1, math.floor(1.0 / direnc))

    def process_correct(self, state: Dict[str, Any]) -> Dict[str, Any]:
        yeni = {
            "canavar_siralamasi":       list(state["canavar_siralamasi"]),
            "mevcut_canavar":           dict(state["mevcut_canavar"]),
            "canavar_mevcut_hp":        state["canavar_mevcut_hp"],
            "oldurülen_canavar_sayisi": state["oldurülen_canavar_sayisi"],
        }
        hasar = self.hasar_hesapla(yeni["mevcut_canavar"]["direnc"])
        yeni["canavar_mevcut_hp"] -= hasar
        if yeni["canavar_mevcut_hp"] <= 0:
            yeni = self._sonraki_canavara_gec(yeni)
        return yeni

    def process_incorrect(self, state: Dict[str, Any]) -> Dict[str, Any]:
        return dict(state)

    def check_win(self, state: Dict[str, Any]) -> bool:
        return state["oldurülen_canavar_sayisi"] >= len(state["canavar_siralamasi"])

    @staticmethod
    def _sonraki_canavara_gec(state: Dict[str, Any]) -> Dict[str, Any]:
        state["oldurülen_canavar_sayisi"] += 1
        idx = state["oldurülen_canavar_sayisi"]
        if idx < len(CANAVAR_KATALOGU):
            sonraki = CANAVAR_KATALOGU[idx]
            state["mevcut_canavar"]    = _canavar_dict(sonraki)
            state["canavar_mevcut_hp"] = sonraki.hp
        else:
            state["canavar_mevcut_hp"] = 0
        return state