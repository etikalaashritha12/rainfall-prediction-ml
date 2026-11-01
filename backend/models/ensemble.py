"""Candidate regression models. All share the SAME preprocessing -> fair comparison."""
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor, VotingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
import config
from preprocessing.feature_engineering import build_preprocessor

BASELINE = "Linear Regression (Baseline)"
RF = "Random Forest"
GB = "Gradient Boosting"
ENSEMBLE = "Voting Ensemble (RF + GB)"


def build_candidates(spec):
    seed = config.RANDOM_SEED
    def pipe(model):
        return Pipeline([("prep", build_preprocessor(spec)), ("model", model)])
    rf = RandomForestRegressor(n_estimators=200, min_samples_leaf=2, n_jobs=-1, random_state=seed)
    gb = GradientBoostingRegressor(n_estimators=200, learning_rate=0.05, max_depth=3, random_state=seed)
    # Voting = average of the predictions of several different models.
    ens = VotingRegressor([("rf", RandomForestRegressor(n_estimators=200, min_samples_leaf=2, n_jobs=-1, random_state=seed)),
                           ("gb", GradientBoostingRegressor(n_estimators=200, learning_rate=0.05, max_depth=3, random_state=seed))])
    return {BASELINE: pipe(LinearRegression()), RF: pipe(rf), GB: pipe(gb), ENSEMBLE: pipe(ens)}
