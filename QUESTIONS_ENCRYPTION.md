# 🔒 Ochrana otázek (Encryption)

Otázky pro kvíz jsou teď **šifrovány** a uloženy v souboru `data/questions.json.enc`.

Běžný text soubor `questions.json` byl smazán pro bezpečnost - pouze ty máš přístup přes klíč v `data/.key`.

## Jak upravit otázky

1. **Vytvoř si `data/questions.json`** s novými otázkami (kopíruj starý formát):
```json
[
  {
    "question": "Moje otázka?",
    "options": ["Odpověď A", "Odpověď B", "Odpověď C"],
    "correct": 0
  }
]
```

2. **Spusť:** `python encrypt_questions.py`
   - Přečte otázky z `questions.json`
   - Zašifruje je do `questions.json.enc`
   - Smaž si pak `questions.json` ručně (pokud chceš)

3. **Hra automaticky načte** šifrované otázky

## Bezpečnost

- Klíč v `data/.key` je tajný (nedej si ho nikam 👀)
- Jen s tímto klíčem se dají otázky dešifrovat
- Šifrování používá **Fernet** (stejné jako skóre)
