# 🧠 PhishShield ML Training Guide

This guide covers the end-to-end machine learning lifecycle in PhishShield-Engine, from raw data ingestion to production model registration.

---

## 🏗️ Architecture Overview

The PhishShield ML stack is built for **high-throughput forensic classification** with fallback deep semantic understanding.

* **Vectorization**: Uses TF-IDF with sublinear scaling, bigrams, and character n-grams (3-5) to detect obfuscated phishing content.
* **Deep Learning**: Integration with HuggingFace Transformers (`bert-base-uncased`) via the `DeepLearningModel` class.
* **Vector Search**: Semantic caching and threat matching via `VectorSearchDB` powered by ChromaDB and SentenceTransformers.
* **Preprocessing**: Features high-speed vectorized cleaning (20-50x faster than traditional NLTK loops).
* **Models**: Supports Naive Bayes, Linear SVC (calibrated), Logistic Regression, Random Forest, and Gradient Boosting (HistGB/LightGBM).
* **Ensembles**: Advanced **Voting** and **Stacking** ensembles for maximum accuracy.
* **Explainability (XAI)**: Native `shap.LinearExplainer` integration to visualize feature importance.

---

## 🚀 Quick Start: Training your first model

If you are setting up for the first time, use the `--generate` flag to create a synthetic dataset:

```bash
# Fastest start: Generate 5k samples and train individual models
python scripts/train_pipeline.py --generate --n_samples 5000 --fast
```

> **Note:** The `--fast` flag now uses `sample_size=50000` and skips ensemble training by default.

---

## 🛠️ The Training Pipeline (`train_pipeline.py`)

The primary entry point is `scripts/train_pipeline.py`.

### 1. Data Loading & Sub-sampling

When working with huge corpora (like the 500k+ Enron dataset), use `--sample_size` to prevent memory exhaustion and speed up iteration.

```bash
# Train on a random 50,000 sample subset of the Enron corpus
python scripts/train_pipeline.py --dataset_path "data/raw/vip/emails.csv" --sample_size 50000
```

### 2. Choosing a Vectorizer

* `tfidf` (Default): Word-level TF-IDF with bigrams. Great for general spam.
* `bow`: Simple Bag-of-Words. Fast but less accurate.
* `tfidf_char`: **Character-level n-grams (3-5)**. Extremely robust against "leet-speak" (`P@yP@l`) and URL obfuscation.

```bash
python scripts/train_pipeline.py --vectorizer tfidf_char
```

### 3. Ensembles & Stacking

For production accuracy, use ensembles. 

* **Voting** (`--ensemble_kind voting`): Fast, combines probabilities from all models.
* **Stacking** (`--ensemble_kind stacking`): Slower, uses a Logistic Regression meta-learner to weigh model outputs.

```bash
python scripts/train_pipeline.py --ensemble --ensemble_kind stacking
```

### 4. Hyperparameter Tuning

Triggers `RandomizedSearchCV` to find optimal model parameters.

```bash
# Run 50 iterations of random search per model
python scripts/train_pipeline.py --tune --tune_iters 50
```

### 5. Porter Stemming

Enable stemming during preprocessing for enhanced semantic normalization (note: this increases training time).

```bash
python scripts/train_pipeline.py --stem
```

---

## 📊 Evaluation & Metrics

After training, results are saved to `models/metrics.json` and logged to `experiments/experiment_log.json`.

* **Accuracy**: Overall percentage of correct predictions.
* **Precision/Recall**: Crucial for phishing (we typically prioritize Recall to ensure no phishing reaches the inbox).
* **F1-Score**: The harmonic mean, used to select the "Best Model" for production.

---

## 🛡️ Best Practices for Production

1.  **Use --fast for Dev**: Iterating on the full 500k dataset takes 10+ minutes. Use `--fast` (50k samples, no ensemble) for testing code changes.
2.  **Character N-Grams**: Always include `tfidf_char` in your production ensemble to catch obfuscated text.
3.  **Regular Retraining**: Use the built-in feedback loop. User-reported "False Negatives" are stored in `data/feedback.db` (SQLite) and mirrored to `data/feedback/feedback_data.csv`.
4.  **Registration**: The pipeline automatically calls `src.models.registry.register_model()`. The `predict.py` script always loads the model marked as `best_model` in the registry.
5.  **Dependency Stability**: Pin `numpy==1.26.4` in your environment to avoid model pickle incompatibility across numpy versions.

---

## 🔧 Troubleshooting

| Issue | Solution |
| :--- | :--- |
| **"Unable to allocate X GiB"** | Use `--sample_size` or reduce `max_features` in `src/features/vectorizer.py`. |
| **"Missing required column: 'text'"** | The data loader now has auto-mapping, but ensure your CSV has a column like `message`, `content`, or `text`. |
| **"Only 1 unique class found"** | Your dataset is likely all 'ham'. Individual models like SVM will skip training. Ensure you have 'spam' labels. |

---

**Maintainer**: VIPHACKER100 (Aryan Ahirwar)
**Last Updated**: 2026-04-03
