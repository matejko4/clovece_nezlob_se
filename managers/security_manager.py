from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken


class SecurityManager:
    """Provides encryption and hashing for game data."""

    KEY_FILE = "data/.key"

    def __init__(self) -> None:
        project_root = Path(__file__).resolve().parent.parent
        self.key_path = project_root / self.KEY_FILE
        self._fernet = Fernet(self.generate_key())

    def generate_key(self) -> bytes:
        """Generate Fernet key on first run and return active key."""
        self.key_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.key_path.exists():
            key = Fernet.generate_key()
            self.key_path.write_bytes(key)
            logging.info("Generated encryption key at %s", self.key_path)
            return key
        return self.key_path.read_bytes()

    def encrypt(self, data: dict) -> bytes:
        """Serialize and encrypt dictionary."""
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        return self._fernet.encrypt(payload)

    def decrypt(self, encrypted: bytes) -> dict:
        """Decrypt bytes and deserialize dictionary."""
        try:
            payload = self._fernet.decrypt(encrypted)
        except InvalidToken as exc:
            raise ValueError("Invalid encrypted payload.") from exc
        return json.loads(payload.decode("utf-8"))

    def hash_value(self, value: str) -> str:
        """Return SHA-256 hex digest for value."""
        return hashlib.sha256(value.encode("utf-8")).hexdigest()
