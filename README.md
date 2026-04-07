# Dokumentace - Clovece nezlob se

## Cíl aplikace
Cilem je vytvorit desktopovou hru Clovece, nezlob se pro 2-4 hrace (lide i jednoducha AI) s casovym limitem tahu, prubeznym bodovanim a perzistentnim ulozenim skore.

## Zvolená varianta a technologie
- Jazyk: Python 3.10+
- GUI: Pygame
- Ulozeni dat: JSON + sifrovani Fernet
- Hashovani: SHA-256 (`hashlib`)

## Struktura projektu (popis souborů)
- `main.py`: vstupni bod aplikace.
- `game/`: herni logika (deska, hrac, figurka, kostka, tahy, hlavni smycka).
- `managers/`: sprava dat, sifrovani, casovace a skore.
- `ui/`: vykresleni desky, HUD, menu, dialogove notifikace.
- `data/`: konfigurace, pravidla a sifrovane skore.
- `docs/`: dokumentace.

## Použité knihovny
- `pygame`: okno, vykreslovani, vstupy, udalosti.
- `cryptography.fernet`: symetricke sifrovani hernich dat.
- `hashlib`: SHA-256 hash hodnot.
- `threading`, `time`, `json`, `logging`, `pathlib`: podpora casovace, IO a diagnostiky.

## Popis tříd
- `Game`: ridi cely prubeh hry, smycku, vstupy, AI, prechody tahu a konec hry.
- `Board`: overuje validitu tahu, aplikuje pohyb, obsazenost a sebrani figurek.
- `Player`: drzi informace o hraci, figurkach, skore a AI rozhodovani.
- `Piece`: reprezentuje jednu figurku a jeji stav.
- `Dice`: realizuje hod kostkou a kratkou animaci.
- `RoundManager`: poradi hracu a timeout signalizace.
- `TimerManager`: odpoctovy casovac tahu.
- `ScoreManager`: body v aktualni hre + trvale statistiky mezi hrami.
- `DataManager`: nacitani/ukladani konfigurace a sifrovanych dat.
- `SecurityManager`: sprava klice, sifrovani/dekryptovani, hashovani.
- `Renderer`, `HUD`, `Menu`, `Dialogs`: GUI vrstva hry.

## Popis datových souborů
- `data/config.json`: nastaveni hry (limity, scoring, safe pole).
- `data/game_rules.json`: rozsirena pravidla (volitelna).
- `data/scores.json.enc`: sifrovane perzistentni statistiky hracu.
- `data/questions.json.enc`: sifrovane otazky pro kviz.
- `data/.key`: lokalni sifrovaci klic vytvoreny pri prvnim spusteni.

## Způsob bodování
- +10 bodu za dokonceni figurky (`finish_piece`).
- +5 bodu za sebrani soupere (`capture`).
- +30 bodu za vyhru cele hry (`win_bonus`).
- -2 body pri timeoutu tahu (`timeout`).

Skore je viditelne v realnem case v HUD a po skonceni hry v zebricku.

## Způsob ochrany řešení
- Pouzit pristup: Fernet sifrovani + SHA-256 hashovani.
- Vyhody:
  - Skore a citliva data nejsou citelna prostym otevrenim souboru.
  - Integrita dat je lepe kontrolovatelna a format je jednotny.
- Limity:
  - Klic je ulozen lokalne v souborovem systemu.
  - Utocnik s plnym pristupem k disku muze klic dohledat.
  - Nejde o absolutni ochranu, ale o ochranu proti trivialnimu prozrazeni.

## Helper skripty
- `encrypt_questions.py`: Edituj a zašifruj otázky
  - `python encrypt_questions.py` - zašifruje `data/questions.json` do `.enc`
  - Viz `QUESTIONS_ENCRYPTION.md`
- `manage_scores.py`: Správa skórů
  - `python manage_scores.py show` - aktuální leaderboard
  - `python manage_scores.py decrypt` - dekryptuj skóry (editace)
  - `python manage_scores.py encrypt` - zašifruj skóry zpět
  - `python manage_scores.py wipe` - smazat všechna skóry
  - Viz `SCORES_MANAGEMENT.md`

## Návod k ovládání
- `Sipky` v menu meni parametry hry.
- `Enter` v menu potvrdi volbu a spusti hru.
- V tahu lidskeho hrace:
  - `Mezernik` = hod kostkou.
  - `Klik` na figurku nebo `1-4` = vyber figurky k tahu.
- `P` = pauza (pokracovat/restart/konec).

## Prezentace / ukázka
Spusteni:

```bash
pip install -r requirements.txt
python main.py
```

Pri prvnim spusteni se vytvori sifrovaci klic `data/.key`. Soubor `data/scores.json.enc` se pri ukladani vytvori automaticky.
