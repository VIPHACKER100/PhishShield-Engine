"""
Secrets Management Hub (Phase 67)
Manages and isolates internal environmental tokens decoupled from application code.
"""
import os
import json
from src.utils.logger import logger

class SecretsVault:
    def __init__(self, secrets_file: str = "config/secrets.json"):
        self.file_path = secrets_file
        self.keys = {}
        self._load()
        
    def _load(self):
        # Always prefer hardware/environment level secrets over JSON files
        env_secret = os.getenv("APP_SECRET_KEY")
        if env_secret:
            self.keys["JWT_SECRET"] = env_secret
            
        if os.path.exists(self.file_path):
            with open(self.file_path, "r") as f:
                self.keys.update(json.load(f))
                
    def get(self, key: str, default: str = None) -> str:
        """Securely return loaded environment variable."""
        val = self.keys.get(key)
        if not val:
            logger.warning("Secret '%s' missing from vault.", key)
            return default
        return val

# Instantiate singleton
vault = SecretsVault()
