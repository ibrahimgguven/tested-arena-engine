from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any

from .models import (
    GameSession, GameType, SessionStatus,
    Soru, CevapSonucu, OturumIstatistik,
)
from .difficulty import DifficultyEngine
from .scoring import ScoringEngine
from .games import (
    BaseGame, BilVeFethetGame, SovayleninsKaderiGame, BombaGame, StandartGame,
)

_GAME_HANDLERS: Dict[GameType, BaseGame] = {
    GameType.BIL_VE_FETHET:     BilVeFethetGame(),
    GameType.SOVAYLENIN_KADERI: SovayleninsKaderiGame(),
    GameType.BOMBA:             BombaGame(),
    GameType.STANDART:          StandartGame(),
}

class QuestionEngine:

    def __init__(self):
        self._difficulty = DifficultyEngine()
        self._scoring    = ScoringEngine()

    def oturum_baslat(self, player_id, game_type, sinif, ders, unite, kazanim_kodu, soru_havuzu):
        handler   = self._get_handler(game_type)
        ilk_state = handler.get_initial_state()
        session   = GameSession.olustur(
            player_id=player_id, game_type=game_type, sinif=sinif,
            ders=ders, unite=unite, kazanim_kodu=kazanim_kodu, oyun_state=ilk_state,
        )
        ilk_soru = self._difficulty.sonraki_soruyu_sec(
            theta=session.theta, sorular=soru_havuzu,
            sorulmus_ids=session.sorulmus_soru_idler, kazanim_kodu=kazanim_kodu,
        )
        return session, ilk_soru

    def cevap_isle(self, session, soru, verilen_cevap, gecen_sure, sure_doldu, soru_havuzu):
        if session.durum != SessionStatus.AKTIF:
            raise ValueError(f"Oturum aktif değil: {session.durum}")

        dogru_mu = not sure_doldu and verilen_cevap.strip() == soru.dogru_cevap.strip()

        yeni_theta = self._difficulty.theta_guncelle(
            theta=session.theta, b=soru.zorluk_b, dogru=dogru_mu, sure_doldu=sure_doldu,
        )

        handler = self._get_handler(session.game_type)
        yeni_state = handler.process_correct(session.oyun_state) if dogru_mu else handler.process_incorrect(session.oyun_state)

        yeni_can    = session.can - (0 if dogru_mu else 1)
        yeni_streak = (session.streak + 1) if dogru_mu else 0

        kazanilan_puan = 0
        if dogru_mu:
            kazanilan_puan = self._scoring.soru_puani_hesapla(
                zorluk_band=soru.zorluk_band, streak=session.streak,
                gecen_sure=gecen_sure, sure_saniye=soru.sure_saniye,
            )

        istat = OturumIstatistik(
            dogru_sayisi=session.istatistik.dogru_sayisi + (1 if dogru_mu else 0),
            yanlis_sayisi=session.istatistik.yanlis_sayisi + (0 if dogru_mu else 1),
            toplam_sure=session.istatistik.toplam_sure + gecen_sure,
            en_yuksek_streak=max(session.istatistik.en_yuksek_streak, yeni_streak),
        )

        bitti, yeni_durum = handler.get_status(yeni_state, yeni_can)

        session.theta               = yeni_theta
        session.can                 = yeni_can
        session.puan               += kazanilan_puan
        session.streak              = yeni_streak
        session.istatistik          = istat
        session.oyun_state          = yeni_state
        session.sorulmus_soru_idler = session.sorulmus_soru_idler + [soru.id]
        session.durum               = yeni_durum

        oturum_ozeti = None
        if bitti:
            session.bitis_zamani = datetime.utcnow()
            oturum_ozeti = self._oturum_ozeti_olustur(session)

        sonuc = CevapSonucu(
            dogru_mu=dogru_mu, dogru_cevap=soru.dogru_cevap, aciklama=soru.aciklama,
            kazanilan_puan=kazanilan_puan, streak=yeni_streak, yeni_theta=yeni_theta,
            can=yeni_can, oyun_state=yeni_state, oturum_durumu=yeni_durum,
            sonuc="kazandi" if yeni_durum == SessionStatus.KAZANDI
                  else ("kaybetti" if yeni_durum == SessionStatus.KAYBETTI else None),
            oturum_ozeti=oturum_ozeti,
        )
        return sonuc, session

    def sonraki_soru(self, session, soru_havuzu):
        if session.durum != SessionStatus.AKTIF:
            return None
        return self._difficulty.sonraki_soruyu_sec(
            theta=session.theta, sorular=soru_havuzu,
            sorulmus_ids=session.sorulmus_soru_idler, kazanim_kodu=session.kazanim_kodu,
        )

    def oturum_iptal(self, session):
        session.durum        = SessionStatus.IPTAL
        session.bitis_zamani = datetime.utcnow()
        return session

    @staticmethod
    def _get_handler(game_type):
        handler = _GAME_HANDLERS.get(game_type)
        if handler is None:
            raise ValueError(f"Bilinmeyen oyun tipi: {game_type}")
        return handler

    def _oturum_ozeti_olustur(self, session):
        bonus = self._scoring.oturum_bonusu_hesapla(session.can, session.istatistik)
        session.puan += bonus
        toplam_soru = session.istatistik.dogru_sayisi + session.istatistik.yanlis_sayisi
        ort_sure = session.istatistik.toplam_sure / toplam_soru if toplam_soru > 0 else 0.0
        return {
            "dogru_sayisi":     session.istatistik.dogru_sayisi,
            "yanlis_sayisi":    session.istatistik.yanlis_sayisi,
            "ortalama_sure":    round(ort_sure, 1),
            "en_yuksek_streak": session.istatistik.en_yuksek_streak,
            "son_theta":        round(session.theta, 3),
            "toplam_puan":      session.puan,
            "oturum_bonusu":    bonus,
        }