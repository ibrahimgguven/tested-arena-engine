"""
tested_arena/question_generator.py
Google Gemini ile MEB müfredatına uygun otomatik soru üretici.

Kullanım:
    from tested_arena import QuestionGenerator
    from tested_arena.models import SoruTipi

    gen = QuestionGenerator()                        # GEMINI_API_KEY env'den
    gen = QuestionGenerator(api_key="AIza...")       # veya doğrudan

    sorular = gen.uret(
        ders="Matematik", sinif=6, unite="Kesirler",
        kazanim_kodu="M.6.1.3.2",
        kazanim_metni="Farklı paydaları eşitleyerek kesir toplar.",
        zorluk_band=5,
        soru_tipi=SoruTipi.COKTAN_SECMELI,
        adet=5,
    )

Ücretsiz Gemini Kotası (2025):
    gemini-2.0-flash : 15 istek/dakika, 1500 istek/gün
"""

import json
import os
import re
import time
import uuid
import logging
from typing import List, Optional, Dict, Any

from dotenv import load_dotenv
from google import genai
from google.genai import types as genai_types

from .models import Soru, SoruTipi, BloomDuzeyi
from .prompt_builder import sistem_promptu, kullanici_promptu, bloom_belirle

load_dotenv()  # .env dosyasındaki GEMINI_API_KEY'i ortam değişkenine yükler

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gemini-2.5-flash"
MAX_RETRY     = 3
RETRY_DELAY   = 2.0


class QuestionGenerator:
    """
    Google Gemini tabanlı MEB uyumlu soru üretici.

    Args:
        api_key : Gemini API anahtarı.
                  Verilmezse GEMINI_API_KEY ortam değişkenine bakılır.
        model   : Kullanılacak model (varsayılan: gemini-2.0-flash)
    """

    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_MODEL):
        anahtar = api_key or os.environ.get("GEMINI_API_KEY")
        if not anahtar:
            raise ValueError(
                "Gemini API anahtarı gerekli.\n"
                "Seçenek 1: QuestionGenerator(api_key='AIza...')\n"
                "Seçenek 2: export GEMINI_API_KEY='AIza...'"
            )
        self._client    = genai.Client(api_key=anahtar)
        self._model_adi = model
        self._config    = genai_types.GenerateContentConfig(
            system_instruction=sistem_promptu(),
            temperature=0.7,
            top_p=0.9,
            max_output_tokens=4096,
        )

    # ── Tekil Üretim ─────────────────────────────────────────────────────────

    def uret(
        self,
        ders: str,
        sinif: int,
        unite: str,
        kazanim_kodu: str,
        kazanim_metni: str,
        zorluk_band: int,
        soru_tipi: SoruTipi = SoruTipi.COKTAN_SECMELI,
        adet: int = 5,
    ) -> List[Soru]:
        """
        Belirtilen kazanım ve zorluk bandına göre sorular üretir.

        Returns:
            List[Soru] — üretilen ve doğrulanan sorular.
        """
        prompt = kullanici_promptu(
            ders=ders, sinif=sinif, unite=unite,
            kazanim_kodu=kazanim_kodu, kazanim_metni=kazanim_metni,
            zorluk_band=zorluk_band, soru_tipi=soru_tipi, adet=adet,
        )

        ham_json = self._gemini_cagir(prompt)
        if ham_json is None:
            logger.error("Gemini'den geçerli yanıt alınamadı.")
            return []

        return self._json_to_sorular(
            ham_json=ham_json,
            ders=ders, sinif=sinif, unite=unite,
            kazanim_kodu=kazanim_kodu, kazanim_metni=kazanim_metni,
            zorluk_band=zorluk_band, soru_tipi=soru_tipi,
        )

    # ── Toplu Üretim ──────────────────────────────────────────────────────────

    def toplu_uret(
        self,
        kazanim_listesi: List[Dict[str, Any]],
        her_kazanim_icin: int = 5,
        bekleme_suresi: float = 1.5,
    ) -> List[Soru]:
        """
        Birden fazla kazanım için toplu soru üretir.

        kazanim_listesi elemanları:
            {
                "ders", "sinif", "unite", "kazanim_kodu", "kazanim_metni",
                "zorluk_band" (opsiyonel, default 5),
                "soru_tipi"   (opsiyonel, default coktan_secmeli),
                "adet"        (opsiyonel, her_kazanim_icin override),
            }
        """
        tum_sorular: List[Soru] = []

        for i, k in enumerate(kazanim_listesi):
            logger.info(
                f"[{i+1}/{len(kazanim_listesi)}] {k.get('kazanim_kodu', '?')} "
                f"— band {k.get('zorluk_band', 5)}"
            )
            try:
                sorular = self.uret(
                    ders=k["ders"], sinif=k["sinif"], unite=k["unite"],
                    kazanim_kodu=k["kazanim_kodu"],
                    kazanim_metni=k["kazanim_metni"],
                    zorluk_band=k.get("zorluk_band", 5),
                    soru_tipi=k.get("soru_tipi", SoruTipi.COKTAN_SECMELI),
                    adet=k.get("adet", her_kazanim_icin),
                )
                tum_sorular.extend(sorular)
                logger.info(f"  → {len(sorular)} soru üretildi.")
            except Exception as e:
                logger.error(f"  → HATA: {e}")

            if i < len(kazanim_listesi) - 1:
                time.sleep(bekleme_suresi)

        return tum_sorular

    # ── Gemini API Çağrısı ────────────────────────────────────────────────────

    def _gemini_cagir(self, prompt: str) -> Optional[List[Dict]]:
        for deneme in range(1, MAX_RETRY + 1):
            try:
                yanit = self._client.models.generate_content(
                    model=self._model_adi,
                    contents=prompt,
                    config=self._config,
                )
                metin = yanit.text.strip()
                return self._json_ayikla(metin)

            except json.JSONDecodeError as e:
                logger.warning(f"JSON parse hatası (deneme {deneme}/{MAX_RETRY}): {e}")
                if deneme < MAX_RETRY:
                    time.sleep(RETRY_DELAY)

            except Exception as e:
                logger.error(f"Gemini API hatası: {e}")
                if deneme < MAX_RETRY:
                    time.sleep(RETRY_DELAY)
                else:
                    raise

        return None

    # ── JSON Ayıklama ─────────────────────────────────────────────────────────

    @staticmethod
    def _json_ayikla(metin: str) -> List[Dict]:
        temiz = re.sub(r"```(?:json)?", "", metin).strip().rstrip("`").strip()
        eslesen = re.search(r"\[.*\]", temiz, re.DOTALL)
        if eslesen:
            return json.loads(eslesen.group())
        return json.loads(temiz)

    # ── JSON → Soru Dönüşümü ──────────────────────────────────────────────────

    def _json_to_sorular(
        self,
        ham_json: List[Dict],
        ders: str, sinif: int, unite: str,
        kazanim_kodu: str, kazanim_metni: str,
        zorluk_band: int, soru_tipi: SoruTipi,
    ) -> List[Soru]:
        sorular = []
        zorluk_b = self._band_to_b(zorluk_band)
        bloom    = bloom_belirle(zorluk_band)

        for idx, veri in enumerate(ham_json):
            try:
                self._dogrula(veri, soru_tipi)
                soru = Soru(
                    id=f"{kazanim_kodu.lower().replace('.', '_')}_{uuid.uuid4().hex[:8]}",
                    ders=ders, sinif=sinif, unite=unite,
                    kazanim_kodu=kazanim_kodu,
                    kazanim_metni=kazanim_metni,
                    soru_tipi=soru_tipi,
                    zorluk_b=zorluk_b,
                    zorluk_band=zorluk_band,
                    sure_saniye=self._sure_belirle(zorluk_band, soru_tipi),
                    soru_metni=veri["soru_metni"].strip(),
                    secenekler=veri.get("secenekler", []),
                    dogru_cevap=str(veri["dogru_cevap"]).strip(),
                    aciklama=veri.get("aciklama", "").strip(),
                    gorsel_url=None,
                    bloom_duzeyi=bloom,
                    aktif=True,
                )
                sorular.append(soru)
            except (KeyError, ValueError, AssertionError) as e:
                logger.warning(f"Soru {idx+1} doğrulamayı geçemedi, atlandı: {e}")

        return sorular

    # ── Doğrulama ─────────────────────────────────────────────────────────────

    @staticmethod
    def _dogrula(veri: Dict, soru_tipi: SoruTipi) -> None:
        assert "soru_metni" in veri and veri["soru_metni"], "soru_metni boş"
        assert "dogru_cevap" in veri, "dogru_cevap eksik"
        assert "aciklama" in veri and veri["aciklama"], "aciklama boş"

        if soru_tipi == SoruTipi.COKTAN_SECMELI:
            assert "secenekler" in veri, "secenekler eksik"
            assert len(veri["secenekler"]) == 4, "4 seçenek olmalı"
            secenek_idler = {s["id"] for s in veri["secenekler"]}
            assert veri["dogru_cevap"] in secenek_idler, \
                f"dogru_cevap ({veri['dogru_cevap']}) seçeneklerde yok"

        elif soru_tipi == SoruTipi.DOGRU_YANLIS:
            assert veri["dogru_cevap"] in ("D", "Y"), \
                "dogru_cevap 'D' veya 'Y' olmalı"

        elif soru_tipi == SoruTipi.ESLESTIRME:
            assert "sol_liste" in veri and len(veri["sol_liste"]) == 4, \
                "sol_liste 4 eleman olmalı"
            assert "sag_liste" in veri and len(veri["sag_liste"]) == 4, \
                "sag_liste 4 eleman olmalı"
            assert isinstance(veri["dogru_cevap"], dict), \
                "dogru_cevap dict olmalı"

        elif soru_tipi == SoruTipi.BOSLUK_DOLDURMA:
            assert "___" in veri["soru_metni"], \
                "soru_metni'nde ___ boşluk işareti yok"

    # ── Yardımcı ─────────────────────────────────────────────────────────────

    @staticmethod
    def _band_to_b(band: int) -> float:
        return round(((band - 1) / 9.0) * 6.0 - 3.0, 2)

    @staticmethod
    def _sure_belirle(zorluk_band: int, soru_tipi: SoruTipi) -> int:
        taban = {
            SoruTipi.COKTAN_SECMELI:  20,
            SoruTipi.DOGRU_YANLIS:    15,
            SoruTipi.ESLESTIRME:      40,
            SoruTipi.BOSLUK_DOLDURMA: 25,
        }.get(soru_tipi, 20)
        return taban + ((zorluk_band - 1) // 3) * 5
