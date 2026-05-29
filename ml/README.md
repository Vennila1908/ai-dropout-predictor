# `ml/` — Machine learning artifacts and scripts

This folder is intentionally *thin* — most of the ML code lives inside the
backend (`backend/app/ml/`) so the FastAPI service can import it directly.

```
ml/
├── artifacts/             # model.joblib + model_meta.json (generated)
├── notebooks/             # for ad-hoc exploration; not used by the app
└── training_scripts/
    ├── train_baseline.py     # CLI: trains and saves the artifact
    └── generate_synthetic.py # CLI: writes datasets/synthetic_students.csv
```

## Train a model

```bash
# Activate the backend venv first.
python ml/training_scripts/train_baseline.py \
       --dataset datasets/sample_students.csv \
       --output  ml/artifacts
```

`train_baseline.py` reuses `backend/app/ml/train.py` (so training and
inference always agree on feature engineering). It tries Logistic Regression,
Random Forest, Gradient Boosting, and XGBoost (if installed), then keeps the
candidate with the best macro-F1 on a 20 % held-out split.

## Generate a fresh dataset

```bash
python ml/training_scripts/generate_synthetic.py --rows 5000
```

The generator uses the same labelling rule the model is asked to learn,
plus 10 % label noise so metrics aren't artificially perfect.

## Where the model is used

`backend/app/services/prediction_service.py` lazy-loads `ml/artifacts/model.joblib`
on the first prediction. If the artifact is missing, it auto-trains from
`datasets/sample_students.csv` so the API works out of the box.
