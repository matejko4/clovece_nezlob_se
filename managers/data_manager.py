from __future__ import annotations

import json
import logging
from pathlib import Path

from managers.security_manager import SecurityManager


class DataCorruptedError(Exception):
    """Raised when persisted data cannot be read safely."""


class DataManager:
    """Loads and saves game configuration and data."""

    DEFAULT_CONFIG = {
        "time_limit_seconds": 30,
        "max_players": 4,
        "default_players": 2,
        "ai_enabled": True,
        "sound_enabled": True,
        "language": "cs",
        "safe_cells": [0, 8, 13, 18, 21, 26, 31, 34, 39],
        "scoring": {
            "finish_piece": 10,
            "capture": 5,
            "win_bonus": 30,
            "timeout_penalty": -2,
        },
    }

    DEFAULT_QUIZ_QUESTIONS = [
        {
            "question": "Co znamená zkratka CPU?",
            "options": ["Central Processing Unit", "Computer Power Utility", "Control Program User"],
            "correct": 0,
        },
        {
            "question": "Která část počítače dlouhodobě ukládá data?",
            "options": ["RAM", "SSD/HDD", "Cache"],
            "correct": 1,
        },
        {
            "question": "Co je to phishing?",
            "options": ["Typ antiviru", "Podvodné vylákání údajů", "Formát disku"],
            "correct": 1,
        },
        {
            "question": "K čemu slouží operační systém?",
            "options": ["Jen na hry", "Řídí hardware a programy", "Zrychluje internet"],
            "correct": 1,
        },
        {
            "question": "Co je IP adresa?",
            "options": ["Adresa zařízení v síti", "Název webu", "Heslo k Wi-Fi"],
            "correct": 0,
        },
        {
            "question": "Který souborový formát je typicky obrázek?",
            "options": [".jpg", ".exe", ".mp3"],
            "correct": 0,
        },
        {
            "question": "Co je silné heslo?",
            "options": ["12345678", "jmeno123", "Kombinace písmen, čísel a znaků"],
            "correct": 2,
        },
        {
            "question": "Co dělá firewall?",
            "options": ["Čistí monitor", "Filtruje síťový provoz", "Zkracuje boot"],
            "correct": 1,
        },
    ]

    def __init__(self) -> None:
        self.project_root = Path(__file__).resolve().parent.parent
        self.config_path = self.project_root / "data/config.json"

    def load_config(self) -> dict:
        """Load configuration, fallback to defaults when missing/broken."""
        if not self.config_path.exists():
            logging.warning("Missing config.json, using defaults.")
            return dict(self.DEFAULT_CONFIG)

        try:
            with self.config_path.open("r", encoding="utf-8") as handle:
                user_config = json.load(handle)
            merged = dict(self.DEFAULT_CONFIG)
            merged.update(user_config)
            if "scoring" in user_config and isinstance(user_config["scoring"], dict):
                merged_scoring = dict(self.DEFAULT_CONFIG["scoring"])
                merged_scoring.update(user_config["scoring"])
                merged["scoring"] = merged_scoring
            return merged
        except Exception:
            logging.warning("Invalid config.json, using defaults.")
            return dict(self.DEFAULT_CONFIG)

    def save_config(self, config: dict) -> None:
        """Persist configuration as JSON."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with self.config_path.open("w", encoding="utf-8") as handle:
            json.dump(config, handle, ensure_ascii=False, indent=2)

    def load_quiz_questions(self) -> list[dict]:
        """Load quiz questions for in-game gate from encrypted file."""
        security = SecurityManager()
        encrypted_path = self.project_root / "data/questions.json.enc"
        plain_path = self.project_root / "data/questions.json"

        # Try loading encrypted version first (preferred)
        if encrypted_path.exists():
            try:
                loaded = self.load_encrypted("data/questions.json.enc", security)
                if isinstance(loaded, list):
                    validated = self._validate_questions(loaded)
                    if validated:
                        return validated
            except Exception as exc:
                logging.warning("Failed to load encrypted questions: %s", exc)

        # Fallback: try plain JSON
        if plain_path.exists():
            try:
                with plain_path.open("r", encoding="utf-8") as handle:
                    loaded = json.load(handle)
                validated = self._validate_questions(loaded)
                if validated:
                    return validated
            except Exception:
                logging.warning("Invalid questions.json, using built-in quiz questions.")

        # Last resort: use built-ins
        plain_path.parent.mkdir(parents=True, exist_ok=True)
        with plain_path.open("w", encoding="utf-8") as handle:
            json.dump(self.DEFAULT_QUIZ_QUESTIONS, handle, ensure_ascii=False, indent=2)
        return list(self.DEFAULT_QUIZ_QUESTIONS)

    def _validate_questions(self, loaded: list) -> list[dict]:
        """Validate and filter quiz questions."""
        validated: list[dict] = []
        if isinstance(loaded, list):
            for item in loaded:
                if not isinstance(item, dict):
                    continue
                question = item.get("question")
                options = item.get("options")
                correct = item.get("correct")
                if not isinstance(question, str):
                    continue
                if not isinstance(options, list) or len(options) != 3 or not all(isinstance(x, str) for x in options):
                    continue
                if not isinstance(correct, int) or correct not in (0, 1, 2):
                    continue
                validated.append({"question": question, "options": options, "correct": correct})
        return validated

    def load_encrypted(self, filepath: str, security: SecurityManager) -> dict:
        """Load encrypted file and decrypt it, handling corruption cases."""
        path = self.project_root / filepath
        try:
            with path.open("rb") as handle:
                return security.decrypt(handle.read())
        except FileNotFoundError:
            return {}
        except Exception as exc:
            raise DataCorruptedError(f"Soubor {filepath} je poškozen nebo neplatný.") from exc

    def save_encrypted(self, filepath: str, data: dict, security: SecurityManager) -> None:
        """Encrypt and save data to file."""
        path = self.project_root / filepath
        path.parent.mkdir(parents=True, exist_ok=True)
        encrypted = security.encrypt(data)
        with path.open("wb") as handle:
            handle.write(encrypted)
