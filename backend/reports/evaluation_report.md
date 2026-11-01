# Evaluation report (2026-11-01T20:59:24)

Split: {'type': 'chronological', 'train': 24544, 'validation': 5260, 'test': 5260}

## Regression models (test set)

| Model | MAE | RMSE | R2 |
|---|---|---|---|
| Linear Regression (Baseline) | 5.081 | 11.763 | 0.212 |
| Random Forest | 4.054 | 11.543 | 0.241 |
| Gradient Boosting | 3.836 | 11.195 | 0.286 |
| Voting Ensemble (RF + GB) | 3.926 | 11.278 | 0.275 |

Best model (by validation RMSE): **Gradient Boosting**

## Heavy-rainfall classifier

```
{
  "precision": 0.15384615384615385,
  "recall": 0.17857142857142858,
  "f1": 0.1652892561983471,
  "confusion_matrix": [
    [
      5149,
      55
    ],
    [
      46,
      10
    ]
  ],
  "roc_auc": 0.9269123339189635,
  "trained": true,
  "heavy_event_counts": {
    "train": 310,
    "val": 78,
    "test": 56
  },
  "threshold_mm": 64.5,
  "decision_probability": 0.5
}
```