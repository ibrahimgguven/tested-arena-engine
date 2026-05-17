from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

class GameType(str, Enum):
    BIL_VE_FETHET     = "bil_ve_fethet"
    SOVAYLENIN_KADERI = "sovaylenin_kaderi"
    BOMBA             = "bomba"
    STANDART          = "standart"

class SessionStatus(str, Enum):
    AKTIF    = "aktif"
    KAZANDI  = "kazandi"
    KAYBETTI = "kaybetti"
    IPTAL    = "iptal"

class SoruTipi(str, Enum):
    COKTAN_SECMELI  = "coktan_secmeli"
    DOGRU_YANLIS    = "dogru_yanlis"
    ESLESTIRME      = "eslestirme"
    BOSLUK_DOLDURMA = "bosluk_doldurma"

class BloomDuzeyi(str, Enum):
    HATIRLAMA = "hatirlama"
    ANLAMA    = "anlama"
    UYGULAMA  = "uygulama"
    ANALIZ    = "analiz"

@dataclass
class Soru:
    id:             str
    ders:           str
    sinif:          int
    unite:          str
    kazanim_kodu:   str
    kazanim_metni:  str
    soru_tipi:      SoruTipi
    zorluk_b:       float
    zorluk_band:    int
    sure_saniye:    int
    soru_metni:     str
    secenekler:     List[Dict[str, str]]
    dogru_cevap:    str
    aciklama:       str
    gorsel_url:     Optional[str]  = None
    bloom_duzeyi:   BloomDuzeyi    = BloomDuzeyi.UYGULAMA
    aktif:          bool           = True

@dataclass
class OturumIstatistik:
    dogru_sayisi:     int   = 0
    yanlis_sayisi:    int   = 0
    toplam_sure:      float = 0.0
    en_yuksek_streak: int   = 0

@dataclass
class GameSession:
    session_id:          str
    player_id:           str
    game_type:           GameType
    sinif:               int
    ders:                str
    unite:               str
    kazanim_kodu:        str
    baslangic_zamani:    datetime
    durum:               SessionStatus
    theta:               float
    can:                 int
    puan:                int
    streak:              int
    istatistik:          OturumIstatistik
    sorulmus_soru_idler: List[str]
    oyun_state:          Dict[str, Any]
    bitis_zamani:        Optional[datetime] = None

    @classmethod
    def olustur(cls, player_id, game_type, sinif, ders, unite, kazanim_kodu, oyun_state):
        return cls(
            session_id=str(uuid.uuid4()),
            player_id=player_id,
            game_type=game_type,
            sinif=sinif,
            ders=ders,
            unite=unite,
            kazanim_kodu=kazanim_kodu,
            baslangic_zamani=datetime.utcnow(),
            durum=SessionStatus.AKTIF,
            theta=0.0,
            can=3,
            puan=0,
            streak=0,
            istatistik=OturumIstatistik(),
            sorulmus_soru_idler=[],
            oyun_state=oyun_state,
        )

@dataclass
class CevapSonucu:
    dogru_mu:       bool
    dogru_cevap:    str
    aciklama:       str
    kazanilan_puan: int
    streak:         int
    yeni_theta:     float
    can:            int
    oyun_state:     Dict[str, Any]
    oturum_durumu:  SessionStatus
    sonuc:          Optional[str]
    oturum_ozeti:   Optional[Dict] = None

@dataclass
class Canavar:
    canavar_id: int
    ad:         str
    hp:         int
    direnc:     float

CANAVAR_KATALOGU: List[Canavar] = [
    Canavar(1, "Goblin",  hp=3,  direnc=1.0),
    Canavar(2, "Troll",   hp=5,  direnc=1.2),
    Canavar(3, "Ejderha", hp=8,  direnc=1.5),
    Canavar(4, "Kral",    hp=12, direnc=2.0),
]