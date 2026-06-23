# ML Engineer Agent

## Purpose

Manages the machine learning lifecycle: data loading/preprocessing, feature engineering (TF-IDF/BOW vectorization), model training (individual + ensemble), hyperparameter tuning, evaluation, explainability (XAI via SHAP), deep learning (HuggingFace Transformers), vector search (ChromaDB), adaptive learning (feedback-based retraining), and model registry.

## Project Context

PhishShield-Engine's ML stack uses a multi-pipeline architecture:
- **Vectorization**: TF-IDF with sublinear scaling, bigrams, and character n-grams (3-5)
- **Traditional ML**: Naive Bayes, LinearSVC (calibrated), Logistic Regression, Random Forest, Gradient Boosting, LightGBM
- **Ensembles**: Voting (soft) and Stacking (Logistic Regression meta-learner)
- **Deep Learning**: `bert-base-uncased` via HuggingFace Transformers for phishing detection
- **Vector Search**: ChromaDB + SentenceTransformers (`all-MiniLM-L6-v2`) for semantic threat matching
- **XAI**: SHAP LinearExplainer for feature importance
- **Adaptive Learning**: Automated retraining triggered by feedback threshold

## Relevant Directories

| Directory | Purpose |
|-----------|---------|
| `src/models/` | All ML modules (train, predict, evaluate, ensemble, tuning, DL, vector search) |
| `src/features/` | Feature engineering (vectorizer.py with TF-IDF/BOW/char-n-gram) |
| `src/preprocessing/` | Text cleaning and normalization (text_cleaner.py) |
| `src/utils/data_loader.py` | Dataset loading, generation, and cleaning |
| `src/utils/data_versioning.py` | Dataset version tracking |
| `scripts/train_pipeline.py` | Main training pipeline entry point |
| `scripts/retrain_scheduler.py` | Background retraining daemon |
| `models/` | Trained model artifacts (.pkl), vectorizer, metrics, registry |
| `data/raw/` | Raw email datasets (CSV) |
| `data/processed/` | Preprocessed datasets |
| `data/feedback/` | User feedback for retraining (CSV + SQLite) |
| `data/versions/` | Versioned dataset snapshots |
| `experiments/` | Experiment log (experiment_log.json) |
| `notebooks/` | Jupyter notebooks for exploratory work |

## Available Models

| Model Key | Algorithm | Notes |
|-----------|-----------|-------|
| `naive_bayes` | MultinomialNB | Fast baseline, alpha=0.1 |
| `svm` | LinearSVC (calibrated) | CalibratedClassifierCV with cv=3 |
| `logistic_regression` | LogisticRegression | C=5.0, solver=saga |
| `random_forest` | RandomForestClassifier | Pipeline with MaxAbsScaler for sparse support |
| `gradient_boosting` | HistGradientBoostingClassifier | Densified via pipeline |
| `lgbm` | LGBMClassifier | Optional, pipeline with scaler |

## Common Workflows

### Full training pipeline (with synthetic data)

```bash
python scripts/train_pipeline.py --generate --n_samples 5000 --fast
```

Flags:
- `--fast`: sample_size=50000, skip ensemble
- `--tune`: RandomizedSearchCV tuning
- `--ensemble --ensemble_kind voting|stacking`: train ensemble after individual models
- `--vectorizer tfidf|bow|tfidf_char`: choose vectorization method
- `--stem`: apply Porter stemming (slower)
- `--sample_size N`: subsample rows for memory control

### Full production pipeline

```bash
python scripts/train_pipeline.py --generate --n_samples 100000 --ensemble --ensemble_kind stacking --tune --tune_iters 50 --vectorizer tfidf_char
```

### Train with real data

```bash
python scripts/train_pipeline.py --dataset_path "data/raw/vip/emails.csv" --sample_size 50000 --ensemble
```

### Evaluate a trained model interactively

```bash
python -c "
from src.models.predict import predict_email
result = predict_email('Free money! Click http://bit.ly/xyz', model_name='random_forest')
print(f'Prediction: {result[\"prediction\"]}')
print(f'Risk Score: {result[\"security_risk_score\"]}')
print(f'SHAP Analysis: {result[\"shap_analysis\"]}')
"
```

### Run all model tests

```bash
python -m pytest tests/test_model.py -v
```

### Inspect model registry

```bash
python -c "
from src.models.registry import list_models, get_best_model
print('All models:', list_models())
print('Best model:', get_best_model())
"
```

### View model metrics

```bash
python -c "import json; print(json.dumps(json.load(open('models/metrics.json')), indent=2))"
```

### Check feedback counts for retraining

```bash
python -c "from src.models.feedback import feedback_count; print(f'Feedback entries: {feedback_count()}')"
```

### Adaptive learning check

```bash
python src/models/adaptive_learning.py
```

### Deep learning test (requires transformers)

```bash
python -c "
from src.models.deep_learning import DeepLearningModel
dl = DeepLearningModel()
dl.load()
print(dl.predict('Your account has been compromised'))
"
```

### Vector similarity search test

```bash
python -c "
from src.models.vector_search import VectorSearchDB
vdb = VectorSearchDB()
vdb.initialize()
vdb.add_email('test1', 'Free money now', 'spam')
print(vdb.search_similar('Claim your prize'))
"
```

## XAI & Explainability

SHAP analysis is integrated into predictions. To see feature-level explanations:

```bash
python -c "
from src.models.predict import predict_email
result = predict_email('Congratulations you won a free gift card', model_name='logistic_regression')
print('Summary:', result['threat_explanation'])
print('SHAP tokens:', result['shap_analysis'])
"
```

## Experiment Tracking

Each training run is logged to `experiments/experiment_log.json` with timestamp, vectorizer, best model, and per-model metrics.

## Best Practices

1. Use `--fast` flag during development to iterate quickly
2. Pin `numpy==1.26.4` to avoid pickle compatibility issues
3. Always character n-grams (`tfidf_char`) in production ensembles for obfuscation robustness
4. Regular retraining via feedback loop (`scripts/retrain_scheduler.py`)
5. Use `--sample_size` for large corpora (>100k rows) to prevent OOM
