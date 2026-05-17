import json, os, re, time, uuid, logging
from typing import List, Optional, Dict, Any
from google import genai
from google.genai import types as genai_types
from .models import Soru, SoruTipi
from .prompt_builder import sistem_promptu, kullanici_promptu, bloom_belirle

logger = logging.getLogger(__name__)
DEFAULT_MODEL = "gemini-2.0-flash"
MAX_RETRY     = 3
RETRY_DELAY   = 2.0

class QuestionGenerator:

    def __init__(self, api_key=None, model=DEFAULT_MODEL):
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

    def uret(self, ders, sinif, unite, kazanim_kodu, kazanim_metni,
             zorluk_band, soru_tipi=SoruTipi.COKTAN_SECMELI, adet=5):
        prompt   = kullanici_promptu(ders=ders, sinif=sinif, unite=unite,
                       kazanim_kodu=kazanim_kodu, kazanim_metni=kazanim_metni,
                       zorluk_band=zorluk_band, soru_tipi=soru_tipi, adet=adet)
        ham_json = self._gemini_cagir(prompt)
        if ham_json is None:
            return []
        return self._json_to_sorular(ham_json, ders, sinif, unite,
                                     kazanim_kodu, kazanim_metni, zorluk_band, soru_tipi)

    def toplu_uret(self, kazanim_listesi, her_kazanim_icin=5, bekleme_suresi=1.5):
        tum_sorular = []
        for i, k in enumerate(kazanim_listesi):
            try:
                sorular = self.uret(
                    ders=k["ders"], sinif=k["sinif"], unite=k["unite"],
                    kazanim_kodu=k["kazanim_kodu"], kazanim_metni=k["kazanim_metni"],
                    zorluk_band=k.get("zorluk_band", 5),
                    soru_tipi=k.get("soru_tipi", SoruTipi.COKTAN_SECMELI),
                    adet=k.get("adet", her_kazanim_icin),
                )
                tum_sorular.extend(sorular)
            except Exception as e:
                logger.error(f"HATA [{k.get('kazanim_kodu')}]: {e}")
            if i < len(kazanim_listesi) - 1:
                time.sleep(bekleme_suresi)
        return tum_sorular

    def _gemini_cagir(self, prompt):
        for deneme in range(1, MAX_RETRY + 1):
            try:
                yanit = self._client.models.generate_content(
                    model=self._model_adi, contents=prompt, config=self._config)
                return self._json_ayikla(yanit.text.strip())
            except json.JSONDecodeError as e:
                logger.warning(f"JSON hatası (deneme {deneme}): {e}")
                if deneme < MAX_RETRY: time.sleep(RETRY_DELAY)
            except Exception as e:
                logger.error(f"API hatası: {e}")
                if deneme < MAX_RETRY: time.sleep(RETRY_DELAY)
                else: raise
        return None

    @staticmethod
    def _json_ayikla(metin):
        temiz   = re.sub(r"```(?:json)?", "", metin).strip().rstrip("`").strip()
        eslesen = re.search(r"\[.*\]", temiz, re.DOTALL)
        if eslesen: return json.loads(eslesen.group())
        return json.loads(temiz)

    def _json_to_sorular(self, ham_json, ders, sinif, unite,
                         kazanim_kodu, kazanim_metni, zorluk_band, soru_tipi):
        sorular  = []
        zorluk_b = round(((zorluk_band - 1) / 9.0) * 6.0 - 3.0, 2)
        bloom    = bloom_belirle(zorluk_band)
        taban    = {SoruTipi.COKTAN_SECMELI:20, SoruTipi.DOGRU_YANLIS:15,
                    SoruTipi.ESLESTIRME:40, SoruTipi.BOSLUK_DOLDURMA:25}.get(soru_tipi, 20)
        sure     = taban + ((zorluk_band - 1) // 3) * 5

        for idx, veri in enumerate(ham_json):
            try:
                assert veri.get("soru_metni") and veri.get("dogru_cevap") and veri.get("aciklama")
                sorular.append(Soru(
                    id=f"{kazanim_kodu.lower().replace('.','_')}_{uuid.uuid4().hex[:8]}",
                    ders=ders, sinif=sinif, unite=unite,
                    kazanim_kodu=kazanim_kodu, kazanim_metni=kazanim_metni,
                    soru_tipi=soru_tipi, zorluk_b=zorluk_b, zorluk_band=zorluk_band,
                    sure_saniye=sure, soru_metni=veri["soru_metni"].strip(),
                    secenekler=veri.get("secenekler", []),
                    dogru_cevap=str(veri["dogru_cevap"]).strip(),
                    aciklama=veri.get("aciklama", "").strip(),
                    bloom_duzeyi=bloom, aktif=True,
                ))
            except Exception as e:
                logger.warning(f"Soru {idx+1} atlandı: {e}")
        return sorular