"""
Secrets Management — manages and isolates internal environment tokens.

Priority (highest to lowest):
  1. OS environment variables  ← always wins (all keys in the JSON file are overlaid)
  2. config/secrets.json       ← local dev convenience only (.gitignored)

In production (ENV=prod) the app will refuse to start if JWT_SECRET is missing
or is the well-known development placeholder.

Usage:
    from src.utils.secrets import vault
    jwt_secret = vault.get("JWT_SECRET")
"""

import os
import json
from src.utils.logger import logger

_DEV_PLACEHOLDER = "email-classifier-dev-secret-change-in-prod"
_ENV = os.environ.get("ENV", "dev").lower()


class SecretsVault:
    def __init__(self, secrets_file: str = "config/secrets.json"):
        self.file_path = secrets_file
        self.keys: dict = {}
        self._load()

    def _load(self):
        # 1. Load JSON file first (lowest priority)
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r") as f:
                    self.keys.update(json.load(f))
                logger.debug("Loaded secrets from '%s'.", self.file_path)
            except Exception as exc:
                logger.warning(
                    "Could not read secrets file '%s': %s", self.file_path, exc
                )

        # 2. Environment variables always win — overlay ALL keys that appear in the JSON,
        #    plus the core required keys. This ensures any new key added to secrets.json
        #    is automatically overrideable by a matching environment variable.
        keys_to_check = set(self.keys.keys()) | {
            "JWT_SECRET",
            "DATABASE_URL",
            "REDIS_HOST",
            "APP_SECRET_KEY",
            "KAFKA_BROKER_URL",
            "KAFKA_TOPIC",
            "SMTP_HOST",
            "SMTP_PORT",
            "SMTP_USER",
            "SMTP_PASSWORD",
            "SENTRY_DSN",
        }
        for key in keys_to_check:
            env_val = os.environ.get(key)
            if env_val:
                self.keys[key] = env_val

        # Alias: APP_SECRET_KEY may be used as an alternative name for JWT_SECRET
        if "APP_SECRET_KEY" in self.keys and "JWT_SECRET" not in self.keys:
            self.keys["JWT_SECRET"] = self.keys["APP_SECRET_KEY"]

        self._validate()

    def _validate(self):
        """Refuse to start in production with a missing or placeholder JWT secret."""
        secret = self.keys.get("JWT_SECRET", "")
        if _ENV == "prod":
            if not secret or secret == _DEV_PLACEHOLDER:
                raise RuntimeError(
                    "FATAL: JWT_SECRET is not set or is using the development placeholder. "
                    "Generate a strong secret with: "
                    'python -c "import secrets; print(secrets.token_hex(32))"'
                )
        elif not secret:
            # Dev mode: warn loudly and fall back to the placeholder
            logger.warning(
                "JWT_SECRET not set — using insecure dev placeholder. "
                "NEVER use this in production."
            )
            self.keys["JWT_SECRET"] = _DEV_PLACEHOLDER

    def get(self, key: str, default: str = None) -> str:
        """Return the secret for `key`, or `default` if absent."""
        val = self.keys.get(key)
        if not val:
            # Log at DEBUG level only — do not expose key names in operational WARNING logs
            logger.debug("Secret '%s' missing from vault.", key)
            return default
        return val


# Module-level singleton — import and use `vault.get("JWT_SECRET")` everywhere.
vault = SecretsVault()
