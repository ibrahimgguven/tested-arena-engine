from typing import Dict, Any
from .base import BaseGame

TOPLAM_BOLGE = 10

class BilVeFethetGame(BaseGame):

    def get_initial_state(self) -> Dict[str, Any]:
        return {
            "toplam_bolge":        TOPLAM_BOLGE,
            "fethedilen_bolgeler": [],
            "siradaki_bolge":      1,
        }

    def process_correct(self, state: Dict[str, Any]) -> Dict[str, Any]:
        yeni = dict(state)
        yeni["fethedilen_bolgeler"] = list(state["fethedilen_bolgeler"])
        bolge = state["siradaki_bolge"]
        if bolge not in yeni["fethedilen_bolgeler"]:
            yeni["fethedilen_bolgeler"].append(bolge)
        yeni["siradaki_bolge"] = bolge + 1
        return yeni

    def process_incorrect(self, state: Dict[str, Any]) -> Dict[str, Any]:
        yeni = dict(state)
        yeni["fethedilen_bolgeler"] = list(state["fethedilen_bolgeler"])
        if yeni["fethedilen_bolgeler"]:
            kaybedilen = yeni["fethedilen_bolgeler"].pop()
            yeni["siradaki_bolge"] = kaybedilen
        return yeni

    def check_win(self, state: Dict[str, Any]) -> bool:
        return len(state["fethedilen_bolgeler"]) >= state["toplam_bolge"]