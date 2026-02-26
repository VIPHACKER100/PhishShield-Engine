#!/usr/bin/env python
"""
Training Pipeline — End-to-end CLI script for dataset generation,
preprocessing, feature extraction, model training, evaluation,
hyperparameter tuning, and ensemble training.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

# Ensure project root is importable
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


def run_pipeline(
    dataset_path: str = "data/raw/emails.csv",
    vectorizer_method: str = "tfidf",
    model_dir: str = "models",
    generate: bool = False,
    tune: bool = False,
    ensemble: bool = False,
    n_samples: int = 1000,
):
    """Execute the full training pipeline."""
    logger.info("=" * 60)
    logger.info("EMAIL SPAM CLASSIFIER — TRAINING PIPELINE")
    logger.info("=" * 60)

    # ---- Step 1: Dataset ----
    if generate or not os.path.exists(dataset_path):
        logger.info("Generating synthetic dataset (%d samples)...", n_samples)
        df = generate_sample_dataset(dataset_path, n_samples)
    else:
        df = load_dataset(dataset_path)

    # Version the dataset
    version_tag = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    data_meta = register_version(dataset_path, version_tag, f"Training run at {datetime.now()}")

    df = clean_dataset(df)

    # ---- Step 2: Preprocessing ----
    logger.info("Preprocessing text...")
    df = preprocess_dataframe(df)
    df.to_csv("data/processed/preprocessed.csv", index=False)

    # ---- Step 3: Vectorisation ----
    logger.info("Vectorising with %s...", vectorizer_method.upper())
    X = df["text"]
    y = df["label"]
    X_train, X_test, y_train, y_test = split_data(X, y)

    vec, X_train_vec = fit_and_save(X_train, vectorizer_method, os.path.join(model_dir, "vectorizer.pkl"))
    X_test_vec = vec.transform(X_test)

    # ---- Step 4: Train models ----
    logger.info("Training models...")
    models = train_all(X_train_vec, y_train, model_dir)

    # ---- Step 5: Evaluate ----
    logger.info("Evaluating models...")
    report = evaluate_all(models, X_test_vec, y_test, os.path.join(model_dir, "metrics.json"))

    # Register each model in the registry
    for res in report["results"]:
        model_name = res["model"]
        register_model(
            model_name=model_name,
            algorithm=model_name,
            parameters={},  # Would need to pull from model object if non-default
            metrics={k: v for k, v in res.items() if k != "model"},
            file_path=os.path.join(model_dir, f"{model_name}.pkl"),
            dataset_version=version_tag
        )

    # ---- Step 6 (optional): Hyperparameter tuning ----
    if tune:
        logger.info("Running hyperparameter tuning (this may take a while)...")
        tune_all(X_train_vec, y_train, model_dir)

    # ---- Step 7 (optional): Ensemble ----
    if ensemble:
        logger.info("Training ensemble model...")
        ens = train_ensemble(X_train_vec, y_train, model_dir)
        from src.models.evaluate import evaluate_model
        ens_metrics = evaluate_model(ens, X_test_vec, y_test, "ensemble_model")
        report["results"].append(ens_metrics)

        # Register ensemble
        register_model(
            model_name="ensemble_model",
            algorithm="VotingClassifier",
            parameters={},
            metrics={k: v for k, v in ens_metrics.items() if k != "model"},
            file_path=os.path.join(model_dir, "ensemble_model.pkl"),
            dataset_version=version_tag
        )

        # Re-pick best
        best = max(report["results"], key=lambda r: r["f1_score"])
        report["best_model"] = best["model"]
        with open(os.path.join(model_dir, "metrics.json"), "w") as f:
            json.dump(report, f, indent=2)

    # ---- Step 8: Experiment log ----
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
            logs = json.load(f)
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
    parser = argparse.ArgumentParser(description="Email Spam Classifier — Training Pipeline")
    parser.add_argument("--dataset_path", default="data/raw/emails.csv", help="Path to dataset CSV")
    parser.add_argument("--model_type", default="tfidf", choices=["tfidf", "bow"], help="Vectoriser method")
    parser.add_argument("--model_dir", default="models", help="Directory to save models")
    parser.add_argument("--generate", action="store_true", help="Generate synthetic dataset")
    parser.add_argument("--tune", action="store_true", help="Run hyperparameter tuning")
    parser.add_argument("--ensemble", action="store_true", help="Train ensemble model")
    parser.add_argument("--n_samples", type=int, default=1000, help="Synthetic dataset size")
    args = parser.parse_args()

    run_pipeline(
        dataset_path=args.dataset_path,
        vectorizer_method=args.model_type,
        model_dir=args.model_dir,
        generate=args.generate,
        tune=args.tune,
        ensemble=args.ensemble,
        n_samples=args.n_samples,
    )


if __name__ == "__main__":
    main()
