#!/usr/bin/env python
"""
Manage encrypted scores helper script.

Usage:
  python manage_scores.py decrypt   → Decrypt scores.json.enc to scores.json (plain)
  python manage_scores.py encrypt   → Encrypt scores.json to scores.json.enc
  python manage_scores.py wipe      → Clear all scores (start fresh)
  python manage_scores.py show      → Display current leaderboard
"""
import json
import sys
from pathlib import Path
from cryptography.fernet import Fernet


def get_key():
    """Load encryption key."""
    key_path = Path('data/.key')
    if not key_path.exists():
        print("❌ Chyba: data/.key neexistuje! Spusť hru nejdříve.")
        sys.exit(1)
    return key_path.read_bytes()


def decrypt_scores():
    """Decrypt scores.json.enc to scores.json."""
    enc_path = Path('data/scores.json.enc')
    plain_path = Path('data/scores.json')
    
    if not enc_path.exists():
        print("❌ Chyba: data/scores.json.enc neexistuje!")
        sys.exit(1)
    
    try:
        key = get_key()
        fernet = Fernet(key)
        encrypted = enc_path.read_bytes()
        decrypted = fernet.decrypt(encrypted)
        scores = json.loads(decrypted.decode('utf-8'))
        
        with plain_path.open('w', encoding='utf-8') as f:
            json.dump(scores, f, ensure_ascii=False, indent=2)
        
        print(f"✓ Decrypted → data/scores.json")
        print(f"✓ Hráči: {len(scores.get('players', []))}")
    except Exception as e:
        print(f"❌ Chyba: {e}")
        sys.exit(1)


def encrypt_scores():
    """Encrypt scores.json to scores.json.enc."""
    plain_path = Path('data/scores.json')
    enc_path = Path('data/scores.json.enc')
    
    if not plain_path.exists():
        print("❌ Chyba: data/scores.json neexistuje!")
        sys.exit(1)
    
    try:
        with plain_path.open('r', encoding='utf-8') as f:
            scores = json.load(f)
        
        key = get_key()
        fernet = Fernet(key)
        encrypted = fernet.encrypt(json.dumps(scores, ensure_ascii=False).encode('utf-8'))
        
        enc_path.write_bytes(encrypted)
        
        print(f"✓ Encrypted → data/scores.json.enc")
        print(f"✓ Hráči: {len(scores.get('players', []))}")
    except Exception as e:
        print(f"❌ Chyba: {e}")
        sys.exit(1)


def wipe_scores():
    """Clear all scores."""
    enc_path = Path('data/scores.json.enc')
    
    confirm = input("⚠️  Opravdu chceš smazat všechna skóre? (ano/ne): ").strip().lower()
    if confirm != 'ano':
        print("❌ Zrušeno.")
        sys.exit(0)
    
    try:
        key = get_key()
        fernet = Fernet(key)
        empty_scores = {"players": []}
        encrypted = fernet.encrypt(json.dumps(empty_scores, ensure_ascii=False).encode('utf-8'))
        
        enc_path.write_bytes(encrypted)
        print("✓ Skóre vymazány!")
    except Exception as e:
        print(f"❌ Chyba: {e}")
        sys.exit(1)


def show_scores():
    """Display current leaderboard."""
    enc_path = Path('data/scores.json.enc')
    
    if not enc_path.exists():
        print("❌ Žádné skóre zatím neexistují.")
        sys.exit(0)
    
    try:
        key = get_key()
        fernet = Fernet(key)
        encrypted = enc_path.read_bytes()
        decrypted = fernet.decrypt(encrypted)
        scores = json.loads(decrypted.decode('utf-8'))
        
        players = sorted(scores.get('players', []), key=lambda p: p.get('total_score', 0), reverse=True)
        
        if not players:
            print("Žádní hráči zatím.")
            return
        
        print("\n📋 LEADERBOARD")
        print("-" * 50)
        for i, p in enumerate(players, 1):
            print(f"{i}. {p['name']:<20} | Body: {p.get('total_score', 0):<6} | Výhry: {p.get('total_wins', 0)}")
        print("-" * 50)
    except Exception as e:
        print(f"❌ Chyba: {e}")
        sys.exit(1)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    
    command = sys.argv[1].lower()
    
    if command == 'decrypt':
        decrypt_scores()
    elif command == 'encrypt':
        encrypt_scores()
    elif command == 'wipe':
        wipe_scores()
    elif command == 'show':
        show_scores()
    else:
        print(f"❌ Neznámý příkaz: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == '__main__':
    main()
