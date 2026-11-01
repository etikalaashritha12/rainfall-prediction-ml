"""Metrics and evaluation plots."""
import matplotlib
matplotlib.use("Agg")  # no GUI needed
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import (confusion_matrix, f1_score, mean_absolute_error, mean_squared_error,
                             precision_score, r2_score, recall_score, roc_auc_score)


def regression_metrics(y_true, y_pred):
    return {"mae": float(mean_absolute_error(y_true, y_pred)),
            "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
            "r2": float(r2_score(y_true, y_pred))}


def classification_metrics(y_true, y_pred, y_prob):
    out = {"precision": float(precision_score(y_true, y_pred, zero_division=0)),
           "recall": float(recall_score(y_true, y_pred, zero_division=0)),
           "f1": float(f1_score(y_true, y_pred, zero_division=0)),
           "confusion_matrix": confusion_matrix(y_true, y_pred, labels=[0, 1]).tolist(),
           "roc_auc": None}
    if len(set(y_true)) == 2:
        out["roc_auc"] = float(roc_auc_score(y_true, y_prob))
    return out


def save_plots(results, best_name, y_test, best_pred, importance, out_dir):
    names = list(results)
    fig, ax = plt.subplots(figsize=(8, 4))
    x = np.arange(len(names))
    ax.bar(x - 0.2, [results[n]["test"]["mae"] for n in names], 0.4, label="MAE")
    ax.bar(x + 0.2, [results[n]["test"]["rmse"] for n in names], 0.4, label="RMSE")
    ax.set_xticks(x, [n.split(" (")[0] for n in names], rotation=15)
    ax.set_title("Model comparison (test set, lower is better)"); ax.legend()
    fig.tight_layout(); fig.savefig(out_dir / "model_comparison.png", dpi=120); plt.close(fig)

    fig, ax = plt.subplots(figsize=(5, 5))
    ax.scatter(y_test, best_pred, s=8, alpha=0.5)
    lim = [0, max(float(np.max(y_test)), float(np.max(best_pred)))]
    ax.plot(lim, lim, "r--", label="perfect prediction"); ax.legend()
    ax.set_xlabel("Actual rainfall"); ax.set_ylabel("Predicted rainfall"); ax.set_title(f"{best_name}: actual vs predicted")
    fig.tight_layout(); fig.savefig(out_dir / "actual_vs_predicted.png", dpi=120); plt.close(fig)

    top = importance[:10][::-1]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.barh([t["feature"] for t in top], [t["importance"] for t in top])
    ax.set_title("Permutation importance (RMSE increase)")
    fig.tight_layout(); fig.savefig(out_dir / "feature_importance.png", dpi=120); plt.close(fig)
