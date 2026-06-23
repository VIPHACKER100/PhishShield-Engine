---
name: train-model
description: Train ML models on email datasets using the full training pipeline with synthetic or real data
---

# Skill: Train ML Models

## Description

Trains machine learning models on email datasets using the PhishShield-Engine training pipeline. Supports synthetic data generation, multiple vectorizers, individual models, hyperparameter tuning, and ensemble methods.

## Prerequisites

- Python environment with dependencies installed (`pip install -r requirements.txt`)
- Virtual environment activated
- Working directory at project root

## Workflow Steps

### 1. Quick training (dev mode)

```bash
python scripts/train_pipeline.py --generate --fast
```

This generates 50,000 synthetic samples and trains individual models (no ensemble). Suitable for testing code changes.

### 2. Full training with ensemble

```bash
python scripts/train_pipeline.py --generate --n_samples 100000 --ensemble --ensemble_kind voting
```

### 3. Training with hyperparameter tuning

```bash
python scripts/train_pipeline.py --generate --tune --tune_iters 30 --ensemble
```

### 4. Training on real dataset

```bash
python scripts/train_pipeline.py --dataset_path "data/raw/emails.csv" --sample_size 50000 --vectorizer tfidf_char
```

### 5. Training with character n-grams (best for obfuscation)

```bash
python scripts/train_pipeline.py --generate --vectorizer tfidf_char --ensemble
```

## Flags Reference

| Flag | Default | Description |
|------|---------|-------------|
| `--dataset_path` | `data/raw/emails.csv` | Path to training dataset |
| `--vectorizer` | `tfidf` | `tfidf`, `bow`, or `tfidf_char` |
| `--sample_size` | None | Subsample N rows (prevents OOM) |
| `--fast` | False | 50k samples, skip ensemble |
| `--tune` | False | RandomizedSearchCV tuning |
| `--tune_iters` | 20 | Random search iterations |
| `--ensemble` | False | Train ensemble after individual models |
| `--ensemble_kind` | `voting` | `voting` (fast) or `stacking` (accurate) |
| `--generate` | False | Generate synthetic dataset |
| `--n_samples` | 1000 | Size of synthetic dataset |
| `--stem` | False | Apply Porter stemming (slow) |
| `--model_dir` | `models` | Directory to save models |

## Output

- Trained models saved to `models/` directory as `.pkl` files
- Vectorizer saved to `models/vectorizer.pkl`
- Metrics saved to `models/metrics.json`
- Dataset version registered in `data/versions/`
- Model entries registered in `models/registry/registry.json`
- Experiment logged to `experiments/experiment_log.json`
- Preprocessed data saved to `data/processed/preprocessed.csv`

## Verification

```bash
# Check model files exist
ls models/*.pkl

# View metrics
python -c "import json; d=json.load(open('models/metrics.json')); print(f'Best model: {d[\"best_model\"]}')"

# Make a test prediction
python -c "from src.models.predict import predict_email; print(predict_email('Free money now!')['prediction'])"

# Run model tests
python -m pytest tests/test_model.py -v
```

## Best Practices

- Use `--fast` for dev iteration, full pipeline for production
- Character n-grams (`tfidf_char`) catch obfuscated text best
- Stacking ensembles give best accuracy but take 3x longer
- Pin `numpy==1.26.4` to avoid pickle compatibility issues
- Use `--sample_size` for datasets larger than 100k rows
