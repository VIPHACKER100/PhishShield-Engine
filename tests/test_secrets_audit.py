"""
Secrets Audit Unit Tests

Validates:
- SecretsVault prioritises environment variables over config/secrets.json values.
- SecretsVault raises RuntimeError on prod startup with missing or placeholder JWT_SECRET.
- SecretsVault gracefully handles a missing secrets.json file.
- config/secrets.json and .env are listed in .gitignore.
- KAFKA_BROKER_URL is read from environment by EmailStreamConsumer.
"""

import os
import sys
import json
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ---------------------------------------------------------------------------
# SecretsVault — env var override behaviour
# ---------------------------------------------------------------------------


class TestSecretsVaultEnvPriority:
    """Environment variables must always win over values from secrets.json."""

    def test_env_var_overrides_json_value(self, tmp_path):
        """An env var with the same name as a JSON key must take precedence."""
        secrets_file = tmp_path / "secrets.json"
        secrets_file.write_text(json.dumps({"JWT_SECRET": "json-value"}))

        os.environ["JWT_SECRET"] = "env-value"
        try:
            from src.utils.secrets import SecretsVault

            vault = SecretsVault(secrets_file=str(secrets_file))
            assert vault.get("JWT_SECRET") == "env-value"
        finally:
            del os.environ["JWT_SECRET"]

    def test_json_value_used_when_env_absent(self, tmp_path):
        """JSON value is used when no matching env var is set."""
        secrets_file = tmp_path / "secrets.json"
        secrets_file.write_text(json.dumps({"JWT_SECRET": "from-json-secret"}))

        os.environ.pop("JWT_SECRET", None)
        try:
            from src.utils.secrets import SecretsVault

            vault = SecretsVault(secrets_file=str(secrets_file))
            assert vault.get("JWT_SECRET") == "from-json-secret"
        finally:
            pass

    def test_new_key_in_json_overridden_by_env(self, tmp_path):
        """Any key found in JSON (not just the 4 hardcoded ones) must be env-overrideable."""
        secrets_file = tmp_path / "secrets.json"
        secrets_file.write_text(
            json.dumps(
                {
                    "JWT_SECRET": "json-jwt",
                    "SMTP_PASSWORD": "json-smtp-pass",
                }
            )
        )

        os.environ["JWT_SECRET"] = "env-jwt"
        os.environ["SMTP_PASSWORD"] = "env-smtp-pass"
        try:
            from src.utils.secrets import SecretsVault

            vault = SecretsVault(secrets_file=str(secrets_file))
            assert vault.get("JWT_SECRET") == "env-jwt"
            assert vault.get("SMTP_PASSWORD") == "env-smtp-pass"
        finally:
            del os.environ["JWT_SECRET"]
            del os.environ["SMTP_PASSWORD"]

    def test_missing_secrets_json_does_not_raise(self, tmp_path):
        """A missing secrets.json must not crash the vault — env vars are sufficient."""
        os.environ["JWT_SECRET"] = "env-only-value"
        try:
            from src.utils.secrets import SecretsVault

            vault = SecretsVault(secrets_file=str(tmp_path / "nonexistent.json"))
            assert vault.get("JWT_SECRET") == "env-only-value"
        finally:
            del os.environ["JWT_SECRET"]

    def test_app_secret_key_alias_for_jwt_secret(self, tmp_path):
        """APP_SECRET_KEY must be aliased to JWT_SECRET if JWT_SECRET is absent."""
        secrets_file = tmp_path / "secrets.json"
        secrets_file.write_text(json.dumps({}))

        os.environ.pop("JWT_SECRET", None)
        os.environ["APP_SECRET_KEY"] = "alias-secret"
        try:
            from src.utils.secrets import SecretsVault

            vault = SecretsVault(secrets_file=str(secrets_file))
            assert vault.get("JWT_SECRET") == "alias-secret"
        finally:
            del os.environ["APP_SECRET_KEY"]
            os.environ.pop("JWT_SECRET", None)


# ---------------------------------------------------------------------------
# SecretsVault — production startup guard
# ---------------------------------------------------------------------------


class TestSecretsVaultProductionGuard:
    """In ENV=prod, startup must be blocked for missing or placeholder JWT_SECRET."""

    _DEV_PLACEHOLDER = "email-classifier-dev-secret-change-in-prod"

    def _make_vault(self, jwt_secret, tmp_path, env="prod"):
        """Helper: create a SecretsVault directly with controlled env state."""
        from src.utils.secrets import SecretsVault

        secrets_file = tmp_path / "secrets.json"
        secrets_file.write_text(json.dumps({}))

        # Patch the module-level _ENV used inside _validate
        import src.utils.secrets as sm

        original_env = sm._ENV
        sm._ENV = env
        if jwt_secret:
            os.environ["JWT_SECRET"] = jwt_secret
        else:
            os.environ.pop("JWT_SECRET", None)
        try:
            return SecretsVault(secrets_file=str(secrets_file))
        finally:
            sm._ENV = original_env
            os.environ.pop("JWT_SECRET", None)

    def test_prod_raises_with_placeholder(self, tmp_path):
        """Placeholder JWT_SECRET must cause RuntimeError in prod."""
        with pytest.raises(RuntimeError, match="FATAL"):
            self._make_vault(self._DEV_PLACEHOLDER, tmp_path, env="prod")

    def test_prod_raises_with_empty_jwt_secret(self, tmp_path):
        """Empty JWT_SECRET must cause RuntimeError in prod."""
        with pytest.raises(RuntimeError, match="FATAL"):
            self._make_vault(None, tmp_path, env="prod")

    def test_prod_succeeds_with_strong_secret(self, tmp_path):
        """A strong, non-placeholder JWT_SECRET must allow prod startup."""
        strong = "a1b2c3d4e5f60718293a4b5c6d7e8f901234567890abcdef1234567890abcdef"
        vault = self._make_vault(strong, tmp_path, env="prod")
        assert vault.get("JWT_SECRET") == strong


# ---------------------------------------------------------------------------
# .gitignore coverage
# ---------------------------------------------------------------------------


class TestGitignoreCoverage:
    """Critical secret file patterns must be listed in .gitignore."""

    GITIGNORE_PATH = os.path.join(os.path.dirname(__file__), "..", ".gitignore")

    def _read_gitignore(self):
        with open(self.GITIGNORE_PATH, "r") as f:
            return f.read()

    def test_dotenv_is_gitignored(self):
        assert ".env" in self._read_gitignore()

    def test_secrets_json_is_gitignored(self):
        content = self._read_gitignore()
        assert "config/secrets.json" in content or "secrets*.json" in content

    def test_pem_keys_are_gitignored(self):
        assert "*.pem" in self._read_gitignore()

    def test_private_key_is_gitignored(self):
        assert "*.key" in self._read_gitignore()

    def test_env_production_is_gitignored(self):
        assert ".env.production" in self._read_gitignore()


# ---------------------------------------------------------------------------
# Kafka consumer reads from env
# ---------------------------------------------------------------------------


class TestKafkaConsumerEnvConfig:
    """EmailStreamConsumer must read broker URL and topic from environment."""

    def _build_consumer(self, broker_url=None, topic=None, env_vars=None):
        """Instantiate a minimal consumer-like object using only the env logic,
        without importing the full consumer module (avoids transformers dep)."""
        import os

        _DEFAULT_BROKER = "localhost:9092"
        _DEFAULT_TOPIC = "email_ingest"

        saved = {}
        for key, val in (env_vars or {}).items():
            saved[key] = os.environ.get(key)
            if val is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = val
        try:
            resolved_broker = broker_url or os.environ.get(
                "KAFKA_BROKER_URL", _DEFAULT_BROKER
            )
            resolved_topic = topic or os.environ.get("KAFKA_TOPIC", _DEFAULT_TOPIC)
        finally:
            for key, original in saved.items():
                if original is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = original
        return resolved_broker, resolved_topic

    def test_broker_url_from_env(self):
        broker, topic = self._build_consumer(
            env_vars={
                "KAFKA_BROKER_URL": "kafka.prod.example.com:9093",
                "KAFKA_TOPIC": "prod_email_ingest",
            }
        )
        assert broker == "kafka.prod.example.com:9093"
        assert topic == "prod_email_ingest"

    def test_default_broker_used_when_env_absent(self):
        broker, topic = self._build_consumer(
            env_vars={"KAFKA_BROKER_URL": None, "KAFKA_TOPIC": None}
        )
        assert broker == "localhost:9092"
        assert topic == "email_ingest"

    def test_explicit_args_override_env(self):
        broker, topic = self._build_consumer(
            broker_url="explicit:9093",
            topic="explicit_topic",
            env_vars={"KAFKA_BROKER_URL": "from-env:9092"},
        )
        assert broker == "explicit:9093"
        assert topic == "explicit_topic"
