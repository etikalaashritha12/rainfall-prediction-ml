"""Permutation importance: shuffle ONE input column on the test set and measure how much the
error grows. A big increase = the model relies on that feature. Works with any model."""
from sklearn.inspection import permutation_importance
import config


def compute_importance(model, X_test, y_test, max_rows=2000):
    if len(X_test) > max_rows:
        X_test = X_test.sample(max_rows, random_state=config.RANDOM_SEED)
        y_test = y_test.loc[X_test.index]
    result = permutation_importance(model, X_test, y_test, n_repeats=5, random_state=config.RANDOM_SEED,
                                    scoring="neg_root_mean_squared_error", n_jobs=-1)
    items = [{"feature": f, "importance": float(m), "std": float(s)}
             for f, m, s in zip(X_test.columns, result.importances_mean, result.importances_std)]
    return sorted(items, key=lambda d: d["importance"], reverse=True)
