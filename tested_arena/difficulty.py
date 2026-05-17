import math
import random
from typing import List, Optional
from .models import Soru

ALPHA         = 0.3
THETA_MIN     = -3.0
THETA_MAX     = 3.0
TARGET_OFFSET = 0.1
WINDOW_START  = 0.3
WINDOW_STEP   = 0.3
WINDOW_MAX    = 1.5

class DifficultyEngine:

    @staticmethod
    def dogru_cevap_olasiligi(theta: float, b: float) -> float:
        return 1.0 / (1.0 + math.exp(-(theta - b)))

    @staticmethod
    def theta_guncelle(theta: float, b: float, dogru: bool, sure_doldu: bool = False) -> float:
        p = DifficultyEngine.dogru_cevap_olasiligi(theta, b)
        if dogru:
            delta = ALPHA * (1.0 - p)
        elif sure_doldu:
            delta = -(ALPHA / 2.0) * p
        else:
            delta = -ALPHA * p
        return max(THETA_MIN, min(THETA_MAX, theta + delta))

    @staticmethod
    def sonraki_soruyu_sec(theta: float, sorular: List[Soru], sorulmus_ids: List[str], kazanim_kodu: str) -> Optional[Soru]:
        hedef_b = max(THETA_MIN, min(THETA_MAX, theta + TARGET_OFFSET))
        uygun = [
            s for s in sorular
            if s.aktif
            and s.kazanim_kodu == kazanim_kodu
            and s.id not in sorulmus_ids
        ]
        if not uygun:
            return None
        pencere = WINDOW_START
        while pencere <= WINDOW_MAX + 0.001:
            adaylar = [s for s in uygun if abs(s.zorluk_b - hedef_b) < pencere]
            if adaylar:
                return random.choice(adaylar)
            pencere += WINDOW_STEP
        return random.choice(uygun)

    @staticmethod
    def b_den_band(b: float) -> int:
        normalized = (b + 3.0) / 6.0
        band = int(normalized * 9.0) + 1
        return max(1, min(10, band))