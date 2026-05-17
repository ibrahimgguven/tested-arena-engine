from .models import OturumIstatistik

class ScoringEngine:

    BASE_PUAN             = 100
    MAX_STREAK_MULTIPLIER = 2.0
    MAX_SURE_BONUSU       = 50

    @staticmethod
    def zorluk_katsayisi(zorluk_band: int) -> float:
        return 1.0 + (zorluk_band - 1) * 0.15

    @staticmethod
    def streak_carpani(streak: int) -> float:
        return min(1.0 + streak * 0.1, ScoringEngine.MAX_STREAK_MULTIPLIER)

    @staticmethod
    def sure_bonusu(gecen_sure: float, sure_saniye: int) -> int:
        if sure_saniye <= 0:
            return 0
        kalan = max(0.0, sure_saniye - gecen_sure)
        return int((kalan / sure_saniye) * ScoringEngine.MAX_SURE_BONUSU)

    @staticmethod
    def soru_puani_hesapla(zorluk_band: int, streak: int, gecen_sure: float, sure_saniye: int) -> int:
        taban = (
            ScoringEngine.BASE_PUAN
            * ScoringEngine.zorluk_katsayisi(zorluk_band)
            * ScoringEngine.streak_carpani(streak)
        )
        return int(taban) + ScoringEngine.sure_bonusu(gecen_sure, sure_saniye)

    @staticmethod
    def oturum_bonusu_hesapla(can: int, istatistik: OturumIstatistik) -> int:
        bonus = 0
        if can == 3:
            bonus += 500
        elif can == 2:
            bonus += 200
        toplam_soru = istatistik.dogru_sayisi + istatistik.yanlis_sayisi
        if toplam_soru > 0:
            ort_sure = istatistik.toplam_sure / toplam_soru
            if ort_sure < 10:
                bonus += 150
        return bonus