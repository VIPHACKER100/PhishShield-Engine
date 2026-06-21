"""Pytest configuration and fixtures."""
import warnings

# Suppress httpx deprecation warning for TestClient
warnings.filterwarnings("ignore", category=DeprecationWarning, module="httpx")

# Suppress sklearn feature names warning for LGBM
warnings.filterwarnings("ignore", message="X does not have valid feature names")