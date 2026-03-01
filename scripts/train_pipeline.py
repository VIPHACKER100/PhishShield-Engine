#!/usr/bin/env python
"""
Training Pipeline — Upgraded end-to-end CLI script.

New flags vs v1
---------------
--sample_size N      Subsample N rows from the dataset before training
                     (recommended for quick iteration on huge corpora).
--vectorizer METHOD  tfidf (default) | bow | tfidf_char
--ensemble_kind      voting (default) | stacking
--stem               Enable Porter stemming during preprocessing (slow)
--tune_iters N       Number of random search iterations for --tune
--fast               Shortcut: sample_size=50 000 + skip ensemble
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.utils.data_loader import generate_sample_dataset, load_dataset, clean_dataset
from src.preprocessing.text_cleaner import preprocess_dataframe
from src.features.vectorizer import fit_and_save
from src.models.train_models import split_data, train_all
from src.models.evaluate import evaluate_all
from src.models.hyperparameter_tuning import tune_all
from src.models.ensemble import train_ensemble
from src.utils.data_versioning import register_version
from src.models.registry import register_model
from src.utils.logger import logger


# ---------------------------------------------------------------------------

def run_pipeline(
    dataset_path: str = "data/raw/emails.csv",
    vectorizer_method: str = "tfidf",
    model_dir: str = "models",
    generate: bool = False,
    tune: bool = False,
    ensemble: bool = False,
    ensemble_kind: str = "voting",
    n_samples: int = 1000,
    sample_size: int | None = None,
    stem: bool = False,
    tune_iters: int = 20,
):
    """Execute the full training pipeline."""
    logger.info("=" * 60)
    logger.info("EMAIL SPAM CLASSIFIER — TRAINING PIPELINE")
    logger.info("=" * 60)

    # ── Step 1: Dataset ─────────────────────────────────────────────────────
    if generate or not os.path.exists(dataset_path):
        logger.info("Generating synthetic dataset (%d samples)...", n_samples)
        df = generate_sample_dataset(dataset_path, n_samples)
    else:
        df = load_dataset(dataset_path)

    # Optional sub-sampling (important for fast iteration on huge corpora)
    if sample_size and sample_size < len(df):
        logger.info(
            "Sub-sampling %d rows from %d (use --sample_size 0 to disable).",
            sample_size, len(df),
        )
        df = df.sample(sample_size, random_state=42).reset_index(drop=True)

    # Version the dataset
    version_tag = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    data_meta = register_version(dataset_path, version_tag, f"Training run at {datetime.now()}")

    df = clean_dataset(df)

    # ── Step 2: Preprocessing ───────────────────────────────────────────────
    logger.info("Preprocessing text (stem=%s)...", stem)
    df = preprocess_dataframe(df, stem=stem)
    os.makedirs("data/processed", exist_ok=True)
    df.to_csv("data/processed/preprocessed.csv", index=False)

    # ── Step 3: Vectorisation ───────────────────────────────────────────────
    logger.info("Vectorising with %s...", vectorizer_method.upper())
    X = df["text"]
    y = df["label"]
    X_train, X_test, y_train, y_test = split_data(X, y)

    vec, X_train_vec = fit_and_save(
        X_train, vectorizer_method,
        os.path.join(model_dir, "vectorizer.pkl"),
    )
    X_test_vec = vec.transform(X_test)

    # ── Step 4: Train models ─────────────────────────────────────────────────
    logger.info("Training models...")
    models = train_all(X_train_vec, y_train, model_dir)

    # ── Step 5: Evaluate ─────────────────────────────────────────────────────
    logger.info("Evaluating models...")
    report = evaluate_all(models, X_test_vec, y_test,
                          os.path.join(model_dir, "metrics.json"))

    for res in report["results"]:
        model_name = res["model"]
        register_model(
            model_name=model_name,
            algorithm=model_name,
            parameters={},
            metrics={k: v for k, v in res.items() if k != "model"},
            file_path=os.path.join(model_dir, f"{model_name}.pkl"),
            dataset_version=version_tag,
        )

    # ── Step 6 (optional): Hyperparameter tuning ────────────────────────────
    if tune:
        logger.info("Running hyperparameter tuning (%d iters)...", tune_iters)
        tune_all(X_train_vec, y_train, model_dir, n_iter=tune_iters)

    # ── Step 7 (optional): Ensemble ──────────────────────────────────────────
    if ensemble:
        logger.info("Training %s ensemble...", ensemble_kind)
        ens = train_ensemble(X_train_vec, y_train, model_dir, kind=ensemble_kind)

        from src.models.evaluate import evaluate_model
        ens_name = f"ensemble_{ensemble_kind}"
        ens_metrics = evaluate_model(ens, X_test_vec, y_test, ens_name)
        report["results"].append(ens_metrics)

        register_model(
            model_name=ens_name,
            algorithm=f"{ensemble_kind.capitalize()}Ensemble",
            parameters={},
            metrics={k: v for k, v in ens_metrics.items() if k != "model"},
            file_path=os.path.join(
                model_dir,
                "ensemble_stacking.pkl" if ensemble_kind == "stacking"
                else "ensemble_model.pkl",
            ),
            dataset_version=version_tag,
        )

        best = max(report["results"], key=lambda r: r["f1_score"])
        report["best_model"] = best["model"]
        with open(os.path.join(model_dir, "metrics.json"), "w") as f:
            json.dump(report, f, indent=2)

    # ── Step 8: Experiment log ───────────────────────────────────────────────
    _log_experiment(report, vectorizer_method)

    logger.info("=" * 60)
    logger.info("PIPELINE COMPLETE — Best model: %s", report["best_model"])
    logger.info("=" * 60)
    return report


def _log_experiment(report: dict, vectorizer_method: str):
    """Append run to experiments/experiment_log.json."""
    log_path = "experiments/experiment_log.json"
    os.makedirs("experiments", exist_ok=True)
    logs = []
    if os.path.exists(log_path):
        with open(log_path) as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []
    logs.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "vectorizer": vectorizer_method,
        "best_model": report["best_model"],
        "results": report["results"],
    })
    with open(log_path, "w") as f:
        json.dump(logs, f, indent=2)
    logger.info("Experiment logged → %s", log_path)


def main():
    parser = argparse.ArgumentParser(
        description="PhishShield — Email Spam Classifier Training Pipeline"
    )
    parser.add_argument(
        "--dataset_path", default="data/raw/emails.csv",
        help="Path to dataset CSV",
    )
    parser.add_argument(
        "--vectorizer", "--model_type", dest="vectorizer",
        default="tfidf", choices=["tfidf", "bow", "tfidf_char"],
        help="Vectoriser method (default: tfidf)",
    )
    parser.add_argument("--model_dir", default="models",
                        help="Directory to save models")
    parser.add_argument("--generate", action="store_true",
                        help="Generate synthetic dataset instead of loading one")
    parser.add_argument("--tune", action="store_true",
                        help="Run hyperparameter tuning after training")
    parser.add_argument("--ensemble", action="store_true",
                        help="Train an ensemble model after individual models")
    parser.add_argument(
        "--ensemble_kind", default="voting", choices=["voting", "stacking"],
        help="Ensemble type: 'voting' (fast) or 'stacking' (accurate, slow)",
    )
    parser.add_argument("--n_samples", type=int, default=1000,
                        help="Size of synthetic dataset when --generate is used")
    parser.add_argument(
        "--sample_size", type=int, default=None,
        help="Sub-sample N rows from the dataset before training "
             "(0 = no sub-sampling). Recommended for large corpora.",
    )
    parser.add_argument("--stem", action="store_true",
                        help="Apply Porter stemming during preprocessing (slow)")
    parser.add_argument("--tune_iters", type=int, default=20,
                        help="RandomizedSearchCV iterations for --tune")
    parser.add_argument(
        "--fast", action="store_true",
        help="Quick mode: sample_size=50000, skip ensemble",
    )
    args = parser.parse_args()

    sample_size = args.sample_size
    do_ensemble = args.ensemble
    if args.fast:
        sample_size = sample_size or 50_000
        do_ensemble = False
        logger.info("--fast mode: using sample_size=%d, ensemble disabled", sample_size)

    run_pipeline(
        dataset_path=args.dataset_path,
        vectorizer_method=args.vectorizer,
        model_dir=args.model_dir,
        generate=args.generate,
        tune=args.tune,
        ensemble=do_ensemble,
        ensemble_kind=args.ensemble_kind,
        n_samples=args.n_samples,
        sample_size=sample_size,
        stem=args.stem,
        tune_iters=args.tune_iters,
    )


if __name__ == "__main__":
    main()
