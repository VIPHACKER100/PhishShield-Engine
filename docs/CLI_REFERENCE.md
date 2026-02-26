# 💻 PhishShield-Engine: CLI Reference

The **PhishShield-Engine** includes a powerful command-line interface (`cli/manage.py`) to help administrators orchestrate the system without writing code or hitting API endpoints directly.

---

## 🚀 1. Starting the Server

Quickly spin up the Uvicorn-backed FastAPI application.

```bash
python cli/manage.py serve
```

**Options:**

- `--port <number>`: Override the default port (8000).

*Example:* `python cli/manage.py serve --port 8080`

---

## 🛡️ 2. Threat Intelligence Management

Manually inject malicious domains directly into the Threat Intelligence SQLite database. Future API calls processing emails with this domain will be immediately flagged as `SPAM`.

```bash
python cli/manage.py block <domain>
```

**Options:**

- `--reason "<Text>"`: Attach a manual string specifying why this string is blocked.

*Example:* `python cli/manage.py block attacker-crypto.com --reason "Bitcoin scam campaign"`

---

## 📊 3. System Metrics

Retrieve a real-time summary of the system's threat blocklist and current intelligence states.

```bash
python cli/manage.py metrics
```

**Output Example:**

```text
--- System Intelligence Metrics ---
Blocked Domains: 154
```

---

## 🛠️ Advanced Automation (Scripts)

While `manage.py` handles primary runtime tasks, the `scripts/` directory operates the DevOps lifecycle:

- `python scripts/train_pipeline.py`: Triggers an immediate vectorization, dataset parsing, and ML training routine. Use `--ensemble` to stack all 3 models.
- `python scripts/benchmark.py`: Fires an `asyncio` stress test delivering thousands of bulk payloads to evaluate API latency.
- `python scripts/retrain_scheduler.py`: A daemon process monitoring `feedback.db`. Runs `train_pipeline.py` silently in the background if threshold drift occurs.
- `python scripts/restore_backup.py <backup_id>`: Restores system registries, metrics, and models from a previously snapshotted environment.
