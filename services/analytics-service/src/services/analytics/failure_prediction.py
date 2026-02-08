"""Failure prediction pipeline implementations."""

from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd
import structlog
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import precision_recall_fscore_support, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from src.services.analytics.base import BasePipeline
from src.services.analytics.feature_engineering import FeatureEngineer

logger = structlog.get_logger()


class FailurePredictionPipeline(BasePipeline):
    """Pipeline for failure prediction analytics."""
    
    def __init__(self):
        self._logger = logger.bind(pipeline="FailurePrediction")
        self._feature_engineer = FeatureEngineer()
    
    def prepare_data(
        self,
        df: pd.DataFrame,
        parameters: Optional[Dict[str, Any]],
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Prepare data for failure prediction."""
        params = parameters or {}
        
        # Feature engineering
        features = params.get("features", ["voltage", "current", "power", "temperature"])
        df = self._feature_engineer.engineer_features(df, features)
        
        # For supervised learning, we need labels
        # In production, these would come from historical failure records
        # For now, we simulate failure labels based on anomaly conditions
        df = self._create_failure_labels(df, params)
        
        # Split into train/test
        test_size = params.get("test_size", 0.2)
        train_df, test_df = train_test_split(df, test_size=test_size, random_state=42)
        
        return train_df, test_df
    
    def _create_failure_labels(
        self,
        df: pd.DataFrame,
        params: Dict[str, Any],
    ) -> pd.DataFrame:
        """
        Create failure labels for supervised learning.
        
        In production, these would come from maintenance records.
        For simulation, we label based on extreme values.
        """
        df = df.copy()
        
        # Define failure conditions
        temp_threshold = params.get("failure_temp_threshold", 75.0)
        voltage_threshold = params.get("failure_voltage_threshold", 245.0)
        
        # Label as failure if conditions met
        df["failure"] = (
            (df["temperature"] > temp_threshold) |
            (df["voltage"] > voltage_threshold)
        ).astype(int)
        
        return df
    
    def train(
        self,
        train_df: pd.DataFrame,
        model_name: str,
        parameters: Optional[Dict[str, Any]],
    ) -> Any:
        """Train failure prediction model."""
        params = parameters or {}
        
        # Get feature columns (exclude target and non-numeric)
        exclude_cols = ["failure", "timestamp", "_time", "device_id"]
        feature_cols = [col for col in train_df.columns if col not in exclude_cols]
        feature_cols = [col for col in feature_cols if train_df[col].dtype in ["float64", "int64"]]
        
        X = train_df[feature_cols].values
        y = train_df["failure"].values
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Train model
        if model_name == "random_forest":
            model = RandomForestClassifier(
                n_estimators=params.get("n_estimators", 100),
                max_depth=params.get("max_depth", 10),
                random_state=params.get("random_state", 42),
            )
        elif model_name == "gradient_boosting":
            model = GradientBoostingClassifier(
                n_estimators=params.get("n_estimators", 100),
                learning_rate=params.get("learning_rate", 0.1),
                max_depth=params.get("max_depth", 6),
                random_state=params.get("random_state", 42),
            )
        else:
            raise ValueError(f"Unknown model: {model_name}")
        
        model.fit(X_scaled, y)
        
        return {
            "model": model,
            "scaler": scaler,
            "feature_cols": feature_cols,
        }
    
    def predict(
        self,
        test_df: pd.DataFrame,
        model: Dict[str, Any],
        parameters: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Run failure prediction on test data."""
        clf = model["model"]
        scaler = model["scaler"]
        feature_cols = model["feature_cols"]
        
        X = test_df[feature_cols].values
        X_scaled = scaler.transform(X)
        
        # Get predictions
        failure_prob = clf.predict_proba(X_scaled)[:, 1]
        predicted_failure = failure_prob > 0.5
        
        # Estimate time to failure based on probability
        time_to_failure = self._estimate_time_to_failure(failure_prob)
        
        return {
            "failure_probability": failure_prob.tolist(),
            "predicted_failure": predicted_failure.tolist(),
            "time_to_failure_hours": time_to_failure.tolist(),
            "high_risk_count": int(np.sum(failure_prob > 0.7)),
            "medium_risk_count": int(np.sum((failure_prob > 0.4) & (failure_prob <= 0.7))),
            "low_risk_count": int(np.sum(failure_prob <= 0.4)),
        }
    
    def _estimate_time_to_failure(self, failure_prob: np.ndarray) -> np.ndarray:
        """Estimate time to failure based on probability."""
        ttf = np.zeros(len(failure_prob))
        
        for i in range(len(failure_prob)):
            if failure_prob[i] > 0.8:
                ttf[i] = 1  # Critical - 1 hour
            elif failure_prob[i] > 0.6:
                ttf[i] = 6  # High risk - 6 hours
            elif failure_prob[i] > 0.4:
                ttf[i] = 24  # Moderate - 24 hours
            else:
                ttf[i] = -1  # Low risk - unknown
        
        return ttf
    
    def evaluate(
        self,
        test_df: pd.DataFrame,
        results: Dict[str, Any],
        parameters: Optional[Dict[str, Any]],
    ) -> Dict[str, float]:
        """Evaluate failure prediction performance."""
        y_true = test_df["failure"].values
        y_pred = np.array(results["predicted_failure"])
        y_prob = np.array(results["failure_probability"])
        
        # Calculate metrics
        precision, recall, f1, _ = precision_recall_fscore_support(
            y_true, y_pred, average="binary", zero_division=0
        )
        
        try:
            auc = roc_auc_score(y_true, y_prob)
        except ValueError:
            auc = 0.5  # Default if only one class present
        
        metrics = {
            "precision": float(precision),
            "recall": float(recall),
            "f1_score": float(f1),
            "auc_roc": float(auc),
            "accuracy": float(np.mean(y_true == y_pred)),
        }
        
        return metrics
