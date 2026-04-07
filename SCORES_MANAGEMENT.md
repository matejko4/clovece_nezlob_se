# 📊 Správa skórů (Scores Helper)

Helper skript pro editaci a správu šifrovaných skórů.

## Příkazy

### `python manage_scores.py show`
Zobrazí aktuální leaderboard.

```
📋 LEADERBOARD
--------------------------------------------------
1. Petr              | Body: 150          | Výhry: 5
2. Jana              | Body: 120          | Výhry: 3
--------------------------------------------------
```

### `python manage_scores.py decrypt`
**Dekryptuje** `data/scores.json.enc` do `data/scores.json` (plain text).

Používej, pokud chceš ručně editovat skóry:
```json
{
  "players": [
    {
      "name": "Petr",
      "total_score": 150,
      "total_wins": 5
    }
  ]
}
```

### `python manage_scores.py encrypt`
**Zašifruje** `data/scores.json` zpět na `data/scores.json.enc`.

Po editaci souboru:
```bash
python manage_scores.py decrypt   # Edituj data/scores.json
python manage_scores.py encrypt   # Zašifruj zpět
```

### `python manage_scores.py wipe`
⚠️ **Smaže všechna skóry** (vyžaduje potvrzení).

Užitečné k resetování pro testování.

## Pracovní postup na editaci

1. Dekryptuj skóry:
   ```bash
   python manage_scores.py decrypt
   ```

2. Otevři `data/scores.json` a edituj v editoru (JSON formát)

3. Zašifruj zpět:
   ```bash
   python manage_scores.py encrypt
   ```

4. Smaž `data/scores.json` ručně, pokud chceš (je to jen plain-text kopie)

## Bezpečnost

- Skóry jsou vždy šifrovány v `scores.json.enc`
- Klíč je v `data/.key`
- `scores.json` (plain) je jen dočasný soubor pro editaci
