# Explainable AI

A risk score without an explanation is unusable in a counseling workflow.
Every prediction this system returns is paired with a structured explanation.

## 1. Output Shape

```json
{
  "risk_level": "high",
  "confidence": 0.87,
  "model_version": "RandomForestClassifier@2025-01-12",
  "top_factors": [
    {"feature": "attendance_pct", "value": 52.0, "contribution": +0.31, "direction": "increases_risk"},
    {"feature": "backlogs",       "value": 4,    "contribution": +0.22, "direction": "increases_risk"},
    {"feature": "internal_marks", "value": 38,   "contribution": +0.18, "direction": "increases_risk"},
    {"feature": "engagement_score","value": 0.41,"contribution": -0.05, "direction": "decreases_risk"}
  ],
  "narrative": "This student is high risk primarily because attendance (52%) is far below the cohort average and there are 4 active backlogs."
}
```

## 2. Strategy

| Model family               | Primary explainer       | Fallback                                           |
|----------------------------|-------------------------|----------------------------------------------------|
| Tree (RF, GBM, XGB)        | `shap.TreeExplainer`    | `(value − feature_mean) × feature_importance`      |
| Linear (LogReg)            | per-feature `coef × x`  | same                                               |
| Anything                   | `permutation_importance`| narrative built from importance ranking            |

If `shap` cannot be imported, the service detects the ImportError once at
startup, logs a warning, and silently switches to the fallback. The API
contract does not change.

## 3. Narrative Generation

The narrative is **template-rendered**, not LLM-generated, so it is always
deterministic and offline-safe:

```
"{name} is at {risk} risk because:
 • {factor_1.feature} = {factor_1.value} ({trend} the cohort avg of {avg})
 • {factor_2.feature} = ...
 ..."
```

When a recommendation is requested, this narrative is one of the inputs to the
LLM prompt — so even if the LLM fabricates context, the deterministic
narrative is always available alongside it for the counselor to verify.

## 4. UI Surface

The frontend `ExplainabilityPanel` renders:

* A **RiskMeter** with confidence dial.
* A **bar chart** of `top_factors` (signed contributions, colored by direction).
* A **plain-language narrative** block.
* A **"feature importance"** chart from the model meta (cohort-level, not
  per-student) for context.
