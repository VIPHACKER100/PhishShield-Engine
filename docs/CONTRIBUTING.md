# Contributing to PhishShield-Engine

We are thrilled you're interested in contributing to PhishShield-Engine! Our goal is to create the most robust, open-source AI email security platform.

This guide details exactly how you can set up your environment, contribute new features or datasets, and submit a Pull Request.

---

## 🛠️ 1. Setup Your Development Environment

### Prerequisites

- Python `3.11` or higher
- Git
- Docker & Docker Compose (for integration testing)

### Fork & Clone

1. Fork the `PhishShield-Engine` repository on GitHub.
2. Clone your fork locally:

   ```bash
   git clone https://github.com/viphacker100/PhishShield-Engine.git
   cd PhishShield-Engine
   ```

3. Set up the virtual environment and install the package in editable mode:

   ```bash
   python -m venv venv
   venv\Scripts\activate      # Windows
   # source venv/bin/activate # macOS/Linux

   pip install -e .
   ```

---

## 🏗️ 2. Project Architecture & Standards

Before writing code, please check our [Architecture Guide](ARCHITECTURE.md) and [Developer Guide](developer_guide.md).

### Coding Standards

- **Typing:** We use standard Python type hints (`from typing import Optional, List`). All new functions should have their parameters and return types hinted.
- **Docstrings:** Use simple, descriptive docstrings for all new methods and classes.
- **Logging:** Do **not** use `print()`. Use the custom initialized logger:

  ```python
  from src.utils.logger import logger
  logger.info("Connecting to Threat DB...")
  logger.error("Failed to parse email", exc_info=True)
  ```

---

## ✅ 3. Running the Test Suite

Before opening a pull request, ensure your code doesn't break existing functionality. We use `pytest` for unit testing.

1. **Run All Tests:**

   ```bash
   pytest tests/ -v
   ```

2. **Run ML Specific Tests:**
   If you modified the AI models in `src/models/`:

   ```bash
   pytest tests/test_model.py
   pytest tests/test_preprocessing.py
   ```

3. Ensure the test suite passes 100%.

---

## 📊 4. Contributing Threat Intelligence & Data

One of the easiest ways to help PhishShield is by submitting new threat indicators!

- **New Brands:** If you see a brand being heavily spoofed, open a PR adding it to the `brand_spoofing` section in `config/config.yaml`.
- **New Obfuscation Tricks:** If you discover a zero-width character or encoding bypass that isn't caught by `src/security/obfuscation_detector.py`, write a new regex or unicode blocker!
- **Data:** You can contribute raw `.csv` data for model training to `data/raw/` if it contains high-quality, sanitized ham/spam labels.

---

## 🔄 5. Submitting a Pull Request (PR)

1. Create a new branch logically tied to your feature or fix:

   ```bash
   git checkout -b feat/brand-detector-update
   ```

2. Make your changes locally, commit with a descriptive message:

   ```bash
   git commit -m "feat: Add Microsoft to the Brand Spoofing target list"
   ```

3. Push your branch to your fork:

   ```bash
   git push origin feat/brand-detector-update
   ```

4. Open a Pull Request on the main `PhishShield-Engine` repository. Ensure your PR description clearly states:
   - What the PR does.
   - Why it's necessary.
   - Any new dependencies you added to `requirements.txt` or `setup.py`.

We actively review PRs and will try to get back to you within 48 hours. Happy coding and happy hunting! 🛡️

---

**Maintainer**: VIPHACKER100 (Aryan Ahirwar)
**Last Updated**: 2026-04-03
