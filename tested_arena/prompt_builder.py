from .models import SoruTipi, BloomDuzeyi

def bloom_belirle(zorluk_band):
    if zorluk_band <= 2:   return BloomDuzeyi.HATIRLAMA
    elif zorluk_band <= 4: return BloomDuzeyi.ANLAMA
    elif zorluk_band <= 6: return BloomDuzeyi.UYGULAMA
    else:                  return BloomDuzeyi.ANALIZ

_TIP_TALIMAT = {
    SoruTipi.COKTAN_SECMELI: '''Çoktan seçmeli soru üret. 4 seçenek (A,B,C,D), tek doğru cevap.
JSON formatı:
{"soru_metni":"...","secenekler":[{"id":"A","metin":"..."},{"id":"B","metin":"..."},{"id":"C","metin":"..."},{"id":"D","metin":"..."}],"dogru_cevap":"B","aciklama":"..."}''',

    SoruTipi.DOGRU_YANLIS: '''Doğru/Yanlış sorusu üret.
JSON formatı:
{"soru_metni":"İfade: ...","secenekler":[{"id":"D","metin":"Doğru"},{"id":"Y","metin":"Yanlış"}],"dogru_cevap":"D","aciklama":"..."}''',

    SoruTipi.BOSLUK_DOLDURMA: '''Boşluk doldurma sorusu üret. Boşluk ___ ile gösterilmeli.
JSON formatı:
{"soru_metni":"Bir üçgenin iç açıları toplamı ___ derecedir.","secenekler":[],"dogru_cevap":"180","aciklama":"..."}''',

    SoruTipi.ESLESTIRME: '''Eşleştirme sorusu üret. Sol ve sağ listede 4er madde.
JSON formatı:
{"soru_metni":"Eşleştiriniz.","secenekler":[],"sol_liste":[{"id":"s1","metin":"..."},{"id":"s2","metin":"..."},{"id":"s3","metin":"..."},{"id":"s4","metin":"..."}],"sag_liste":[{"id":"r1","metin":"..."},{"id":"r2","metin":"..."},{"id":"r3","metin":"..."},{"id":"r4","metin":"..."}],"dogru_cevap":{"s1":"r2","s2":"r1","s3":"r4","s4":"r3"},"aciklama":"..."}''',
}

_ZORLUK_TANIM = {
    1:"Çok temel, ezber.", 2:"Temel bilgi.", 3:"Kavramı anlama.", 4:"İlişki kurma.",
    5:"Formül uygulama.", 6:"Çok adımlı uygulama.", 7:"Analiz.",
    8:"Alışılmadık bağlam.", 9:"Olimpiyat düzeyi.", 10:"Üst düzey analiz.",
}

def sistem_promptu():
    return """Sen MEB müfredatına uygun ortaokul (5-8. sınıf) soru üreticisisin.
Kurallar:
1. Sorular Türkçe ve sade olmalı.
2. MEB kazanımına birebir uygun olmalı.
3. Yanıt YALNIZCA geçerli JSON içermeli, başka hiçbir şey olmamalı.
4. Sayısal sorularda hata olmamalı."""

def kullanici_promptu(ders, sinif, unite, kazanim_kodu, kazanim_metni, zorluk_band, soru_tipi, adet):
    bloom = bloom_belirle(zorluk_band)
    return f"""Şu bilgilere göre {adet} soru üret:
Ders: {ders} | Sınıf: {sinif} | Ünite: {unite}
Kazanım: [{kazanim_kodu}] {kazanim_metni}
Zorluk: {zorluk_band}/10 — {_ZORLUK_TANIM.get(zorluk_band,'')}
Bloom: {bloom.value}

{_TIP_TALIMAT[soru_tipi]}

{adet} elemanlı JSON dizisi döndür: [ {{...}}, {{...}} ]
YALNIZCA JSON yaz, başka hiçbir şey yazma."""
