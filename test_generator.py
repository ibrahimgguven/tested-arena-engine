"""
test_generator.py
QuestionGenerator testleri.

API anahtarı olmadan çalışan testler (validasyon, dönüşüm):
    python test_generator.py

Gerçek Gemini çağrısı (API anahtarı gerekir):
    GEMINI_API_KEY=AIza... python test_generator.py --gercek
"""

import sys
import json
import os
from dotenv import load_dotenv

load_dotenv()  # .env dosyasındaki GEMINI_API_KEY'i ortam değişkenine yükler

# ─── Test 1: Import ve paket yapısı ──────────────────────────────────────────

print("=" * 60)
print("TEST 1: Import")
print("=" * 60)
try:
    from tested_arena import QuestionGenerator, QuestionEngine, GameType
    from tested_arena.models import SoruTipi, Soru
    from tested_arena.prompt_builder import (
        bloom_belirle, kullanici_promptu, sistem_promptu
    )
    print("OK — Tüm modüller import edildi.")
except ImportError as e:
    print(f"HATA: {e}")
    sys.exit(1)


# ─── Test 2: Bloom eşlemesi ────────────────────────────────────────────────

print("\n" + "=" * 60)
print("TEST 2: Bloom ↔ Zorluk Band Eşlemesi")
print("=" * 60)
from tested_arena.models import BloomDuzeyi

beklenen = {
    1: BloomDuzeyi.HATIRLAMA,
    2: BloomDuzeyi.HATIRLAMA,
    3: BloomDuzeyi.ANLAMA,
    4: BloomDuzeyi.ANLAMA,
    5: BloomDuzeyi.UYGULAMA,
    6: BloomDuzeyi.UYGULAMA,
    7: BloomDuzeyi.ANALIZ,
    8: BloomDuzeyi.ANALIZ,
    9: BloomDuzeyi.ANALIZ,
    10: BloomDuzeyi.ANALIZ,
}
for band, beklenen_bloom in beklenen.items():
    gelen = bloom_belirle(band)
    durum = "OK" if gelen == beklenen_bloom else "HATA"
    print(f"  Band {band:2d} → {gelen.value:12s}  [{durum}]")


# ─── Test 3: Band → b dönüşümü ────────────────────────────────────────────

print("\n" + "=" * 60)
print("TEST 3: Band → IRT b Parametresi")
print("=" * 60)
from tested_arena.question_generator import QuestionGenerator as QG

for band in [1, 3, 5, 7, 10]:
    b = QG._band_to_b(band)
    print(f"  Band {band:2d} → b = {b:+.2f}")


# ─── Test 4: Süre hesaplama ────────────────────────────────────────────────

print("\n" + "=" * 60)
print("TEST 4: Süre Hesaplama")
print("=" * 60)
tipler = [
    SoruTipi.COKTAN_SECMELI,
    SoruTipi.DOGRU_YANLIS,
    SoruTipi.ESLESTIRME,
    SoruTipi.BOSLUK_DOLDURMA,
]
for tip in tipler:
    for band in [1, 5, 10]:
        sure = QG._sure_belirle(band, tip)
        print(f"  {tip.value:20s} band {band:2d} → {sure}sn")


# ─── Test 5: Doğrulama (mock veri) ────────────────────────────────────────

print("\n" + "=" * 60)
print("TEST 5: Doğrulama Mantığı (mock soru verisi)")
print("=" * 60)

mock_coktan = {
    "soru_metni": "1/2 + 1/4 = ?",
    "secenekler": [
        {"id": "A", "metin": "1/6"},
        {"id": "B", "metin": "2/6"},
        {"id": "C", "metin": "3/4"},
        {"id": "D", "metin": "1/3"},
    ],
    "dogru_cevap": "C",
    "aciklama": "Ortak payda 4: 2/4 + 1/4 = 3/4",
}

mock_dt = {
    "soru_metni": "Bir üçgenin iç açıları toplamı 180 derecedir.",
    "secenekler": [{"id": "D", "metin": "Doğru"}, {"id": "Y", "metin": "Yanlış"}],
    "dogru_cevap": "D",
    "aciklama": "Evet, her üçgende iç açılar toplamı 180°'dir.",
}

mock_bosluk = {
    "soru_metni": "Bir üçgenin iç açıları toplamı ___ derecedir.",
    "secenekler": [],
    "dogru_cevap": "180",
    "aciklama": "Her üçgende iç açılar toplamı 180°'dir.",
}

mock_eslestirme = {
    "soru_metni": "Eşleştiriniz.",
    "secenekler": [],
    "sol_liste": [
        {"id": "s1", "metin": "Kare"}, {"id": "s2", "metin": "Üçgen"},
        {"id": "s3", "metin": "Daire"}, {"id": "s4", "metin": "Dikdörtgen"},
    ],
    "sag_liste": [
        {"id": "r1", "metin": "3 kenar"}, {"id": "r2", "metin": "4 eşit kenar"},
        {"id": "r3", "metin": "Pi sayısı"}, {"id": "r4", "metin": "2 çift eşit kenar"},
    ],
    "dogru_cevap": {"s1": "r2", "s2": "r1", "s3": "r3", "s4": "r4"},
    "aciklama": "Geometrik şekillerin özellikleri.",
}

testler = [
    (mock_coktan,   SoruTipi.COKTAN_SECMELI,  "Çoktan seçmeli"),
    (mock_dt,       SoruTipi.DOGRU_YANLIS,     "Doğru/Yanlış"),
    (mock_bosluk,   SoruTipi.BOSLUK_DOLDURMA, "Boşluk doldurma"),
    (mock_eslestirme, SoruTipi.ESLESTIRME,     "Eşleştirme"),
]

for veri, tip, ad in testler:
    try:
        QG._dogrula(veri, tip)
        print(f"  OK — {ad} doğrulaması geçti.")
    except AssertionError as e:
        print(f"  HATA — {ad}: {e}")


# ─── Test 6: JSON Ayıklama ─────────────────────────────────────────────────

print("\n" + "=" * 60)
print("TEST 6: JSON Ayıklama (markdown temizleme)")
print("=" * 60)

ornekler = [
    ('```json\n[{"a": 1}]\n```',   "Markdown bloklu"),
    ('[{"a": 1}]',                  "Temiz JSON"),
    ('Yanıt:\n[{"a": 1}]\nTeşekkürler', "Çevreli metin"),
]

for metin, ad in ornekler:
    try:
        sonuc = QG._json_ayikla(metin)
        print(f"  OK — {ad}: {sonuc}")
    except Exception as e:
        print(f"  HATA — {ad}: {e}")


# ─── Test 7: Prompt üretimi ────────────────────────────────────────────────

print("\n" + "=" * 60)
print("TEST 7: Prompt Üretimi")
print("=" * 60)

prompt = kullanici_promptu(
    ders="Matematik", sinif=6, unite="Kesirler",
    kazanim_kodu="M.6.1.3.2",
    kazanim_metni="Farklı paydaları eşitleyerek kesir toplar.",
    zorluk_band=5,
    soru_tipi=SoruTipi.COKTAN_SECMELI,
    adet=3,
)
print(f"  Prompt uzunluğu: {len(prompt)} karakter")
assert "M.6.1.3.2" in prompt, "Kazanım kodu prompt'ta yok"
assert "Kesirler" in prompt, "Ünite prompt'ta yok"
assert "5/10" in prompt, "Zorluk bandı prompt'ta yok"
print("  OK — Prompt alanları doğru.")


# ─── Test 8: Gerçek API (opsiyonel) ───────────────────────────────────────

if "--gercek" in sys.argv:
    print("\n" + "=" * 60)
    print("TEST 8: Gerçek Gemini API Çağrısı")
    print("=" * 60)

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("  ATLANDI — GEMINI_API_KEY ortam değişkeni tanımlı değil.")
    else:
        gen = QuestionGenerator(api_key=api_key)
        sorular = gen.uret(
            ders="Matematik",
            sinif=6,
            unite="Kesirler",
            kazanim_kodu="M.6.1.3.2",
            kazanim_metni="Farklı paydaları eşitleyerek kesir toplar.",
            zorluk_band=4,
            soru_tipi=SoruTipi.COKTAN_SECMELI,
            adet=3,
        )
        print(f"  Üretilen soru sayısı: {len(sorular)}")
        for s in sorular:
            print(f"\n  [{s.id}]")
            print(f"  Soru: {s.soru_metni}")
            print(f"  Seçenekler:")
            for sec in s.secenekler:
                isaret = "✓" if sec["id"] == s.dogru_cevap else " "
                print(f"    [{isaret}] {sec['id']}) {sec['metin']}")
            print(f"  Açıklama: {s.aciklama}")
            print(f"  b={s.zorluk_b}, band={s.zorluk_band}, süre={s.sure_saniye}sn")


# ─── Özet ─────────────────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("Tüm testler tamamlandı.")
print("Gerçek API testi için: GEMINI_API_KEY=AIza... python test_generator.py --gercek")
print("=" * 60)
