#!/usr/bin/env python
"""
Encrypt questions helper script.

Use this to update encrypted questions:
1. Edit data/questions.json (plain text)
2. Run: python encrypt_questions.py
3. Encrypted version is saved to data/questions.json.enc
"""
import json
from pathlib import Path
from cryptography.fernet import Fernet

# Load the encryption key
key_path = Path('data/.key')
if not key_path.exists():
    print("❌ Chyba: data/.key neexistuje! Spusť hru nejdříve.")
    exit(1)

key = key_path.read_bytes()

# Load plain text questions
plain_path = Path('data/questions.json')
if not plain_path.exists():
    print("❌ Chyba: data/questions.json neexistuje!")
    print("Vytvoř si ho nejdříve se svými otázkami.")
    exit(1)

try:
    with plain_path.open('r', encoding='utf-8') as f:
        questions = json.load(f)
    print(f"✓ Nabito {len(questions)} otázek")
except Exception as e:
    print(f"❌ Chyba při čtení: {e}")
    exit(1)

# Encrypt
try:
    fernet = Fernet(key)
    encrypted = fernet.encrypt(json.dumps(questions, ensure_ascii=False).encode('utf-8'))
    
    enc_path = Path('data/questions.json.enc')
    enc_path.write_bytes(encrypted)
    print(f"✓ Otázky šifrovány ✓ → data/questions.json.enc")
    print(f"✓ Celkem otázek: {len(questions)}")
except Exception as e:
    print(f"❌ Chyba při šifrování: {e}")
    exit(1)
